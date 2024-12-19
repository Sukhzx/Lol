import asyncio
import random
import string
import datetime
from pyrogram import Client, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes

# Telegram API credentials are stored per user
user_details = {}
keys = {}  # Format: {key: (expiration_date, owner_id)}

OWNER_USERNAME = "jatt_agya"  # Owner username for key generation
BOT_TOKEN = "8171439141:AAE1EaS42AkruKHGi0-lIRKIqN0KEtgIgeU"

# Key Validation Functions
def generate_key(owner_name, days):
    random_key = "".join(random.choices(string.ascii_letters + string.digits, k=5))
    key = f"{owner_name}-{random_key}"
    expiration_date = datetime.datetime.now() + datetime.timedelta(days=days)
    return key, expiration_date

def is_valid_key(key, user_id):
    if key in keys:
        expiration_date, owner_id = keys[key]
        if owner_id == user_id and expiration_date > datetime.datetime.now():
            return True
    return False

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=user_id,
        text=f"👋 Welcome to the bot!\n\nCreated by: @{OWNER_USERNAME}\n\nTo use this bot, redeem your access key first.\n\nUse: `/redeem <key>`",
        parse_mode="Markdown",
    )

# Key Redemption Handler
async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if len(context.args) == 1:
        key = context.args[0]
        if is_valid_key(key, user_id):
            user_details[user_id] = {"key": key, "state": "awaiting_login"}
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Key redeemed successfully! Please log in to proceed.\nSend your credentials in the format: `phone_number:api_id:api_hash`",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Invalid or expired key. Please try again.")
    else:
        await update.message.reply_text("⚠️ Usage: `/redeem <key>`", parse_mode="Markdown")

# Key Generation Handler (Owner Only)
async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username == OWNER_USERNAME and len(context.args) == 2:
        try:
            key, days = context.args[0], int(context.args[1])
            new_key, expiration_date = generate_key(OWNER_USERNAME, days)
            keys[new_key] = (expiration_date, update.effective_chat.id)
            await update.message.reply_text(f"✅ Key generated: `{new_key}` (Valid for {days} days)", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("⚠️ Invalid days. Please use `/gen <key> <days>`", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ You are not authorized to generate keys.")

# Collect API Credentials
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if user_id in user_details and user_details[user_id]["state"] == "awaiting_login":
        details = update.message.text.split(":")
        if len(details) == 3:
            phone, api_id, api_hash = details
            user_details[user_id].update({"phone": phone, "api_id": api_id, "api_hash": api_hash, "state": "logged_in"})
            await context.bot.send_message(
                chat_id=user_id,
                text="✅ Login successful! Use the menu to choose an action.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Send to Groups", callback_data="send_groups")],
                    [InlineKeyboardButton("Send to Personal DMs", callback_data="send_dms")],
                ]),
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Invalid format. Please use: `phone_number:api_id:api_hash`",
                parse_mode="Markdown",
            )

# Button Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.message.chat.id
    await query.answer()

    if query.data == "send_groups":
        await query.edit_message_text("🔹 Please send the message you want to forward to groups.")
        user_details[user_id]["target"] = "groups"
    elif query.data == "send_dms":
        await query.edit_message_text("🔹 Please send the message you want to forward to personal DMs.")
        user_details[user_id]["target"] = "dms"

# Forward Messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    if "target" in user_details[user_id]:
        target = user_details[user_id]["target"]
        message = update.message.text

        # Simulated sending logic (replace with actual implementation)
        if target == "groups":
            await update.message.reply_text("✅ Message forwarded to all groups.")
        elif target == "dms":
            await update.message.reply_text("✅ Message forwarded to all personal DMs.")

# Main Application
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("redeem", redeem))
    app.add_handler(CommandHandler("gen", generate))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    print("Bot is running...")
    await app.run_polling()

# Start the bot
if __name__ == "__main__":
    asyncio.run(main())