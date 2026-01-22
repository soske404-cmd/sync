import re
import json
import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatType
from BOT.tools.proxy import get_proxy
import os

# Import gate checkers
from BOT.paypal import check_paypal
from BOT.authnet import check_authnet
from BOT.payflow import check_payflow
from BOT.stripe_auth import check_stripe_auth
from BOT.b3 import check_b3
from BOT.stripe_charge import check_stripe_charge

# Store active checking sessions
active_sessions = {}
# Store results for each session
session_results = {}

def load_users():
    try:
        with open("DATA/users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def load_allowed_groups():
    try:
        with open("DATA/groups.json", "r") as f:
            return json.load(f)
    except:
        return []

def has_credits(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False
        credits = user.get("plan", {}).get("credits", 0)
        if credits == "∞":
            return True
        return int(credits) > 0
    except:
        return False

def deduct_credit_bulk(user_id, amount):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False
        credits = user["plan"].get("credits", 0)
        if credits == "∞":
            return True
        credits = int(credits)
        if credits >= amount:
            user["plan"]["credits"] = str(credits - amount)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True
        return False
    except:
        return False

def extract_cards(text):
    return re.findall(r'(\d{12,19}\|\d{1,2}\|\d{2,4}\|\d{3,4})', text)

def is_txt_allowed(user_id):
    """Check if user can use TXT checker (Ultimate or VIP only)"""
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return False, 0
        plan = user.get("plan", {}).get("plan", "Free").upper()
        # Owner has unlimited access
        if plan == "OWNER":
            return True, 1000
        # ULTIMATE plan - 500 cards
        elif plan == "ULTIMATE":
            return True, 500
        # VIP plan - 300 cards
        elif plan == "VIP":
            return True, 300
        else:
            return False, 0
    except:
        return False, 0

def get_owner_link():
    return "https://t.me/gitsus"

async def check_card_with_gate(gate, cc, mm, yy, cvv, proxy):
    """Check a card with the specified gate"""
    loop = asyncio.get_event_loop()
    
    if gate == "pp":
        return await loop.run_in_executor(None, check_paypal, cc, mm, yy, cvv, proxy)
    elif gate == "an":
        return await loop.run_in_executor(None, check_authnet, cc, mm, yy, cvv, proxy)
    elif gate == "sc":
        return await loop.run_in_executor(None, check_stripe_charge, cc, mm, yy, cvv, proxy)
    elif gate == "pl":
        return await loop.run_in_executor(None, check_payflow, cc, mm, yy, cvv, proxy)
    elif gate == "au":
        return await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
    elif gate == "b3":
        return await loop.run_in_executor(None, check_b3, cc, mm, yy, cvv, proxy)
    elif gate == "str":
        # For autostripe, we need to import differently
        try:
            from BOT.str import check_autostripe, get_autostripe_info
            user_site_info = get_autostripe_info(proxy)  # Using proxy as user_id placeholder
            if user_site_info:
                site = user_site_info['site']
                fullcc = f"{cc}|{mm}|{yy}|{cvv}"
                result = await check_autostripe(site, fullcc)
                # Parse result
                if "CHARGED" in result.upper() or "SUCCESS" in result.upper():
                    return "Charged 💎", result[:40]
                elif any(x in result.upper() for x in ["CVV", "CVC", "INSUFFICIENT", "3DS", "AUTHENTICATION"]):
                    return "Approved ✅", result[:40]
                else:
                    return "Declined ❌", result[:40]
            return "Declined ❌", "No Site"
        except:
            return "Declined ❌", "Error"
    else:
        return "Declined ❌", "Unknown Gate"


@Client.on_message(filters.command("txt") & ~filters.edited)
async def txt_checker_start(client, message):
    """TXT File Checker - Ultimate and VIP only"""
    user_id = str(message.from_user.id)
    
    # Check if user can use TXT checker
    allowed, limit = is_txt_allowed(user_id)
    if not allowed:
        return await message.reply(
            "<pre>Notification ❗️</pre>\n"
            "<b>~ Message :</b> <code>TXT Checker is only for Ultimate & VIP plans!</code>\n"
            "<b>~ Ultimate:</b> <code>500 cards limit</code>\n"
            "<b>~ VIP:</b> <code>300 cards limit</code>\n"
            "━━━━━━━━━━━━━\n"
            '<b>~ Buy Premium →</b> <b><a href="https://t.me/gitsus">Click Here</a></b>',
            reply_to_message_id=message.id
        )
    
    # Check if already has active session
    if user_id in active_sessions and active_sessions[user_id].get("active"):
        return await message.reply(
            "<pre>⚠️ Wait!</pre>\n<b>You have an active TXT checker session. Stop it first.</b>",
            reply_to_message_id=message.id
        )
    
    users = load_users()
    if user_id not in users:
        return await message.reply(
            "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
            reply_to_message_id=message.id
        )
    
    user_data = users[user_id]
    plan = user_data.get("plan", {}).get("plan", "Free")
    
    # Ask for gate selection
    gate_buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("PayPal $0.01", callback_data=f"txtgate_pp_{user_id}"),
            InlineKeyboardButton("Authnet $1", callback_data=f"txtgate_an_{user_id}")
        ],
        [
            InlineKeyboardButton("Stripe $1", callback_data=f"txtgate_sc_{user_id}"),
            InlineKeyboardButton("B3 Auth", callback_data=f"txtgate_b3_{user_id}")
        ],
        [
            InlineKeyboardButton("Stripe Auth", callback_data=f"txtgate_au_{user_id}"),
            InlineKeyboardButton("Payflow Auth", callback_data=f"txtgate_pl_{user_id}")
        ],
        [
            InlineKeyboardButton("AutoStripe", callback_data=f"txtgate_str_{user_id}")
        ],
        [
            InlineKeyboardButton("Cancel", callback_data=f"txtcancel_{user_id}")
        ]
    ])
    
    await message.reply(
        f"<pre>✦ TXT File Checker</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Plan:</b> <code>{plan}</code>\n"
        f"<b>[•] Card Limit:</b> <code>{limit}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Select a gate to check cards:</b>",
        reply_to_message_id=message.id,
        reply_markup=gate_buttons
    )


