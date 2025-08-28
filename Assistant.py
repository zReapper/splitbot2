

import json
import os
import time
from telethon import TelegramClient, events, Button

with open('config.json', 'r') as f:
    config = json.load(f)

bot_cfg = config['assistants'][0]
api_id = int(bot_cfg['api_id'])
api_hash = bot_cfg['api_hash']
bot_token = bot_cfg['bot_token']

assistant1_cfg = config['assistants'][0]
assistant2_cfg = config['assistants'][1]
assistant1_id = int(assistant1_cfg['bot_id']) if 'bot_id' in assistant1_cfg else None
assistant2_id = int(assistant2_cfg['bot_id']) if 'bot_id' in assistant2_cfg else None

assistant_client_files = [
    os.path.join(os.path.dirname(__file__), 'assistant1_clients.json'),
    os.path.join(os.path.dirname(__file__), 'assistant2_clients.json')
]

def load_clients(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                return set(data.get('clients', []))
            except Exception:
                return set()
    return set()

def save_clients(filename, clients):
    with open(filename, 'w') as f:
        json.dump({'clients': list(clients)}, f)

try:
    with open('assignments.json', 'r') as f:
        assignments = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    assignments = {}

assistant_clients_sets = [load_clients(f) for f in assistant_client_files]

LAST_ASSISTANT_FILE = os.path.join(os.path.dirname(__file__), 'last_assistant.json')
def get_last_assistant():
    if os.path.exists(LAST_ASSISTANT_FILE):
        try:
            with open(LAST_ASSISTANT_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last', 1)
        except Exception:
            return 1
    return 1
def set_last_assistant(idx):
    with open(LAST_ASSISTANT_FILE, 'w') as f:
        json.dump({'last': idx}, f)

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

@bot.on(events.NewMessage)
async def handler(event):
    print("[DEBUG] Handler triggered")
    sender = await event.get_sender()
    username = getattr(sender, 'username', None)
    first_name = getattr(sender, 'first_name', '')
    last_name = getattr(sender, 'last_name', '')
    user_id = sender.id
    # Build a readable message
    identifier = f"@{username}" if username else (first_name + (" " + last_name if last_name else "")).strip() or str(user_id)
    user_info_lines = [
        f"Identifier: {identifier}",
        f"User ID: {user_id}"
    ]
    if username:
        user_info_lines.append(f"Direct Message: https://t.me/{username}")
    inbox = f"[CLIENT INFO]\n" + "\n".join(user_info_lines) + "\n\n[INBOX]\n"
    if event.text:
        inbox += event.text
    elif event.message:
        inbox += str(event.message)
    else:
        inbox += "[No text]"
    # Add a button if username exists
    reply_markup = None
    if username:
        reply_markup = [[Button.url('Open Chat', f'https://t.me/{username}')]]

    # Assignment logic: assign each user to an assistant (50/50, persistent)
    if username not in assignments or not isinstance(assignments[username], dict):
        last_idx = get_last_assistant()
        idx = 0 if last_idx == 1 else 1
        assignments[username] = {"assistant": idx}
        assistant_clients_sets[idx].add(username)
        save_clients(assistant_client_files[idx], assistant_clients_sets[idx])
        set_last_assistant(idx)
        with open('assignments.json', 'w') as f:
            json.dump(assignments, f)
    else:
        idx = assignments[username]["assistant"]


    # Nachricht an die jeweilige Gruppe weiterleiten
    group_ids = [-1002955174685, -1002954577695]  # -1002955174685 für Assistent 1, -1002954577695 für Assistent 2
    group_id = group_ids[idx]
    try:
        await bot.send_message(group_id, inbox, buttons=reply_markup)
        print(f"[DEBUG] Nachricht an Gruppe {group_id} gesendet.")
    except Exception as e:
        print(f"[ERROR] Fehler beim Senden an Gruppe {group_id}: {e}")

print('Universal relay bot with 50/50 assignment is running...')
bot.run_until_disconnected()
# assistant2_bot_client = TelegramClient('assistant_2_bot', assistant2_cfg['api_id'], assistant2_cfg['api_hash'])

async def save_assignments():
    with open('assignments.json', 'w') as f:
        json.dump(assignments, f)

# List of usernames or IDs to ignore (do not forward or auto-reply)
ignore_users = set(config.get('ignore_users', []))

# Restriction: users in restricted_users.json will never get a message from the bot or be sent to assistants
restricted_users_file = os.path.join(os.path.dirname(__file__), 'restricted_users.json')
restricted_users = set()
try:
    with open(restricted_users_file, 'r') as rf:
        data = json.load(rf)
        restricted_users.update(data.get('users', []))
except Exception:
    pass

# List of simple greetings to match
simple_greetings = {"hey", "hi", "hello", "hallo", "servus", "guten tag", "moin", "yo", "hola"}

# Helper: get assistant bot usernames from config (must be set in config.json)
assistant_bot_usernames = [assistant1_cfg.get('bot_username'), assistant2_cfg.get('bot_username')]

def load_clients(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                data = json.load(f)
                return set(data.get('clients', []))
            except Exception:
                return set()
    return set()

def save_clients(filename, clients):
    with open(filename, 'w') as f:
        json.dump({'clients': list(clients)}, f)

assistant_client_files = [
    os.path.join(os.path.dirname(__file__), 'assistant1_clients.json'),
    os.path.join(os.path.dirname(__file__), 'assistant2_clients.json')
]

assistant_clients_sets = [load_clients(f) for f in assistant_client_files]

@main_client.on(events.NewMessage(incoming=True))
async def handler(event):
    print("[DEBUG] Handler triggered for incoming message.")
    # Process all chats (private, group, channel)
    print(f"[DEBUG] Chat type: private={event.is_private}, group={event.is_group}, channel={event.is_channel}")
    # Only process text messages from private chats
    if event.text and not event.is_private:
        print("[DEBUG] Text message not from private chat. Returning.")
        return
    sender = await event.get_sender()
    # Robust username extraction: username, else name, else ID
    latest_username = getattr(sender, 'username', None)
    if latest_username:
        print('[DEBUG] Username found directly on sender')
    else:
        try:
            entity = await event.client.get_entity(sender.id)
            latest_username = getattr(entity, 'username', None)
            print(f"[DEBUG] Username fetched from entity: {latest_username}")
        except Exception as e:
            print(f"[DEBUG] Exception fetching username from entity: {e}")
            latest_username = None
    # Always have a username for assignment and display
    if latest_username:
        display_name = f"@{latest_username}"
        username = latest_username
    elif getattr(sender, 'first_name', None) or getattr(sender, 'last_name', None):
        display_name = (getattr(sender, 'first_name', '') or '') + (" " + getattr(sender, 'last_name', '') if getattr(sender, 'last_name', None) else '')
        display_name = display_name.strip()
        username = display_name.replace(' ', '_')
    else:
        display_name = str(sender.id)
        username = str(sender.id)
    message = event.text.strip().lower()

    # Always show the Telegram username (with @) at the top, or 'No username available'
    if latest_username:
        username_line = f"@{latest_username}"
        dm_link = f"https://t.me/{latest_username}"
    elif getattr(sender, 'first_name', None) or getattr(sender, 'last_name', None):
        username_line = (getattr(sender, 'first_name', '') or '') + (" " + getattr(sender, 'last_name', '') if getattr(sender, 'last_name', None) else '')
        username_line = username_line.strip()
        dm_link = None
    else:
        username_line = str(sender.id)
        dm_link = None
    # Always include user ID and a clean direct link if possible
    user_info_lines = [
        f"Identifier: {username_line}",
        f"User ID: {sender.id}"
    ]
    if dm_link:
        user_info_lines.append(f"Direct Message: {dm_link}")

    # Ignore users in the ignore_users list or restricted_users
    if username in ignore_users or username in restricted_users:
        print(f"[DEBUG] User {username} is in ignore or restricted list. Returning.")
        return

    now = int(time.time())
    twentyfour_hours = 24 * 60 * 60
    ten_days = 10 * 24 * 60 * 60

    # Always define these before use
    is_new_client = False
    is_long_ago = False

    # Assign client to assistant if not already assigned (strict round-robin)
    if username in restricted_users:
        print(f"[DEBUG] User {username} is in restricted_users. Returning.")
        return

    if username not in assignments or isinstance(assignments[username], int):
        last_idx = get_last_assistant()
        print(f"[DEBUG] Assigning NEW user {username} (id: {sender.id}) to assistant {last_idx}")
        idx = 0 if last_idx == 1 else 1  # Alternate: if last was 1, now 0; if last was 0, now 1
        assignments[username] = {"assistant": idx, "last_message_time": now, "messages": [], "greeted": False, "last_greeted": 0, "helped": False}
        assistant_clients_sets[idx].add(username)
        save_clients(assistant_client_files[idx], assistant_clients_sets[idx])
        set_last_assistant(idx)
        is_new_client = True
        print(f"[DEBUG] Existing user {username} (id: {sender.id}) assigned to assistant {assignments[username]['assistant']}")
    else:
        idx = assignments[username]["assistant"]
        last_time = assignments[username].get("last_message_time", 0)
        if now - last_time > ten_days:
            is_long_ago = True
        assignments[username]["last_message_time"] = now
    # --- Improved batching logic: Only one summary per user per window ---
    import tempfile, os, base64, requests
    now_ts = int(time.time())
    batch_window = 0  # No batching delay, process immediately
    # Initialize batching state if not present
    if 'batch_start' not in assignments[username]:
        assignments[username]['batch_start'] = now_ts
    if 'pending_summary' not in assignments[username]:
        assignments[username]['pending_summary'] = False
    if 'photo_links' not in assignments[username]:
        assignments[username]['photo_links'] = []
    if 'video_links' not in assignments[username]:
        assignments[username]['video_links'] = []


    # Collect messages/media and store media message IDs for batch forwarding
    if 'media_message_ids' not in assignments[username]:
        assignments[username]['media_message_ids'] = []
    if event.photo or event.document or event.video:
        # Store the message ID for later forwarding
        assignments[username]['media_message_ids'].append(event.message.id)
    if event.photo:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png', dir=os.path.dirname(__file__)) as tmpfile:
            photo_path = tmpfile.name
        await event.download_media(file=photo_path)
        try:
            with open(photo_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            response = requests.post('https://api.imgbb.com/1/upload', data={
                'key': 'cb11ecfde7065f3e4c403559a16fcc8b',
                'image': b64
            })
            url = response.json()['data']['url'] if response.ok and response.json().get('success') else None
        except Exception:
            url = None
        if url:
            assignments[username]['photo_links'].append(url)
        else:
            assignments[username]['photo_links'].append('upload failed')
    elif event.video:
        import sys
        import concurrent.futures
        import requests.auth
        PIXELDRAIN_API_KEY = '8e67c0b8-589c-4d08-aedc-4f539f9e460a'
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4', dir=os.path.dirname(__file__)) as tmpfile:
            video_path = tmpfile.name
        await event.download_media(file=video_path)
        url = None
        error_log = ''
        def upload_pixeldrain():
            try:
                with open(video_path, 'rb') as f:
                    files = {'file': (os.path.basename(video_path), f)}
                    response = requests.post(
                        'https://pixeldrain.com/api/file',
                        files=files,
                        auth=requests.auth.HTTPBasicAuth('user', PIXELDRAIN_API_KEY),
                        timeout=60
                    )
                return response
            except Exception as e:
                return e
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                response = await loop.run_in_executor(pool, upload_pixeldrain)
                if isinstance(response, Exception):
                    error_log += f"Pixeldrain exception: {response}\n"
                    response = None
            except Exception as e:
                error_log += f"Pixeldrain async exception: {e}\n"
                response = None
        if response and hasattr(response, 'ok') and response.ok:
            try:
                resp_json = response.json()
                if resp_json.get('success'):
                    file_id = resp_json['id']
                    url = f'https://pixeldrain.com/u/{file_id}'
                else:
                    error_log += f"Pixeldrain API error: {resp_json}\n"
            except Exception as e:
                error_log += f"Pixeldrain JSON decode error: {e}\n"
        elif response:
            error_log += f"Pixeldrain HTTP error: {response.status_code} {response.text}\n"
        if url:
            assignments[username]['video_links'].append(url)
        else:
            assignments[username]['video_links'].append('video upload failed')
            print(f"[PIXELDRAIN VIDEO UPLOAD ERROR] {error_log}", file=sys.stderr)
    elif event.document:
        assignments[username]["messages"].append("[File sent above]")
    elif event.text:
        assignments[username]["messages"].append(event.text)
    else:
        assignments[username]["messages"].append("[Unknown message type]")

    assignments[username]["messages"] = assignments[username]["messages"][-10:]
    assistant_clients_sets[idx].add(username)
    save_clients(assistant_client_files[idx], assistant_clients_sets[idx])
    await save_assignments()

    # Batching: Only the first message in the window starts the timer and sends the summary

    if assignments[username]['pending_summary']:
        print(f"[DEBUG] Pending summary for {username}, batching. Forcing immediate send.")
        # Instead of returning, force immediate summary send
    else:
        print(f"[DEBUG] Starting batching window for {username}.")
        assignments[username]['pending_summary'] = True
        assignments[username]['batch_start'] = now_ts
        await save_assignments()
        await asyncio.sleep(batch_window)

    # After window, build and send summary
    try:
        print(f"[DEBUG] Building and sending summary for {username}.")
        photo_links = assignments[username].get('photo_links', [])
        clean_links = [l for l in photo_links if l != 'upload failed']
        video_links = assignments[username].get('video_links', [])
        clean_video_links = [l for l in video_links if l != 'video upload failed']
        text_messages = [msg for msg in assignments[username]["messages"] if not msg.startswith("[Photos:") and not msg.startswith("[Photo]") and not msg.startswith("[File]")]
        file_links = [msg for msg in assignments[username]["messages"] if msg.startswith("[File]")]
        print(f'[DEBUG] Sending summary for {username} (id: {sender.id}) to assistant {idx}')

        if text_messages or clean_links or clean_video_links or file_links:
            # Always include only the Telegram username (not name) for the assistant
            print(f"[DEBUG] Sending summary for {username} to assistant {idx}.")
            # Always show the username (with @) at the very top
            inbox = f"[CLIENT INFO]\n" + "\n".join(user_info_lines) + "\n\n[INBOX]\n"
            # Add a Telegram button to open chat if username is available
            reply_markup = None
            if latest_username:
                from telethon import Button
                reply_markup = [[Button.url('Open Chat', f'https://t.me/{latest_username}')]]
            if text_messages:
                inbox += "\n".join(f"- {msg}" for msg in text_messages) + "\n\n"
            if clean_links:
                inbox += "Photos:\n" + "\n\n".join(f"{i+1}. {link}" for i, link in enumerate(clean_links)) + "\n\n"
            if clean_video_links:
                inbox += "Videos:\n" + "\n\n".join(f"{i+1}. {link}" for i, link in enumerate(clean_video_links)) + "\n\n"
            if file_links:
                inbox += "Files:\n" + "\n".join(file_links) + "\n\n"
            if len(clean_links) < len(photo_links):
                inbox += "[Some photos failed to upload]\n\n"
            if len(clean_video_links) < len(video_links):
                inbox += "[Some videos failed to upload]\n\n"
            inbox += "-----------------"
            if sender.username:
                inbox += f"\n\n[Direct Message Link]\nhttps://t.me/{sender.username}"
            # Send the summary as before
            bot_username = assistant_bot_usernames[idx]
            # Use bot_id if bot_username is None or empty
            print(f'[DEBUG] Calling send_message for {username} to {bot_username}')
            if not bot_username or bot_username == 'None' or bot_username == '':
                bot_username = assistant1_cfg.get('bot_id') if idx == 0 else assistant2_cfg.get('bot_id')
            try:
                if reply_markup:
                    await assistant_clients[idx].send_message(bot_username, inbox, buttons=reply_markup)
                else:
                    await assistant_clients[idx].send_message(bot_username, inbox)
                print(f"[DEBUG] About to send message to assistant: {bot_username}")
            except Exception as e:
                print(f"[ERROR] Failed to send inbox to assistant bot_username={bot_username} for client {username}: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"[ERROR] Failed to build/send summary: {e}")

    # Clear batch state
    assignments[username]["messages"] = []
    assignments[username]["photo_links"] = []
    assignments[username]["video_links"] = []
    assignments[username]['pending_summary'] = False
    await save_assignments()

    bot_username = assistant_bot_usernames[idx]
    # Forward all media messages collected in the batch window
    if 'media_message_ids' in assignments[username]:
        for msg_id in assignments[username]['media_message_ids']:
            try:
                # Use bot_id if bot_username is missing or empty
                target = bot_username
                if not target or target == 'None' or target == '':
                    target = assistant1_cfg.get('bot_id') if idx == 0 else assistant2_cfg.get('bot_id')
                is_bot = str(target).lower().endswith('bot')
                if not is_bot:
                    await main_client.forward_messages(target, msg_id)
                    print(f"[DEBUG] Forwarded media message id {msg_id} to assistant userbot {target} for client {username}")
                else:
                    # For bot accounts, download and send the file (not implemented for batch, can be added if needed)
                    pass
            except Exception as e:
                import traceback
                print(f"[ERROR] Failed to send/forward media id {msg_id} to assistant {target} for client {username}: {e}")
                traceback.print_exc()
        assignments[username]['media_message_ids'] = []
        await save_assignments()
    return

    # Unban keyword detection only for new or long-ago clients, and only if it's a direct request
    unban_patterns = [
        r"\b(i need|can i get|how much.*unban|price.*unban|cost.*unban|can you unban|could you unban|please unban|unban my|unban an|unban a|unban account|unban service|unban offer|unban price|unban help|unban support|unban request|unban\?)\b"
    ]
    if (is_new_client or is_long_ago):
        for pat in unban_patterns:
            if re.search(pat, message):
                await event.reply(
                    "To proceed with the unban I need from you:\n\n"
                    "Username\n"
                    "Follower\n"
                    "Reason (screenshot)\n"
                    "Ban date"
                )
                break

    # 24-hour cooldown for greeting/help replies
    greetings = {"hi", "hey", "hello", "hallo", "servus", "guten tag", "moin", "yo", "hola"}
    cooldown = 24 * 60 * 60
    # Only interact if not forbidden/restricted
    if username not in ignore_users and username not in restricted_users:
        # Step 1: Greeting (if 24h passed since last_greeted)
        if (not assignments[username]["greeted"] or now - assignments[username].get("last_greeted", 0) > cooldown) and any(message.startswith(greet) for greet in greetings):
            await event.reply("Hey, how may I help you?")
            assignments[username]["greeted"] = True
            assignments[username]["last_greeted"] = now
            assignments[username]["helped"] = False  # Reset help reply for new period
            await save_assignments()
            return

        # Step 2: Help reply (if 24h passed since last_helped)
        if assignments[username]["greeted"] and (not assignments[username].get("last_helped") or now - assignments[username].get("last_helped", 0) > cooldown) and not any(message.startswith(greet) for greet in greetings) and not assignments[username].get("helped", False):
            await event.reply("Thank you for reaching out! One of our assistants will contact you within 12 hours. We appreciate your patience and look forward to helping you.")
            assignments[username]["helped"] = True
            assignments[username]["last_helped"] = now
            await save_assignments()
            return

    # Wait 1 minute before forwarding to assistants
    await asyncio.sleep(60)


    # After delay, batch all photo links and text into one clean message
    photo_links = assignments[username].pop('photo_links', []) if 'photo_links' in assignments[username] else []
    clean_links = [l for l in photo_links if l != 'upload failed']
    text_messages = [msg for msg in assignments[username]["messages"] if not msg.startswith("[Photos:") and not msg.startswith("[Photo]") and not msg.startswith("[File]")]
    file_links = [msg for msg in assignments[username]["messages"] if msg.startswith("[File]")]

    # Build the formatted inbox for the assistant
    inbox = "[CLIENT INFO]\n" + "\n".join(user_info_lines) + "\n\n[INBOX]\n"
    if text_messages:
        inbox += "\n".join(f"- {msg}" for msg in text_messages) + "\n\n"
    if clean_links:
        inbox += "Photos:\n" + "\n".join(clean_links) + "\n\n"
    if file_links:
        inbox += "Files:\n" + "\n".join(file_links) + "\n\n"
    if len(clean_links) < len(photo_links):
        inbox += "[Some photos failed to upload]\n\n"
    inbox += "-----------------"
    # Add direct message link if client has a username
    if sender.username:
        inbox += f"\n\n[Direct Message Link]\nhttps://t.me/{sender.username}"

    # Clear messages after sending summary
    assignments[username]["messages"] = []

    # Always define bot_username before sending
    bot_username = assistant_bot_usernames[idx]

    # Forward all media (photos, files, etc.) if present
    if event.photo or event.document:
        try:
            # Detect if assistant is a bot (by username starting with '@' and 'bot' in username)
            is_bot = bot_username.lower().endswith('bot')
            if not is_bot:
                # Forward the original message (media) to the assistant (user account)
                await main_client.forward_messages(bot_username, event.message)
                print(f"[DEBUG] Forwarded media message to assistant userbot {bot_username} for client {username}")
            else:
                # For bot accounts, download and send the file only if it has a valid name
                file = await event.get_message()
                file_name = None
                if hasattr(file, 'file') and hasattr(file.file, 'name'):
                    file_name = file.file.name
                if file_name and file_name != 'unnamed':
                    file_bytes = await event.download_media(file=bytes)
                    await assistant_clients[idx].send_file(bot_username, file_bytes, file_name=file_name)
                    print(f"[DEBUG] Sent media as file to assistant bot {bot_username} for client {username}")
                else:
                    print(f"[DEBUG] Skipped sending file with name '{file_name}' to assistant bot {bot_username} for client {username}")
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to send/forward media to assistant {bot_username} for client {username}: {e}")
            traceback.print_exc()
        # Then send the inbox text as a separate message
        try:
            await assistant_clients[idx].send_message(bot_username, inbox)
            print(f"[DEBUG] Inbox sent to assistant bot_username={bot_username} for client {username}")
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to send inbox to assistant bot_username={bot_username} for client {username}: {e}")
            traceback.print_exc()
    else:
        try:
            # Debug: print out which session is being used to send the message
            print(f"[DEBUG] Using session: {assistant_clients[idx].session.filename if hasattr(assistant_clients[idx], 'session') else assistant_clients[idx]}")
            print(f"[DEBUG] Sending to bot_username: {bot_username}")
            print(f"[DEBUG] Sending inbox to assistant bot_username={bot_username} for client {username}")
            result = await assistant_clients[idx].send_message(bot_username, inbox)
            print(f"[DEBUG] Message sent result: {result}")
        except Exception as e:
            import traceback
            print(f"[ERROR] Failed to send inbox to assistant bot_username={bot_username} for client {username}: {e}")
            traceback.print_exc()

# --- Admin Control Bot ---
control_bot_cfg = config.get('control_bot', {})
if control_bot_cfg.get('bot_token'):
    control_bot = TelegramClient('control_bot', assistant1_cfg['api_id'], assistant1_cfg['api_hash'])
else:
    control_bot = None

# State for missed client checker
missed_checker_running = True

async def missed_clients_checker_control():
    global missed_checker_running
    while True:
        if missed_checker_running:
            await missed_clients_checker()
        await asyncio.sleep(10)

# --- Admin Control Bot Command Handlers ---
if control_bot:
    @control_bot.on(events.NewMessage(pattern='/stopmissed'))
    async def stopmissed_handler(event):
        global missed_checker_running
        missed_checker_running = not missed_checker_running
        status = 'paused' if not missed_checker_running else 'resumed'
        await event.reply(f"Missed client reassignment is now {status}.")

    @control_bot.on(events.NewMessage(pattern='/missed'))
    async def missed_handler(event):
        missed1 = load_missed_clients(missed_clients_files[0])
        missed2 = load_missed_clients(missed_clients_files[1])
        msg = f"Assistant 1 missed: {[c['username'] for c in missed1]}\nAssistant 2 missed: {[c['username'] for c in missed2]}"
        await event.reply(msg)

    @control_bot.on(events.NewMessage(pattern='/clients1'))
    async def clients1_handler(event):
        clients = list(load_clients(assistant_client_files[0]))
        await event.reply(f"Assistant 1 clients: {clients}")

    @control_bot.on(events.NewMessage(pattern='/clients2'))
    async def clients2_handler(event):
        clients = list(load_clients(assistant_client_files[1]))
        await event.reply(f"Assistant 2 clients: {clients}")

    @control_bot.on(events.NewMessage(pattern='/addclient1 (.+)'))
    async def addclient1_handler(event):
        username = event.pattern_match.group(1)
        clients = load_clients(assistant_client_files[0])
        clients.add(username)
        save_clients(assistant_client_files[0], clients)
        await event.reply(f"Added {username} to assistant 1 clients.")

    @control_bot.on(events.NewMessage(pattern='/addclient2 (.+)'))
    async def addclient2_handler(event):
        username = event.pattern_match.group(1)
        clients = load_clients(assistant_client_files[1])
        clients.add(username)
        save_clients(assistant_client_files[1], clients)
        await event.reply(f"Added {username} to assistant 2 clients.")

    @control_bot.on(events.NewMessage(pattern='/removeclient1 (.+)'))
    async def removeclient1_handler(event):
        username = event.pattern_match.group(1)
        clients = load_clients(assistant_client_files[0])
        if username in clients:
            clients.remove(username)
            save_clients(assistant_client_files[0], clients)
            await event.reply(f"Removed {username} from assistant 1 clients.")
        else:
            await event.reply(f"{username} not found in assistant 1 clients.")

    @control_bot.on(events.NewMessage(pattern='/removeclient2 (.+)'))
    async def removeclient2_handler(event):
        username = event.pattern_match.group(1)
        clients = load_clients(assistant_client_files[1])
        if username in clients:
            clients.remove(username)
            save_clients(assistant_client_files[1], clients)
            await event.reply(f"Removed {username} from assistant 2 clients.")
        else:
            await event.reply(f"{username} not found in assistant 2 clients.")

    @control_bot.on(events.NewMessage(pattern='/switchclient (.+)'))
    async def switchclient_handler(event):
        username = event.pattern_match.group(1)
        clients1 = load_clients(assistant_client_files[0])
        clients2 = load_clients(assistant_client_files[1])
        if username in clients1:
            clients1.remove(username)
            clients2.add(username)
            save_clients(assistant_client_files[0], clients1)
            save_clients(assistant_client_files[1], clients2)
            await event.reply(f"Switched {username} from assistant 1 to assistant 2.")
        elif username in clients2:
            clients2.remove(username)
            clients1.add(username)
            save_clients(assistant_client_files[1], clients2)
            save_clients(assistant_client_files[0], clients1)
            await event.reply(f"Switched {username} from assistant 2 to assistant 1.")
        else:
            await event.reply(f"{username} not found in either assistant's client list.")

    @control_bot.on(events.NewMessage(pattern='/help'))
    async def help_handler(event):
        help_text = (
            "Available admin commands:\n"
            "/help — Show this help message\n"
            "/stopmissed — Pause/resume the 24-hour missed client reassignment\n"
            "/missed — Show all missed clients for both assistants\n"
            "/clients1 — Show all clients assigned to assistant 1\n"
            "/clients2 — Show all clients assigned to assistant 2\n"
            "/addclient1 <username> — Add a client to assistant 1\n"
            "/addclient2 <username> — Add a client to assistant 2\n"
            "/removeclient1 <username> — Remove a client from assistant 1\n"
            "/removeclient2 <username> — Remove a client from assistant 2\n"
            "/switchclient <username> — Move a client to the other assistant\n"
        )
        await event.reply(help_text)

async def start_main_user_with_info(client, phone, role):
    print(f"\nLogging in as {role} user with phone: {phone}")
    await client.start(phone=phone)
    print(f"{role.capitalize()} user logged in.")

async def start_bot_with_info(client, bot_token, role):
    print(f"\n[DEBUG] Logging in as {role} bot with token: {bot_token[:8]}... (hidden)")
    try:
        await client.start(bot_token=bot_token)
        print(f"[DEBUG] {role.capitalize()} bot logged in successfully.")
    except Exception as e:
        print(f"[ERROR] {role.capitalize()} bot failed to log in: {e}")

async def start_user_with_info(client, phone, role):
    print(f"\nLogging in as {role} user with phone: {phone}")
    await client.start(phone=phone)
    print(f"{role.capitalize()} user logged in.")

async def main():
    await start_main_bot_with_info(main_client, bot_token)
    await start_bot_with_info(assistant_clients[0], assistant1_cfg.get('bot_token', ''), 'assistant 1')
    # Login assistant 2 as user (userbot), not as bot
    await start_user_with_info(assistant_clients[1], assistant2_cfg['phone'], 'assistant 2')
    # Only log in assistant2_bot_client, do not send messages from it to @AssistantN0W1BOT
    # await start_bot_with_info(assistant2_bot_client, assistant2_cfg.get('bot_token', ''), 'assistant 2 (bot)')
    # Start missed clients checker (controllable)
    if control_bot:
        asyncio.create_task(missed_clients_checker_control())
        await control_bot.start(bot_token=control_bot_cfg['bot_token'])
        print('Control bot started.')
    else:
        asyncio.create_task(missed_clients_checker())
    print('All clients started. Listening for messages...')
    await main_client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

