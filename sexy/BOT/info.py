import json
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode

USERS_FILE = "DATA/users.json"
CONFIG_FILE = "FILES/config.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def load_owner_id():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        return config.get("OWNER")
    except:
        return None

@Client.on_message(filters.command("info") & ~filters.edited)
async def info_command(client, message: Message):
    """Show user info"""
    users = load_users()
    
    # Check if replying to someone or checking self
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        user_id = str(target_user.id)
        name = target_user.first_name
    else:
        target_user = message.from_user
        user_id = str(message.from_user.id)
        name = message.from_user.first_name
    
    profile = f"<a href='tg://user?id={user_id}'>{name}</a>"
    
    if user_id not in users:
        return await message.reply(
            f"<pre>User Info ❌</pre>\n<b>User</b> {profile} <b>is not registered.</b>",
            parse_mode=ParseMode.HTML
        )
    
    user_data = users[user_id]
    plan_data = user_data.get("plan", {})
    
    plan_name = plan_data.get("plan", "Free")
    badge = plan_data.get("badge", "🎟️")
    credits = plan_data.get("credits", 0)
    antispam = plan_data.get("antispam", 15)
    mlimit = plan_data.get("mlimit", 5)
    private = plan_data.get("private", "off")
    registered_at = user_data.get("registered_at", "Unknown")
    
    # Get site info
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        user_site = sites.get(user_id, {}).get("site", "Not Set")
    except:
        user_site = "Not Set"
    
    info_text = f"""<pre>User Info ~ Sos ✦</pre>
━━━━━━━━━━━━━━━
<b>[•] Name:</b> {profile}
<b>[•] ID:</b> <code>{user_id}</code>
<b>[•] Plan:</b> <code>{plan_name} {badge}</code>
<b>[•] Credits:</b> <code>{credits}</code>
<b>[•] Antispam:</b> <code>{antispam}s</code>
<b>[•] Mass Limit:</b> <code>{mlimit}</code>
<b>[•] Private:</b> <code>{private}</code>
<b>[•] Registered:</b> <code>{registered_at}</code>
━━━━━━━━━━━━━━━"""
    
    await message.reply(info_text, parse_mode=ParseMode.HTML)


@Client.on_message(filters.command("me") & ~filters.edited)
async def me_command(client, message: Message):
    """Show own info"""
    users = load_users()
    user_id = str(message.from_user.id)
    name = message.from_user.first_name
    profile = f"<a href='tg://user?id={user_id}'>{name}</a>"
    
    if user_id not in users:
        return await message.reply(
            f"<pre>Not Registered ❌</pre>\n<b>Use /register first.</b>",
            parse_mode=ParseMode.HTML
        )
    
    user_data = users[user_id]
    plan_data = user_data.get("plan", {})
    
    plan_name = plan_data.get("plan", "Free")
    badge = plan_data.get("badge", "🎟️")
    credits = plan_data.get("credits", 0)
    antispam = plan_data.get("antispam", 15)
    mlimit = plan_data.get("mlimit", 5)
    private = plan_data.get("private", "off")
    
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        user_site = sites.get(user_id, {}).get("site", "Not Set")
    except:
        user_site = "Not Set"
    
    info_text = f"""<pre>My Info ~ Sos ✦</pre>
━━━━━━━━━━━━━━━
<b>[•] Name:</b> {profile}
<b>[•] Plan:</b> <code>{plan_name} {badge}</code>
<b>[•] Credits:</b> <code>{credits}</code>
<b>[•] Antispam:</b> <code>{antispam}s</code>
<b>[•] Mass Limit:</b> <code>{mlimit}</code>
<b>[•] Private:</b> <code>{private}</code>
━━━━━━━━━━━━━━━"""
    
    await message.reply(info_text, parse_mode=ParseMode.HTML)


@Client.on_message(filters.command("buy") & ~filters.edited)
async def buy_command(client, message: Message):
    """Show available plans for purchase"""
    owner_id = load_owner_id()
    owner_link = f"<a href='tg://user?id={owner_id}'>Owner</a>" if owner_id else "Owner"
    
    buy_text = f"""<pre>Available Plans ~ Sos ✦</pre>
━━━━━━━━━━━━━━━
<code>1 Credit = 1 Card Check</code>

<b>plan1 - Plus 💠</b>
   • Price: <code>$1</code>
   • Credits: <code>200</code>
   • Antispam: <code>13s</code>
   • Duration: <code>1 Day</code>

<b>plan2 - Pro 🔰</b>
   • Price: <code>$3</code>
   • Credits: <code>500</code>
   • Antispam: <code>7s</code>
   • Mass Limit: <code>7</code>
   • Duration: <code>7 Days</code>

<b>plan3 - Elite 📧</b>
   • Price: <code>$6</code>
   • Credits: <code>1000</code>
   • Antispam: <code>3s</code>
   • Mass Limit: <code>10</code>
   • Duration: <code>15 Days</code>

<b>plan4 - VIP 🎖</b>
   • Price: <code>$15</code>
   • Credits: <code>2000</code>
   • Antispam: <code>1s</code>
   • Mass Limit: <code>15</code>
   • Duration: <code>30 Days</code>

<b>plan5 - Ultimate ⭐️</b>
   • Price: <code>$25</code>
   • Credits: <code>2500</code>
   • Antispam: <code>1s</code>
   • Mass Limit: <code>22</code>
   • Duration: <code>30 Days</code>

━━━━━━━━━━━━━━━
<b>Buy plans from Owner</b>
"""
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Contact Owner", url="https://t.me/gitsus")],
        [InlineKeyboardButton("Close", callback_data="exit")]
    ])
    
    await message.reply(buy_text, reply_markup=buttons, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