@Client.on_callback_query(filters.regex(r"^txtgate_"))
async def txt_gate_selected(client, callback: CallbackQuery):
    """Handle gate selection for TXT checker"""
    data = callback.data
    parts = data.split("_")
    gate = parts[1]
    owner_id = parts[2]
    user_id = str(callback.from_user.id)
    
    if user_id != owner_id:
        return await callback.answer("❌ This is not your session!", show_alert=True)
    
    # Store selected gate
    if user_id not in active_sessions:
        active_sessions[user_id] = {}
    
    active_sessions[user_id]["gate"] = gate
    active_sessions[user_id]["waiting_file"] = True
    
    gate_names = {
        "pp": "PayPal $0.01",
        "an": "Authnet $1",
        "sc": "Stripe $1 Charge",
        "b3": "B3 Auth",
        "au": "Stripe Auth",
        "pl": "Payflow Auth",
        "str": "AutoStripe"
    }
    
    await callback.message.edit_text(
        f"<pre>✦ TXT File Checker</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Gate:</b> <code>{gate_names.get(gate, gate)}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>Now send your TXT file with cards.</b>\n"
        f"<code>Format: cc|mm|yy|cvv</code>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Cancel", callback_data=f"txtcancel_{user_id}")]
        ])
    )
    
    await callback.answer("Gate selected! Now send your TXT file.")


@Client.on_callback_query(filters.regex(r"^txtcancel_"))
async def txt_cancel(client, callback: CallbackQuery):
    """Cancel TXT checker session"""
    user_id = str(callback.from_user.id)
    owner_id = callback.data.split("_")[1]
    
    if user_id != owner_id:
        return await callback.answer("❌ This is not your session!", show_alert=True)
    
    # Stop active session
    if user_id in active_sessions:
        active_sessions[user_id]["active"] = False
        active_sessions[user_id]["waiting_file"] = False
    
    await callback.message.edit_text("<pre>TXT Checker Cancelled ❌</pre>")
    await callback.answer("Cancelled!")


@Client.on_callback_query(filters.regex(r"^txtstop_"))
async def txt_stop(client, callback: CallbackQuery):
    """Stop active TXT checker"""
    user_id = str(callback.from_user.id)
    owner_id = callback.data.split("_")[1]
    
    if user_id != owner_id:
        return await callback.answer("❌ This is not your session!", show_alert=True)
    
    if user_id in active_sessions:
        active_sessions[user_id]["active"] = False
    
    await callback.answer("Stopping... Please wait.")


