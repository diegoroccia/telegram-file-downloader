from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterDocument
from datetime import date
import glob

# import sqlite3

api_id = 998937
api_hash = "438c3382cff1b6bc01ec948bad04d5f3"
channel_name = "🇮🇹 eBooksItalia 📚 [ #TeamAlberello🌳 #NoTarocchi ☣️ ]"
# channel_name = "📚 Gruppo eBooksItalia 📚"
# channel_name=':it: eBooksItalia :books: [ #TeamAlberello:deciduous_tree: #NoTarocchi ☣ ]'
offset = date(year=2019, month=9, day=26)

client = TelegramClient("anon", api_id, api_hash)

client.start()
# ---------------------------------------


room = [dialog for dialog in client.get_dialogs() if dialog.name == channel_name][0]

# for msg in client.iter_messages(channel_name, limit=None, filter=InputMessagesFilterDocument, offset_date=offset):
for msg in client.iter_messages(room, limit=None, filter=InputMessagesFilterDocument):
    try:
        file_name = msg.media.document.to_dict()["attributes"][0].get("file_name", "")
        if file_name.endswith("epub"):
            print(
                f"Downloading {file_name} ( uploaded on {msg.media.document.date} )...",
                end="",
            )
            if glob.glob("books/" + file_name):
                print("file already present")
                break
            else:
                client.download_media(message=msg, file="books/")
                print("Done")
    except KeyError:
        print("Unable to download ")
        print(msg.media.document)
        pass
