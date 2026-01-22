import json
from TOOLS.getbin import get_bin_details
from BOT.helper.start import load_users

def format_shopify_response(cc, mes, ano, cvv, raw_response, timet, profile):
    fullcc = f"{cc}|{mes}|{ano}|{cvv}"

    # Extract user_id
    try:
        user_id = profile.split("id=")[-1].split("'")[0]
    except Exception:
        user_id = None

    # Load gateway from DATA/sites.json
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        gateway = sites.get(user_id, {}).get("gate", "Shopify Self Site 💷")
    except Exception:
        gateway = "Shopify Self Site 💷"

    # Clean response
    raw_response = str(raw_response) if raw_response else "-"

    # Determine status
    if "ORDER_PLACED" in raw_response or "Thank You" in raw_response:
        status_flag = "Charged 💎"
    elif any(keyword in raw_response for keyword in [
        "3D CC", "MISMATCHED_BILLING", "MISMATCHED_PIN", "MISMATCHED_ZIP", "INSUFFICIENT_FUNDS", "INVALID_CVC", "INCORRECT_CVC", "3DS_REQUIRED", "MISMATCHED_BILL", "3D_AUTHENTICATION", "INCORRECT_ZIP", "INCORRECT_ADDRESS"
    ]):
        status_flag = "Approved ❎"
    else:
        status_flag = "Declined ❌"

    # BIN lookup
    bin_data = get_bin_details(cc[:6]) or {}
    bin_info = {
        "bin": bin_data.get("bin", cc[:6]),
        "country": bin_data.get("country", "Unknown"),
        "flag": bin_data.get("flag", "🏳️"),
        "vendor": bin_data.get("vendor", "Unknown"),
        "type": bin_data.get("type", "Unknown"),
        "level": bin_data.get("level", "Unknown"),
        "bank": bin_data.get("bank", "Unknown")
    }

    # User Plan
    try:
        users = load_users()
        user_data = users.get(user_id, {})
        plan = user_data.get("plan", {}).get("plan", "Free")
        badge = user_data.get("plan", {}).get("badge", "🎟️")
    except Exception:
        plan = "Unknown"
        badge = "❔"

    # Final formatted message
    result = f"""
<b>[#AutoShopify] | Sos</b> ✦
━━━━━━━━━━━━━━━
<b>[•] Card</b>- <code>{fullcc}</code>
<b>[•] Gateway</b> - <b>{gateway}</b>
<b>[•] Status</b>- <code>{status_flag}</code>
<b>[•] Response</b>- <code>{raw_response}</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
<b>[+] Bin</b>: <code>{bin_info['bin']}</code>  
<b>[+] Info</b>: <code>{bin_info['vendor']} - {bin_info['type']} - {bin_info['level']}</code> 
<b>[+] Bank</b>: <code>{bin_info['bank']}</code> 🏦
<b>[+] Country</b>: <code>{bin_info['country']} - [{bin_info['flag']}]</code>
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━
<b>[ﾒ] Checked By</b>: {profile} [<code>{plan} {badge}</code>]
<b>[ϟ] Dev</b> ➺ <a href="https://t.me/gitsus">𝙎𝙤𝙨𝙠𝙚</a>
━━━━━━━━━━━━━━━
<b>[ﾒ] T/t</b>: <code>[{timet} 𝐬]</code> <b>|P/x:</b> [<code>Live ⚡️</code>]
"""
    return status_flag, result