@Client.on_callback_query(filters.regex(r"^txtview_"))
async def txt_view_results(client, callback: CallbackQuery):
    """View specific result category"""
    data = callback.data
    parts = data.split("_")
    category = parts[1]  # charged, approved, declined, errors
    owner_id = parts[2]
    user_id = str(callback.from_user.id)
    
    if user_id != owner_id:
        return await callback.answer("❌ This is not your session!", show_alert=True)
    
    if user_id not in session_results:
        return await callback.answer("No results found!", show_alert=True)
    
    results = session_results[user_id]
    cards = results.get(category, [])
    
    if not cards:
        return await callback.answer(f"No {category} cards found!", show_alert=True)
    
    category_titles = {
        "charged": "💎 Charged Cards",
        "approved": "✅ Approved Cards",
        "declined": "❌ Declined Cards",
        "errors": "⚠️ Error Cards"
    }
    
    # Build card list
    card_text = f"<pre>{category_titles.get(category, category)}</pre>\n"
    card_text += "━━━━━━━━━━━━━━━\n"
    
    for card_info in cards[:50]:  # Limit to 50 cards per view
        card_text += f"<code>{card_info['card']}</code>\n"
        card_text += f"└ {card_info['response']}\n"
    
    if len(cards) > 50:
        card_text += f"\n<i>... and {len(cards) - 50} more cards</i>"
    
    card_text += f"\n━━━━━━━━━━━━━━━\n"
    card_text += f"<b>Total:</b> <code>{len(cards)}</code>"
    
    # Back button
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Back to Results", callback_data=f"txtback_{user_id}")]
    ])
    
    if len(card_text) > 4000:
        # Send as file
        os.makedirs("downloads", exist_ok=True)
        filename = f"downloads/txt_{category}_{user_id}.txt"
        
        with open(filename, "w") as f:
            f.write(f"{category_titles.get(category, category)}\n")
            f.write("=" * 50 + "\n\n")
            for card_info in cards:
                f.write(f"{card_info['card']} >> {card_info['response']}\n")
        
        await callback.message.reply_document(
            filename,
            caption=f"<pre>{category_titles.get(category, category)}</pre>\n<b>Total:</b> <code>{len(cards)}</code>",
            reply_markup=buttons
        )
        os.remove(filename)
        await callback.answer()
    else:
        await callback.message.edit_text(card_text, reply_markup=buttons)
        await callback.answer()


@Client.on_callback_query(filters.regex(r"^txtback_"))
async def txt_back_to_results(client, callback: CallbackQuery):
    """Go back to main results view"""
    user_id = str(callback.from_user.id)
    owner_id = callback.data.split("_")[1]
    
    if user_id != owner_id:
        return await callback.answer("❌ This is not your session!", show_alert=True)
    
    if user_id not in session_results:
        return await callback.answer("No results found!", show_alert=True)
    
    results = session_results[user_id]
    
    charged_count = len(results.get("charged", []))
    approved_count = len(results.get("approved", []))
    declined_count = len(results.get("declined", []))
    errors_count = len(results.get("errors", []))
    total = results.get("total", 0)
    
    result_text = f"<pre>✦ TXT Checker Results</pre>\n"
    result_text += "━━━━━━━━━━━━━━━\n"
    result_text += f"<b>[💎] Charged:</b> <code>{charged_count}</code>\n"
    result_text += f"<b>[✅] Approved:</b> <code>{approved_count}</code>\n"
    result_text += f"<b>[❌] Declined:</b> <code>{declined_count}</code>\n"
    result_text += f"<b>[⚠️] Errors:</b> <code>{errors_count}</code>\n"
    result_text += "━━━━━━━━━━━━━━━\n"
    result_text += f"<b>[•] Total:</b> <code>{total}</code>\n"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"💎 Charged ({charged_count})", callback_data=f"txtview_charged_{user_id}"),
            InlineKeyboardButton(f"✅ Approved ({approved_count})", callback_data=f"txtview_approved_{user_id}")
        ],
        [
            InlineKeyboardButton(f"❌ Declined ({declined_count})", callback_data=f"txtview_declined_{user_id}"),
            InlineKeyboardButton(f"⚠️ Errors ({errors_count})", callback_data=f"txtview_errors_{user_id}")
        ],
        [
            InlineKeyboardButton("Owner", url=get_owner_link())
        ]
    ])
    
    await callback.message.edit_text(result_text, reply_markup=buttons)
    await callback.answer()


