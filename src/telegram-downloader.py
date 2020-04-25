from telethon import TelegramClient, sync
from telethon.tl.types import InputMessagesFilterDocument
from datetime import date, datetime, timedelta
from lxml import etree
import glob
import pytz
import sqlite3
import sys
import yaml
import zipfile


def get_epub_info(fname):
    ns = {
        "n": "urn:oasis:names:tc:opendocument:xmlns:container",
        "pkg": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }

    # prepare to read from the .epub file
    zip = zipfile.ZipFile(fname)

    # find the contents metafile
    txt = zip.read("META-INF/container.xml")
    tree = etree.fromstring(txt)
    cfname = tree.xpath("n:rootfiles/n:rootfile/@full-path", namespaces=ns)[0]

    # grab the metadata block from the contents metafile
    cf = zip.read(cfname)
    tree = etree.fromstring(cf)
    p = tree.xpath("/pkg:package/pkg:metadata", namespaces=ns)[0]

    # repackage the data
    res = {}
    for s in ["title", "language", "creator", "date", "identifier"]:
        if len(res) > 0:
            res[s] = p.xpath("dc:%s/text()" % (s), namespaces=ns)[0]
    return res


with open("/config/config.yaml") as cfg_file:
    config = yaml.load(cfg_file)
    api_id = config.get("api_id")
    api_hash = config.get("api_hash")
    channel = config.get("channel")

client = TelegramClient("anon", api_id, api_hash)

client.start()

utc = pytz.UTC

go_back_to = utc.localize(
    datetime.utcnow().replace(minute=0, hour=0, second=0) - timedelta(days=10)
)

print(f"I will go back to {go_back_to}")


rooms = [dialog for dialog in client.get_dialogs() if channel in dialog.name]

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
                # if glob.glob(f"books/{file_name}"):
                #    print(get_epub_info(f"books/{file_name}"))
        except KeyError:
            print("Unable to download ")
            print(msg.media.document)
            pass
        except KeyboardInterrupt:
            print("\n\ngot CTRL+C, stopping ... ")
            connection.close()
            sys.exit(0)


connection.close()
