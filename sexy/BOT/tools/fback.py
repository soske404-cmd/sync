from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import json

# Load config
with open("FILES/config.json") as f:
    CONFIG = json.load(f)

OWNER = int(CONFIG["OWNER"])
CHANNEL = CONFIG["FEEDBACK"]  # use @channel_username only
FEEDBACK_GROUP = "@sosfeedbacks"  # Group to forward approved feedbacks


# ✅ /f or /fb command - Reply to photo/video
@Client.on_message(filters.command(["f", "fb"]) & filters.reply)
async def fback_reply_handler(client, msg: Message):
    rep = msg.reply_to_message

    # Support both photos and videos
    if not rep or (not rep.photo and not rep.video):
        return await msg.reply(
            "<b>Reply To An Image or Video To Process It</b>",
            reply_to_message_id=msg.id
        )

    if rep.from_user.id != msg.from_user.id:
        return await msg.reply(
            "<b>You Can Submit Feedbacks Of Own Media</b>",
            reply_to_message_id=msg.id
        )

    try:
        # Forward photo to owner
        fwd = await rep.forward(OWNER)

        # Send approval buttons to owner - Don't show /fb in message
        user = msg.from_user
        username = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        userid = f"<code>{user.id}</code>"

        btn_msg = await client.send_message(
            OWNER,
            f"<pre>New Feedback Received ✨</pre>\n<b>⟡ From - {username}</b>\n<b>⟡ UserID - {userid}</b>",
            reply_to_message_id=fwd.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approve ✅", callback_data=f"approve|{msg.from_user.id}|{fwd.id}|{msg.id}|{0}")],
                [InlineKeyboardButton("Reject ❌", callback_data=f"reject|{msg.from_user.id}|{msg.id}|{0}")]
            ])
        )

        # Confirm to user
        await msg.reply("<pre>Feedback Submitted ✅</pre>\n<b>⌁ Message</b> • <code>Awaiting review from the team</code>", reply_to_message_id=msg.id)

    except Exception as e:
        print(f"⚠️ Failed to send feedback. Error:\n`{e}`")


# ✅ /f or /fb in caption - Send photo/video with command in caption
@Client.on_message(filters.caption & filters.private)
async def fback_caption_handler(client, msg: Message):
    # Check if caption starts with /f or /fb
    if not msg.caption:
        return
    
    caption_lower = msg.caption.lower().strip()
    if not (caption_lower.startswith("/f") or caption_lower.startswith("/fb")):
        return
    
    # Support both photos and videos
    if not msg.photo and not msg.video:
        return await msg.reply(
            "<b>Send An Image or Video With /f or /fb In Caption</b>",
            reply_to_message_id=msg.id
        )

    try:
        # Forward photo/video to owner
        fwd = await msg.forward(OWNER)

        # Send approval buttons to owner - Don't show /fb in message
        user = msg.from_user
        username = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
        userid = f"<code>{user.id}</code>"

        btn_msg = await client.send_message(
            OWNER,
            f"<pre>New Feedback Received ✨</pre>\n<b>⟡ From - {username}</b>\n<b>⟡ UserID - {userid}</b>",
            reply_to_message_id=fwd.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approve ✅", callback_data=f"approve|{msg.from_user.id}|{fwd.id}|{msg.id}|{0}")],
                [InlineKeyboardButton("Reject ❌", callback_data=f"reject|{msg.from_user.id}|{msg.id}|{0}")]
            ])
        )

        # Confirm to user
        await msg.reply("<pre>Feedback Submitted ✅</pre>\n<b>⌁ Message</b> • <code>Awaiting review from the team</code>", reply_to_message_id=msg.id)

    except Exception as e:
        print(f"⚠️ Failed to send feedback. Error:\n`{e}`")


# ✅ Approve button handler
@Client.on_callback_query(filters.regex(r"^approve\|"))
async def approve_btn(client, cb):
    try:
        _, uid, fwdid, msgid, _ = cb.data.split("|")
        uid = int(uid)
        fwdid = int(fwdid)
        msgid = int(msgid)
        user = await client.get_users(uid)

        username = f"<a href='tg://user?id={uid}'>{user.first_name}</a>"
        userid = f"<code>{uid}</code>"

        # Forward to feedback group (t.me/sosfeedbacks)
        try:
            await client.forward_messages(
                chat_id=FEEDBACK_GROUP,
                from_chat_id=cb.message.chat.id,
                message_ids=fwdid
            )
        except Exception as e:
            print(f"Failed to forward to feedback group: {e}")
        
        # Also forward to channel if configured
        try:
            await client.forward_messages(
                chat_id=CHANNEL,
                from_chat_id=cb.message.chat.id,
                message_ids=fwdid
            )
        except Exception as e:
            print(f"Failed to forward to channel: {e}")

        # Notify user
        await client.send_message(
            uid,
            "<pre>Feedback Approved ✅</pre>\n<b>⌁ Message</b> • <code>Feedback You Recently Submitted Has Been Approved</code>",
            reply_to_message_id=msgid
        )

        # Edit button message
        await cb.message.edit_text(
            f"<pre>Feedback Approved ✅</pre>\n<b>⟡ From - {username}</b>\n<b>⟡ UserID - {userid}</b>"
        )

        await cb.answer("Approved ✅")

    except Exception as e:
        await cb.answer(f"❌ Error: {e}", show_alert=True)


@Client.on_callback_query(filters.regex(r"^reject\|"))
async def reject_btn(client, cb):
    try:
        _, uid, msgid, _ = cb.data.split("|")
        uid = int(uid)
        msgid = int(msgid)
        user = await client.get_users(uid)

        username = f"<a href='tg://user?id={uid}'>{user.first_name}</a>"
        userid = f"<code>{uid}</code>"

        await client.send_message(
            uid,
            "<pre>Feedback Rejected ❌</pre>\n<b>⌁ Message</b> • <code>Feedback You Recently Submitted Has Been Rejected</code>\n<b>Try to give more details next time.</b>",
            reply_to_message_id=msgid
        )

        await cb.message.edit_text(
            f"<pre>Feedback Rejected ❌</pre>\n<b>⟡ From - {username}</b>\n<b>⟡ UserID - {userid}</b>"
        )

        await cb.answer("Rejected ❌")

    except Exception as e:
        await cb.answer(f"❌ Error: {e}", show_alert=True)
