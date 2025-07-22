import os
import asyncio
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from config import API_ID, API_HASH, BOT_TOKEN, FORCE_CHANNEL, ADMIN_ID
from tools import get_data
from database import (
    get_user_data, save_user_data,
    get_referral_data, save_referral_data,
    reset_daily_downloads
)

app = Client("Video_hub_terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

users_file = "users.txt"
user_states = {}  # For tracking admin input states manually

def save_user(user_id):
    with open(users_file, "a+") as f:
        f.seek(0)
        if str(user_id) not in f.read().splitlines():
            f.write(f"{user_id}\n")

def force_join_required(user_id):
    try:
        member = app.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status not in ("member", "administrator", "creator")
    except:
        return True

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user = message.from_user
    user_id = str(user.id)
    save_user(user_id)

    user_data = get_user_data()
    referral_data = get_referral_data()

    if user_id not in user_data:
        user_data[user_id] = {"downloads": 0, "last_reset": datetime.utcnow().strftime("%Y-%m-%d")}
    if user_id not in referral_data:
        referral_data[user_id] = {"referrals": 0, "referred_by": None}

    if len(message.command) > 1:
        referrer_id = message.command[1]
        if referrer_id != user_id and referral_data[user_id]["referred_by"] is None:
            referral_data[user_id]["referred_by"] = referrer_id
            referral_data[referrer_id]["referrals"] += 1
            try:
                await app.send_message(int(referrer_id),
                    f"🎉 You got a new referral!\n👤 [{user.first_name}](tg://user?id={user.id}) joined through your link\n💰 +1 download credit"
                )
            except:
                pass

    save_user_data(user_data)
    save_referral_data(referral_data)

    if force_join_required(user.id):
        return await message.reply(
            "🔐 Please join our updates channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Developer Channel", url="https://t.me/+28D1ypobsIxjZjQ1")],
                [InlineKeyboardButton("📢 Join Video Link Channel", url="https://t.me/+bnQ1FHi3EOk0YjM1")],
                [InlineKeyboardButton("Follow Me Baby 🌚", url="https://www.instagram.com/love_reel_page/profilecard/?igsh=MWpvbWFjd29namlxMQ==")],
                [InlineKeyboardButton("✅ I Joined", callback_data="refresh")]
            ])
        )

    referral_link = f"https://t.me/Video_hub_terabox_bot?start={user.id}"
    await message.reply(
        f"👋 Hello {user.mention}\n\n"
        f"📥 Send any Terabox link to download.\n\n"
        f"🎁 Daily Limit: 4\n"
        f"➕ 1 referral = +1 extra\n"
        f"🔗 Your Referral Link:\n`{referral_link}`"
    )

@app.on_callback_query()
async def join_refresh(client, cb: CallbackQuery):
    if cb.data == "refresh":
        if not force_join_required(cb.from_user.id):
            await cb.message.delete()
            await cb.message.reply("✅ Thank you! Now send a link.")
        else:
            await cb.answer("❌ Not joined yet!", show_alert=True)

@app.on_message(filters.command("panel") & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    await message.reply(
        "🛠️ Admin Panel:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Stats", callback_data="stats")],
            [InlineKeyboardButton("➕ Add Credits", callback_data="addcredit")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
        ])
    )

@app.on_callback_query(filters.user(ADMIN_ID))
async def admin_actions(client, query: CallbackQuery):
    if query.data == "stats":
        u, r = get_user_data(), get_referral_data()
        await query.message.edit(
            f"👤 Total Users: {len(u)}\n🔗 Referrals Used: {sum([v['referrals'] for v in r.values()])}"
        )
    elif query.data == "addcredit":
        await query.message.edit("✏️ Send user ID and amount like:\n`123456789 3`")
        user_states[query.from_user.id] = "waiting_credit"
    elif query.data == "broadcast":
        await query.message.edit("📢 Now send the message to broadcast")
        user_states[query.from_user.id] = "waiting_broadcast"

@app.on_message(filters.text & filters.user(ADMIN_ID))
async def admin_inputs(client, message: Message):
    state = user_states.get(message.from_user.id)
    if state == "waiting_credit":
        try:
            uid, amt = message.text.split()
            r = get_referral_data()
            if uid not in r:
                r[uid] = {"referrals": 0, "referred_by": None}
            r[uid]["referrals"] += int(amt)
            save_referral_data(r)
            await message.reply(f"✅ Added {amt} credits to `{uid}`")
        except:
            await message.reply("❌ Invalid format. Use: `user_id amount`")
        user_states.pop(message.from_user.id, None)

    elif state == "waiting_broadcast":
        with open("users.txt") as f:
            users = f.read().splitlines()
        sent, fail = 0, 0
        for u in users:
            try:
                await app.send_message(int(u), message.text)
                sent += 1
            except:
                fail += 1
        await message.reply(f"📤 Broadcast complete.\n✅ Sent: {sent} | ❌ Failed: {fail}")
        user_states.pop(message.from_user.id, None)

@app.on_message(filters.text & ~filters.command(["start", "panel"]))
async def downloader(client, message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if force_join_required(message.from_user.id):
        return await message.reply("🔒 Please join channel first.")

    user_data = get_user_data()
    referral_data = get_referral_data()

    if user_id not in user_data:
        user_data[user_id] = {"downloads": 0, "last_reset": datetime.utcnow().strftime("%Y-%m-%d")}
    if user_id not in referral_data:
        referral_data[user_id] = {"referrals": 0, "referred_by": None}

    if user_data[user_id]["downloads"] >= 4:
        if referral_data[user_id]["referrals"] <= 0:
            return await message.reply("🚫 Limit reached.\n💡 Refer to get more.")
        referral_data[user_id]["referrals"] -= 1
    else:
        user_data[user_id]["downloads"] += 1

    save_user_data(user_data)
    save_referral_data(referral_data)

    msg = await message.reply("⏳ Processing your link...")
    try:
        bar = ["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]
        for b in bar:
            await msg.edit(f"⬇️ Downloading...\n`{b}`")
            await asyncio.sleep(0.3)

        data = get_data(text)
        if not data:
            return await msg.edit("❌ Invalid or expired link.")

        caption = f"🎬 **{data['file_name']}**\n📦 Size: {data['size'] or 'N/A'}"
        await client.send_video(
            message.chat.id,
            video=data["link"],
            caption=caption,
            supports_streaming=True
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ Error: `{e}`")

async def reset_task():
    while True:
        reset_daily_downloads()
        await asyncio.sleep(86400)

if __name__ == "__main__":
    app.start()
    app.loop.create_task(reset_task())
    idle()
        
