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
                    f"🎉 ʏᴏᴜ ɢᴏᴛ ᴀ ɴᴇᴡ ʀᴇғᴇʀʀᴀʟ!\n👤 [{user.first_name}](tg://user?id={user.id}) ᴊᴏɪɴᴇᴅ ᴛʜʀᴏᴜɢʜ ʏᴏᴜʀ ʟɪɴᴋ\n💰 +1 ᴅᴏᴡɴʟᴏᴀᴅ ᴄʀᴇᴅɪᴛ"
                )
            except: pass

    save_user_data(user_data)
    save_referral_data(referral_data)

    if force_join_required(user.id):
        return await message.reply(
            "🔐 ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴏᴜʀ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 ᴊᴏɪɴ developer channel", url="https://t.me/+28D1ypobsIxjZjQ1")],
                [InlineKeyboardButton("📢 ᴊᴏɪɴ video link channel", url="https://t.me/+bnQ1FHi3EOk0YjM1")],
                [InlineKeyboardButton("FOLLOW ME BABY 🌚", url="https://www.instagram.com/love_reel_page/profilecard/?igsh=MWpvbWFjd29namlxMQ==")],
                [InlineKeyboardButton("✅ ɪ ᴊᴏɪɴᴇᴅ", callback_data="refresh")]
            ])
        )

    referral_link = f"https://t.me/Video_hub_terabox_bot?start={user.id}"
    await message.reply(
        f"👋 ʜᴇʟʟᴏ {user.mention}\n\n"
        f"📥 sᴇɴᴅ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ.\n\n"
        f"🎁 ᴅᴀɪʟʏ ʟɪᴍɪᴛ: 4\n"
        f"➕ 1 ʀᴇғᴇʀʀᴀʟ = +1 ᴇxᴛʀᴀ\n"
        f"🔗 ʏᴏᴜʀ ʀᴇғᴇʀʀᴀʟ:\n`{referral_link}`"
    )

@app.on_callback_query()
async def join_refresh(client, cb: CallbackQuery):
    if cb.data == "refresh":
        if not force_join_required(cb.from_user.id):
            await cb.message.delete()
            await cb.message.reply("✅ ᴛʜᴀɴᴋ ʏᴏᴜ! ɴᴏᴡ sᴇɴᴅ ᴀ ʟɪɴᴋ.")
        else:
            await cb.answer("❌ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ʏᴇᴛ!", show_alert=True)

@app.on_message(filters.command("panel") & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    await message.reply(
        "🛠️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ:",
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
            f"👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs: {len(u)}\n🔗 ʀᴇғᴇʀʀᴀʟs ᴜsᴇᴅ: {sum([v['referrals'] for v in r.values()])}"
        )
    elif query.data == "addcredit":
        await query.message.edit("✏️ sᴇɴᴅ ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴀᴍᴏᴜɴᴛ ʟɪᴋᴇ:\n`123456789 3`")
        app.set_state(query.from_user.id, "waiting_credit")
    elif query.data == "broadcast":
        await query.message.edit("📢 ɴᴏᴡ sᴇɴᴅ ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ")
        app.set_state(query.from_user.id, "waiting_broadcast")

@app.on_message(filters.text & filters.user(ADMIN_ID))
async def admin_inputs(client, message: Message):
    state = app.get_state(message.from_user.id)
    if state == "waiting_credit":
        try:
            uid, amt = message.text.split()
            r = get_referral_data()
            if uid not in r:
                r[uid] = {"referrals": 0, "referred_by": None}
            r[uid]["referrals"] += int(amt)
            save_referral_data(r)
            await message.reply(f"✅ ᴀᴅᴅᴇᴅ {amt} ᴄʀᴇᴅɪᴛs ᴛᴏ `{uid}`")
        except:
            await message.reply("❌ ɪɴᴠᴀʟɪᴅ ғᴏʀᴍᴀᴛ. ᴜsᴇ: `user_id amount`")
        app.clear_state(message.from_user.id)

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
        await message.reply(f"📤 ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ.\n✅ sᴇɴᴛ: {sent} | ❌ ғᴀɪʟᴇᴅ: {fail}")
        app.clear_state(message.from_user.id)

@app.on_message(filters.text & ~filters.command(["start", "panel"]))
async def downloader(client, message: Message):
    user_id = str(message.from_user.id)
    text = message.text.strip()

    if force_join_required(message.from_user.id):
        return await message.reply("🔒 ᴘʟᴇᴀsᴇ ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ғɪʀsᴛ.")

    user_data = get_user_data()
    referral_data = get_referral_data()

    if user_id not in user_data:
        user_data[user_id] = {"downloads": 0, "last_reset": datetime.utcnow().strftime("%Y-%m-%d")}
    if user_id not in referral_data:
        referral_data[user_id] = {"referrals": 0, "referred_by": None}

    if user_data[user_id]["downloads"] >= 4:
        if referral_data[user_id]["referrals"] <= 0:
            return await message.reply("🚫 ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ.\n💡 ʀᴇғᴇʀ ᴛᴏ ɢᴇᴛ ᴍᴏʀᴇ.")
        referral_data[user_id]["referrals"] -= 1
    else:
        user_data[user_id]["downloads"] += 1

    save_user_data(user_data)
    save_referral_data(referral_data)

    msg = await message.reply("⏳ ᴘʀᴏᴄᴇssɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ...")
    try:
        bar = ["▰▱▱▱▱", "▰▰▱▱▱", "▰▰▰▱▱", "▰▰▰▰▱", "▰▰▰▰▰"]
        for b in bar:
            await msg.edit(f"⬇️ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ...\n`{b}`")
            await asyncio.sleep(0.3)

        data = get_data(text)
        if not data:
            return await msg.edit("❌ ɪɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ʟɪɴᴋ.")
        caption = f"🎬 **{data['file_name']}**\n📦 sɪᴢᴇ: {data['size'] or 'N/A'}"
        await client.send_video(
            message.chat.id,
            video=data["link"],
            caption=caption,
            supports_streaming=True
        )
        await msg.delete()
    except Exception as e:
        await msg.edit(f"❌ ᴇʀʀᴏʀ: `{e}`")

# ------------------- Main -------------------

async def reset_task():
    while True:
        reset_daily_downloads()
        await asyncio.sleep(86400)

async def main():
    try:
        await app.start()
        asyncio.create_task(reset_task())
        print("✅ Bot is running...")
        await idle()
    except Exception as e:
        if "FLOOD_WAIT" in str(e):
            wait_time = int(str(e).split("A wait of ")[1].split(" ")[0])
            print(f"⏳ FloodWait detected! Sleeping for {wait_time} seconds...")
            import time
            time.sleep(wait_time + 5)
            os.execvp("python", ["python", "bot.py"])
        else:
            raise e

if __name__ == "__main__":
    asyncio.run(main())
    