@Client.on_message(filters.document & filters.private)
async def handle_txt_file(client, message):
    """Handle TXT file upload for checker"""
    user_id = str(message.from_user.id)
    
    # Check if user is waiting for file
    if user_id not in active_sessions or not active_sessions[user_id].get("waiting_file"):
        return  # Not waiting for TXT file
    
    # Check file type
    if not message.document.file_name.endswith('.txt'):
        return await message.reply(
            "<pre>Invalid File ❌</pre>\n<b>Please send a .txt file</b>",
            reply_to_message_id=message.id
        )
    
    # Check plan limits
    allowed, limit = is_txt_allowed(user_id)
    if not allowed:
        return
    
    # Download file
    os.makedirs("downloads", exist_ok=True)
    file_path = f"downloads/txt_upload_{user_id}.txt"
    await message.download(file_path)
    
    # Read cards from file
    try:
        with open(file_path, "r") as f:
            content = f.read()
        os.remove(file_path)
    except:
        return await message.reply("<pre>Error reading file ❌</pre>", reply_to_message_id=message.id)
    
    all_cards = extract_cards(content)
    
    if not all_cards:
        return await message.reply(
            "<pre>No cards found ❌</pre>\n<b>File must contain cards in format:</b> <code>cc|mm|yy|cvv</code>",
            reply_to_message_id=message.id
        )
    
    # Limit cards
    if len(all_cards) > limit:
        all_cards = all_cards[:limit]
    
    card_count = len(all_cards)
    
    # Check credits
    users = load_users()
    user_data = users.get(user_id, {})
    available_credits = user_data.get("plan", {}).get("credits", 0)
    
    if available_credits != "∞":
        try:
            if card_count > int(available_credits):
                return await message.reply(
                    "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>",
                    reply_to_message_id=message.id
                )
        except:
            pass
    
    # Get gate and proxy
    gate = active_sessions[user_id].get("gate", "pp")
    proxy = get_proxy(message.from_user.id)
    
    gate_names = {
        "pp": "PayPal $0.01",
        "an": "Authnet $1",
        "sc": "Stripe $1 Charge",
        "b3": "B3 Auth",
        "au": "Stripe Auth",
        "pl": "Payflow Auth",
        "str": "AutoStripe"
    }
    
    # Mark session as active
    active_sessions[user_id]["active"] = True
    active_sessions[user_id]["waiting_file"] = False
    
    # Initialize results
    session_results[user_id] = {
        "charged": [],
        "approved": [],
        "declined": [],
        "errors": [],
        "total": card_count
    }
    
    plan = user_data.get("plan", {}).get("plan", "Free")
    badge = user_data.get("plan", {}).get("badge", "🎟️")
    profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
    
    # Send initial status
    loader_msg = await message.reply(
        f"<pre>✦ TXT Checker | Processing</pre>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[•] Gate:</b> <code>{gate_names.get(gate, gate)}</code>\n"
        f"<b>[•] Cards:</b> <code>{card_count}</code>\n"
        f"<b>[•] Progress:</b> <code>0/{card_count}</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[💎] Charged:</b> <code>0</code>\n"
        f"<b>[✅] Approved:</b> <code>0</code>\n"
        f"<b>[❌] Declined:</b> <code>0</code>\n"
        f"<b>[⚠️] Errors:</b> <code>0</code>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<b>[ﾒ] By:</b> {profile} [<code>{plan} {badge}</code>]",
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏹ Stop Checking", callback_data=f"txtstop_{user_id}")]
        ])
    )
    
    start_time = time()
    checked = 0
    
    for card in all_cards:
        # Check if stopped
        if not active_sessions.get(user_id, {}).get("active", False):
            break
        
        parts = card.split("|")
        if len(parts) != 4:
            session_results[user_id]["errors"].append({
                "card": card,
                "response": "Invalid Format"
            })
            checked += 1
            continue
        
        cc, mm, yy, cvv = parts
        
        try:
            status, response = await check_card_with_gate(gate, cc, mm, yy, cvv, proxy)
            
            if "Charged" in status:
                session_results[user_id]["charged"].append({
                    "card": card,
                    "response": response
                })
            elif "Approved" in status:
                session_results[user_id]["approved"].append({
                    "card": card,
                    "response": response
                })
            elif "Declined" in status:
                session_results[user_id]["declined"].append({
                    "card": card,
                    "response": response
                })
            else:
                session_results[user_id]["errors"].append({
                    "card": card,
                    "response": response
                })
        except Exception as e:
            session_results[user_id]["errors"].append({
                "card": card,
                "response": str(e)[:30]
            })
        
        checked += 1
        
        # Update progress every 5 cards
        if checked % 5 == 0 or checked == card_count:
            charged_count = len(session_results[user_id]["charged"])
            approved_count = len(session_results[user_id]["approved"])
            declined_count = len(session_results[user_id]["declined"])
            errors_count = len(session_results[user_id]["errors"])
            
            try:
                await loader_msg.edit_text(
                    f"<pre>✦ TXT Checker | Processing</pre>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"<b>[•] Gate:</b> <code>{gate_names.get(gate, gate)}</code>\n"
                    f"<b>[•] Cards:</b> <code>{card_count}</code>\n"
                    f"<b>[•] Progress:</b> <code>{checked}/{card_count}</code>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"<b>[💎] Charged:</b> <code>{charged_count}</code>\n"
                    f"<b>[✅] Approved:</b> <code>{approved_count}</code>\n"
                    f"<b>[❌] Declined:</b> <code>{declined_count}</code>\n"
                    f"<b>[⚠️] Errors:</b> <code>{errors_count}</code>\n"
                    f"━━━━━━━━━━━━━━━\n"
                    f"<b>[ﾒ] By:</b> {profile} [<code>{plan} {badge}</code>]",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(f"💎 Charged ({charged_count})", callback_data=f"txtview_charged_{user_id}"),
                            InlineKeyboardButton(f"✅ Approved ({approved_count})", callback_data=f"txtview_approved_{user_id}")
                        ],
                        [
                            InlineKeyboardButton(f"❌ Declined ({declined_count})", callback_data=f"txtview_declined_{user_id}"),
                            InlineKeyboardButton(f"⚠️ Errors ({errors_count})", callback_data=f"txtview_errors_{user_id}")
                        ],
                        [
                            InlineKeyboardButton("⏹ Stop Checking", callback_data=f"txtstop_{user_id}")
                        ]
                    ])
                )
            except:
                pass
    
    # Finished
    end_time = time()
    timetaken = round(end_time - start_time, 2)
    
    active_sessions[user_id]["active"] = False
    
    # Deduct credits
    if available_credits != "∞":
        deduct_credit_bulk(user_id, checked)
    
    charged_count = len(session_results[user_id]["charged"])
    approved_count = len(session_results[user_id]["approved"])
    declined_count = len(session_results[user_id]["declined"])
    errors_count = len(session_results[user_id]["errors"])
    
    # Final message
    final_text = f"<pre>✦ TXT Checker | Completed ✅</pre>\n"
    final_text += "━━━━━━━━━━━━━━━\n"
    final_text += f"<b>[•] Gate:</b> <code>{gate_names.get(gate, gate)}</code>\n"
    final_text += f"<b>[•] Checked:</b> <code>{checked}/{card_count}</code>\n"
    final_text += f"<b>[•] Time:</b> <code>{timetaken}s</code>\n"
    final_text += "━━━━━━━━━━━━━━━\n"
    final_text += f"<b>[💎] Charged:</b> <code>{charged_count}</code>\n"
    final_text += f"<b>[✅] Approved:</b> <code>{approved_count}</code>\n"
    final_text += f"<b>[❌] Declined:</b> <code>{declined_count}</code>\n"
    final_text += f"<b>[⚠️] Errors:</b> <code>{errors_count}</code>\n"
    final_text += "━━━━━━━━━━━━━━━\n"
    final_text += f"<b>[ﾒ] By:</b> {profile} [<code>{plan} {badge}</code>]"
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"💎 Charged ({charged_count})", callback_data=f"txtview_charged_{user_id}"),
            InlineKeyboardButton(f"✅ Approved ({approved_count})", callback_data=f"txtview_approved_{user_id}")
        ],
        [
            InlineKeyboardButton(f"❌ Declined ({declined_count})", callback_data=f"txtview_declined_{user_id}"),
            InlineKeyboardButton(f"⚠️ Errors ({errors_count})", callback_data=f"txtview_errors_{user_id}")
        ],
        [
            InlineKeyboardButton("Owner", url=get_owner_link())
        ]
    ])
    
    try:
        await loader_msg.edit_text(final_text, reply_markup=buttons)
    except:
        await message.reply(final_text, reply_markup=buttons)
