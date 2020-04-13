from telethon import TelegramClient, sync
from telethon.tl.types import InputMessagesFilterDocument
from datetime import date, datetime, timedelta
import glob
import pytz
import sqlite3
import sys
import yaml

with open("config.yaml") as cfg_file:
    config = yaml.load(cfg_file)
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")

client = TelegramClient("anon", api_id, api_hash)

client.start()

utc = pytz.UTC

go_back_to = utc.localize(
    datetime.utcnow().replace(minute=0, hour=0, second=0) - timedelta(days=1)
)

print(f"I will go back to {go_back_to}")


rooms = [dialog for dialog in client.get_dialogs() if "eBooksItalia" in dialog.name]

connection = sqlite3.Connection("database.sqlite3")

for room in rooms:
    print(f"Scraping {room.name} ...")
    for msg in client.iter_messages(
        room, limit=None, filter=InputMessagesFilterDocument
    ):
        if msg.date < go_back_to:
            break
        try:
            file_name = msg.media.document.to_dict()["attributes"][0].get(
                "file_name", ""
            )
            if file_name.endswith("epub"):
                print(
                    f" - [{msg.id} / {msg.media.document.date}] {file_name} ...",
                    end="",
                )
                if (
                    len(
                        connection.execute(
                            f"select * from Messages where msg_id = {msg.id}"
                        ).fetchall()
                    )
                    > 0
                ):
                    print("message already in the DB")
                elif glob.glob("books/" + file_name):
                    print("file already present")
                else:
                    client.download_media(message=msg, file="books/")
                    connection.execute(
                        f'insert into Messages values ( {msg.id}, "{file_name}" );'
                    )
                    connection.commit()
                    print("\u2713")
        except KeyError:
            print("Unable to download ")
            print(msg.media.document)
            pass
        except KeyboardInterrupt:
            print("\n\ngot CTRL+C, stopping ... ")
            connection.close()
            sys.exit(0)


connection.close()
