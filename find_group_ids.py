import json
from telethon.sync import TelegramClient

with open('config.json', 'r') as f:
    config = json.load(f)

for idx, assistant in enumerate(config['assistants']):
    print(f"\nAssistant {idx+1} ({assistant['phone']}):")
    with TelegramClient(f'find_groups_{idx+1}', assistant['api_id'], assistant['api_hash']) as client:
        client.start(phone=assistant['phone'])
        for dialog in client.iter_dialogs():
            if dialog.is_group:
                print(f"{dialog.name}: {dialog.id}")