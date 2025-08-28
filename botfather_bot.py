import logging
from telethon import TelegramClient, events, Button
import asyncio

# Replace with your BotFather token
API_ID = 26117875  # From config.json main account
API_HASH = 'e121705b6821eb0287a0a2d264fd6f56'  # From config.json main account
BOT_TOKEN = '8401265217:AAErGXj2yU45162YXHYMPRPSMm2zxLQWnvM'

logging.basicConfig(level=logging.INFO)

# Create the bot client
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    username = getattr(sender, 'username', None)
    first_name = getattr(sender, 'first_name', '')
    last_name = getattr(sender, 'last_name', '')
    user_id = sender.id
    if username:
        identifier = f"@{username}"
        dm_link = f"https://t.me/{username}"
    elif first_name or last_name:
        identifier = (first_name or '') + (" " + last_name if last_name else '')
        identifier = identifier.strip()
        dm_link = None
    else:
        identifier = str(user_id)
        dm_link = None
    user_info_lines = [
        f"Identifier: {identifier}",
        f"User ID: {user_id}"
    ]
    if dm_link:
        user_info_lines.append(f"Direct Message: {dm_link}")
    inbox = f"[CLIENT INFO]\n" + "\n".join(user_info_lines) + "\n\n[INBOX]\n"
    if event.text:
        inbox += event.text
    # Add a button if username exists
    reply_markup = None
    if username:
        reply_markup = [[Button.url('Open Chat', f'https://t.me/{username}')]]
    await event.respond(inbox, buttons=reply_markup)

print('Bot is running...')
bot.run_until_disconnected()
