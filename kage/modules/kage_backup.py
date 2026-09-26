# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

# ©️ Codrago, 2024-2030
# This file is a part of Heroku Userbot
# 🌐 https://github.com/coddrago/Heroku
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import asyncio
import contextlib
import datetime
import hashlib
import io
import logging
import os
import re
import time
import zipfile
import orjson

from pathlib import Path

from herokutl.tl.types import Message

from .. import loader, utils
from ..database import migrate_legacy_db
from ..inline.types import BotInlineCall

# Images built before `cryptography` was added to requirements.txt lack it;
# the module must still load there and keep unencrypted backups working.
try:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

logger = logging.getLogger(__name__)

# Container: BACKUP_MAGIC | salt | nonce | AES-256-GCM ciphertext+tag.
# The whole header is authenticated as associated data. KDF parameters are
# pinned to the format version, so changing them requires a new magic.
BACKUP_MAGIC = b"KAGEBK1"
ENCRYPTED_SUFFIX = ".kbak"
SALT_SIZE = 16
NONCE_SIZE = 12
GCM_TAG_SIZE = 16
HEADER_SIZE = len(BACKUP_MAGIC) + SALT_SIZE + NONCE_SIZE
KEY_SIZE = 32
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
# scrypt needs 128 * N * r bytes; OpenSSL's default 32 MiB cap is exactly that, so leave headroom
SCRYPT_MAXMEM = 2 * 128 * SCRYPT_N * SCRYPT_R

RESTORE_CALLBACK_CONFIRM = "kage/backupall/restore/confirm"
RESTORE_CALLBACK = "kage/backupall/restore"


class BackupCryptoError(Exception):
    string_key: str


class BackupPasswordRequired(BackupCryptoError):
    string_key = "password_required"


class BackupDecryptionError(BackupCryptoError):
    string_key = "wrong_password"


class BackupCryptoUnavailable(BackupCryptoError):
    string_key = "crypto_unavailable"


def is_encrypted_backup(data: bytes) -> bool:
    return data.startswith(BACKUP_MAGIC)


def _require_crypto():
    if AESGCM is None:
        raise BackupCryptoUnavailable("The 'cryptography' package is not installed")


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=SCRYPT_MAXMEM,
        dklen=KEY_SIZE,
    )


def encrypt_backup(data: bytes, password: str) -> bytes:
    """Encrypts backup bytes into the KAGEBK1 container.

    Raises:
        ValueError: If the password is empty.
        BackupCryptoUnavailable: If `cryptography` is not installed.
    """
    if not password:
        raise ValueError("Backup password must not be empty")

    _require_crypto()
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    header = BACKUP_MAGIC + salt + nonce
    return header + AESGCM(_derive_key(password, salt)).encrypt(nonce, data, header)


def decrypt_backup(data: bytes, password: str) -> bytes:
    """Decrypts a KAGEBK1 container, verifying its integrity.

    Raises:
        ValueError: If the data is not an encrypted Kage backup.
        BackupPasswordRequired: If no password is given.
        BackupDecryptionError: On a wrong password or damaged/truncated data.
        BackupCryptoUnavailable: If `cryptography` is not installed.
    """
    if not is_encrypted_backup(data):
        raise ValueError("Not an encrypted Kage backup")

    if not password:
        raise BackupPasswordRequired("Encrypted backup needs a password")

    if len(data) < HEADER_SIZE + GCM_TAG_SIZE:
        raise BackupDecryptionError("Encrypted backup is truncated")

    _require_crypto()
    header = data[:HEADER_SIZE]
    salt = header[len(BACKUP_MAGIC) : len(BACKUP_MAGIC) + SALT_SIZE]
    nonce = header[-NONCE_SIZE:]
    try:
        return AESGCM(_derive_key(password, salt)).decrypt(
            nonce, data[HEADER_SIZE:], header
        )
    except InvalidTag:
        raise BackupDecryptionError("Wrong password or damaged backup") from None


@loader.tds
class KageBackupMod(loader.Module):
    """Handles database and modules backups"""

    strings = {
        "name": "KageBackup",
        "password_hint": (
            "🔓 <i>Not encrypted. Set a password to encrypt backups:</i>"
            " <code>{prefix}cfg KageBackup backup_password</code>"
        ),
        "encrypted_note": "🔐 <i>Encrypted with your backup password.</i>",
        "password_required": (
            "🔐 <b>This backup is encrypted. Set the password it was made with:</b>"
            " <code>{prefix}cfg KageBackup backup_password</code>"
        ),
        "wrong_password": (
            "🚫 <b>Can't decrypt the backup: wrong password or damaged file."
            " Nothing was restored.</b>"
        ),
        "crypto_unavailable": (
            "🚫 <b>Backup encryption needs the</b> <code>cryptography</code>"
            " <b>package. Update the Kage image or run</b>"
            " <code>pip install cryptography</code>"
        ),
        "_cfg_doc_backup_password": (
            "Password for encrypting backups (scrypt + AES-256-GCM). Empty ="
            " backups are not encrypted. Encrypted backups can't be restored"
            " without it, so keep it somewhere safe"
        ),
    }

    strings_ru = {
        "password_hint": (
            "🔓 <i>Без шифрования. Задайте пароль, чтобы шифровать бэкапы:</i>"
            " <code>{prefix}cfg KageBackup backup_password</code>"
        ),
        "encrypted_note": "🔐 <i>Зашифровано вашим паролем бэкапов.</i>",
        "password_required": (
            "🔐 <b>Бэкап зашифрован. Укажите пароль, с которым он был создан:</b>"
            " <code>{prefix}cfg KageBackup backup_password</code>"
        ),
        "wrong_password": (
            "🚫 <b>Не удалось расшифровать бэкап: неверный пароль или файл"
            " повреждён. Ничего не восстановлено.</b>"
        ),
        "crypto_unavailable": (
            "🚫 <b>Для шифрования бэкапов нужен пакет</b> <code>cryptography</code>"
            "<b>. Обновите образ Kage или выполните</b>"
            " <code>pip install cryptography</code>"
        ),
        "_cfg_doc_backup_password": (
            "Пароль для шифрования бэкапов (scrypt + AES-256-GCM). Пусто —"
            " бэкапы не шифруются. Без пароля зашифрованный бэкап не"
            " восстановить, храните его надёжно"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "backup_password",
                "",
                lambda: self.strings["_cfg_doc_backup_password"],
                validator=loader.validators.Hidden(),
            ),
        )

    async def client_ready(self):
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self.tg_id,
                photo="https://raw.githubusercontent.com/gerdaroot/Kage/master/assets/img/setup.png",
                caption=self.strings["period"],
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {
                                "text": f"🕰 {i} h",
                                "callback": self._set_backup_period,
                                "args": (i,),
                            }
                            for i in [1, 2, 4, 6, 8, 12, 24, 48, 168]
                        ],
                        3,
                    )
                    + [
                        [
                            {
                                "text": "🚫 Never",
                                "callback": self._set_backup_period,
                                "args": (0,),
                            }
                        ]
                    ]
                ),
            )

        self._content_channel_id = await utils.wait_for_content_channel(self._db)

    async def _set_backup_period(self, call: BotInlineCall, value: int):
        if not value:
            self.set("period", "disabled")
            await self.inline.bot(
                call.answer(
                    self.strings["never_bot"].format(prefix=self.get_prefix()),
                    show_alert=True,
                )
            )
            await call.delete()
            return

        self.set("period", value * 60 * 60)
        self.set("last_backup", round(time.time()))

        await self.inline.bot(
            call.answer(
                self.strings["saved_bot"].format(prefix=self.get_prefix()),
                show_alert=True,
            )
        )
        await call.delete()

    @loader.command()
    async def set_backup_period(self, message: Message):
        """[time] | set your backup bd period"""
        if (
            not (args := utils.get_args_raw(message))
            or not args.isdigit()
            or int(args) not in range(200)
        ):
            await utils.answer(message, self.strings["invalid_args"])
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(
                message,
                f"<b>{self.strings['never'].format(prefix=self.get_prefix())}</b>",
            )
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(
            message, f"<b>{self.strings['saved'].format(prefix=self.get_prefix())}</b>"
        )

    @staticmethod
    def _dump_json(obj) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS)

    @staticmethod
    def _timestamp() -> str:
        return f"{datetime.datetime.now():%d-%m-%Y-%H-%M}"

    def _build_mods_zip(self) -> tuple[bytes, int]:
        buffer = io.BytesIO()
        files_count = 0
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(loader.LOADED_MODULES_DIR):
                for file in files:
                    if file.endswith(f"{self.tg_id}.py"):
                        with open(os.path.join(root, file), "rb") as f:
                            zipf.writestr(file, f.read())
                        files_count += 1

            zipf.writestr(
                "db_mods.json",
                self._dump_json(self.lookup("LoaderMod").get("loaded_modules", {})),
            )

        return buffer.getvalue(), files_count

    def _build_full_archive(self) -> bytes:
        mods, _ = self._build_mods_zip()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("db.json", self._dump_json(self._db))
            z.writestr("mods.zip", mods)

        return archive.getvalue()

    @property
    def _backup_password(self) -> str:
        return self.config["backup_password"] or ""

    async def _seal_backup(self, data: bytes, name: str) -> io.BytesIO:
        if password := self._backup_password:
            data = await asyncio.to_thread(encrypt_backup, data, password)
            name += ENCRYPTED_SUFFIX

        file = io.BytesIO(data)
        file.name = name
        return file

    async def _open_backup(self, data: bytes) -> bytes:
        if not is_encrypted_backup(data):
            return data

        return await asyncio.to_thread(decrypt_backup, data, self._backup_password)

    def _caption(self, text: str) -> str:
        note = "encrypted_note" if self._backup_password else "password_hint"
        prefix = utils.escape_html(self.get_prefix())
        return f"{text}\n\n{self.strings[note].format(prefix=prefix)}"

    def _crypto_error_text(self, error: BackupCryptoError) -> str:
        return self.strings[error.string_key].format(
            prefix=utils.escape_html(self.get_prefix())
        )

    def _restore_markup(self):
        return self.inline.generate_markup(
            [[{"text": "↪️ Restore this", "data": RESTORE_CALLBACK_CONFIRM}]]
        )

    @loader.loop(interval=1, autostart=True)
    async def handler(self):
        try:
            if self.get("period") == "disabled":
                raise loader.StopLoop

            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            archive = await self._seal_backup(
                self._build_full_archive(), f"backup-{self._timestamp()}.backup"
            )

            backup_topic_id = await utils.get_topic_id(self._db, "Backups")
            if not backup_topic_id:
                logger.error("Backups topic not found in database")
                return

            await self.inline.bot.send_document(
                int(f"-100{self._content_channel_id}"),
                archive,
                caption=self._caption(
                    self.strings["backupall_info"].format(
                        prefix=utils.escape_html(self.get_prefix())
                    )
                ),
                reply_markup=self._restore_markup(),
                message_thread_id=backup_topic_id,
            )

            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("KageBackup failed")
            await asyncio.sleep(60)

    @staticmethod
    def _read_full_archive(archive: bytes) -> tuple[dict, object, dict[str, bytes]]:
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            db_data = orjson.loads(migrate_legacy_db(zf.read("db.json").decode()))
            mods_zip = zf.read("mods.zip")

        with zipfile.ZipFile(io.BytesIO(mods_zip)) as modzip:
            db_mods = orjson.loads(modzip.read("db_mods.json"))
            modules = {
                Path(name).name: modzip.read(name)
                for name in modzip.namelist()
                if name != "db_mods.json" and Path(name).name.endswith(".py")
            }

        return db_data, db_mods, modules

    def _restore_full_archive(self, archive: bytes):
        # Everything is parsed before the first write, so a broken archive
        # can't leave the database restored without its modules.
        db_data, db_mods, modules = self._read_full_archive(archive)

        with contextlib.suppress(KeyError):
            db_data["kage.inline"].pop("bot_token")

        if not self._db.process_db_autofix(db_data):
            raise RuntimeError("Attempted to restore broken database")

        self._db.clear()
        self._db.update(**db_data)
        self._db.save()

        if isinstance(db_mods, dict):
            self.lookup("LoaderMod").set("loaded_modules", db_mods)

        for name, source in modules.items():
            (loader.LOADED_MODULES_PATH / name).write_bytes(source)

    @loader.callback_handler()
    async def restore(self, call: BotInlineCall):
        if not call.data.startswith(RESTORE_CALLBACK):
            return

        if call.data == RESTORE_CALLBACK_CONFIRM:
            await utils.answer(
                call,
                "❓ <b>Are you sure?</b>",
                reply_markup={"text": "✅ Yes", "data": RESTORE_CALLBACK},
            )
            return

        try:
            file = await (
                await self._client.get_messages(
                    self._content_channel_id, ids=[call.message.message_id]
                )
            )[0].download_media(bytes)

            self._restore_full_archive(await self._open_backup(file))
        except BackupCryptoError as e:
            await self.inline.bot(
                call.answer(
                    utils.remove_html(self._crypto_error_text(e)), show_alert=True
                )
            )
            return
        except Exception:
            logger.exception("Restore from backupall failed")
            await self.inline.bot(
                call.answer(self.strings["reply_to_file"], show_alert=True)
            )
            return

        await self.inline.bot(
            call.answer(self.strings["all_restored_bot"], show_alert=True)
        )
        await self.invoke("restart", "-f", peer=call.message.chat.id)

    @staticmethod
    def _message_id(message) -> int:
        return getattr(message, "message_id", getattr(message, "id"))

    async def convert(self, call: BotInlineCall, ans, file):
        match ans:
            case "y":
                await utils.answer(call, self.strings["converting_db"])
                backup = await self._seal_backup(
                    migrate_legacy_db(file).encode(),
                    f"db-converted-{self._timestamp()}.json",
                )
                await utils.answer_file(
                    call,
                    backup,
                    caption=self._caption(
                        self.strings["backup_caption"].format(
                            prefix=utils.escape_html(self.get_prefix())
                        )
                    ),
                )
            case _:
                await utils.answer(
                    call,
                    self.strings["advice_converting"],
                    reply_markup=[[{"text": "🔻 Close", "action": "close"}]],
                )

    @loader.command()
    async def backupdb(self, message: Message):
        try:
            txt = await self._seal_backup(
                self._dump_json(self._db), f"db-backup-{self._timestamp()}.json"
            )
        except BackupCryptoError as e:
            await utils.answer(message, self._crypto_error_text(e))
            return

        if not getattr(self, "_content_channel_id", None):
            self._content_channel_id = await utils.wait_for_content_channel(self._db)

        backup_topic_id = await utils.get_topic_id(self._db, "Backups")
        if not backup_topic_id:
            logger.error("Backups topic not found in database")
            await utils.answer(message, self.strings["backup_sent"])
            return

        backup_msg = await self.inline.bot.send_document(
            int(f"-100{self._content_channel_id}"),
            txt,
            caption=self._caption(
                self.strings["backup_caption"].format(
                    prefix=utils.escape_html(self.get_prefix())
                )
            ),
            message_thread_id=backup_topic_id,
        )

        await utils.answer(
            message,
            self.strings["backup_sent"].format(
                f"https://t.me/c/{self._content_channel_id}/{backup_topic_id}/{self._message_id(backup_msg)}"
            ),
        )

    @loader.command()
    async def restoredb(self, message: Message):
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(
                message,
                self.strings["reply_to_file"],
            )
            return

        try:
            file = await self._open_backup(await reply.download_media(bytes))
        except BackupCryptoError as e:
            await utils.answer(message, self._crypto_error_text(e))
            return

        try:
            decoded_text = orjson.loads(migrate_legacy_db(file.decode()))

        except UnicodeDecodeError:
            await utils.answer(
                message, self.strings["probably_zip"].format(self.get_prefix())
            )
            return
        if re.search(r'"(hikka\.)(\S+\":)', file.decode()):
            await utils.answer(
                message,
                self.strings["db_warning"],
                reply_markup=[
                    {
                        "text": "❌",
                        "callback": self.convert,
                        "args": (
                            "n",
                            file.decode(),
                        ),
                    },
                    {
                        "text": "✅",
                        "callback": self.convert,
                        "args": (
                            "y",
                            file.decode(),
                        ),
                    },
                ],
            )
            return

        with contextlib.suppress(KeyError):
            decoded_text["kage.inline"].pop("bot_token")

        if not self._db.process_db_autofix(decoded_text):
            raise RuntimeError("Attempted to restore broken database")

        self._db.clear()
        self._db.update(**decoded_text)
        self._db.save()

        await utils.answer(message, self.strings["db_restored"])
        await self.invoke("restart", "-f", peer=message.peer_id)

    @loader.command()
    async def backupmods(self, message: Message):
        mods_quantity = len(self.lookup("LoaderMod").get("loaded_modules", {}))
        mods, files_count = self._build_mods_zip()
        mods_quantity += files_count

        try:
            archive = await self._seal_backup(mods, f"mods-{self._timestamp()}.zip")
        except BackupCryptoError as e:
            await utils.answer(message, self._crypto_error_text(e))
            return

        caption = self._caption(
            self.strings["modules_backup"].format(
                mods_quantity,
                utils.escape_html(self.get_prefix()),
            )
        )

        if not getattr(self, "_content_channel_id", None):
            self._content_channel_id = await utils.wait_for_content_channel(self._db)

        backup_topic_id = await utils.get_topic_id(self._db, "Backups")
        if not backup_topic_id:
            logger.error("Backups topic not found in database")
            await utils.answer_file(message, archive, caption=caption)
            return

        backup_msg = await self.inline.bot.send_document(
            int(f"-100{self._content_channel_id}"),
            archive,
            caption=caption,
            message_thread_id=backup_topic_id,
        )

        await utils.answer(
            message,
            self.strings["backup_sent"].format(
                f"https://t.me/c/{self._content_channel_id}/{backup_topic_id}/{self._message_id(backup_msg)}"
            ),
        )

    @loader.command()
    async def restoremods(self, message: Message):
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(message, self.strings["reply_to_file"])
            return

        try:
            file = await self._open_backup(await reply.download_media(bytes))
        except BackupCryptoError as e:
            await utils.answer(message, self._crypto_error_text(e))
            return

        try:
            decoded_text = orjson.loads(file.decode())
        except Exception:
            try:
                file = io.BytesIO(file)
                file.name = "mods.zip"

                with zipfile.ZipFile(file) as zf:
                    with zf.open("db_mods.json", "r") as modules:
                        db_mods = orjson.loads(modules.read().decode())
                        if isinstance(db_mods, dict) and all(
                            (
                                isinstance(key, str)
                                and isinstance(value, str)
                                and utils.check_url(value)
                            )
                            for key, value in db_mods.items()
                        ):
                            self.lookup("LoaderMod").set("loaded_modules", db_mods)

                    for name in zf.namelist():
                        if name == "db_mods.json" or not Path(name).name.endswith(
                            ".py"
                        ):
                            continue

                        path = loader.LOADED_MODULES_PATH / Path(name).name
                        with zf.open(name, "r") as module:
                            path.write_bytes(module.read())
            except Exception:
                logger.exception("Unable to restore modules")
                await utils.answer(message, self.strings["reply_to_file"])
                return
        else:
            if not isinstance(decoded_text, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in decoded_text.items()
            ):
                raise RuntimeError("Invalid backup")

            self.lookup("LoaderMod").set("loaded_modules", decoded_text)

        await utils.answer(message, self.strings["mods_restored"])
        await self.invoke("restart", "-f", peer=message.peer_id)

    @loader.command()
    async def backupall(self, message: Message):
        try:
            archive = await self._seal_backup(
                self._build_full_archive(), f"kage-{self._timestamp()}.backup"
            )
        except BackupCryptoError as e:
            await utils.answer(message, self._crypto_error_text(e))
            return

        backup_topic_id = await utils.get_topic_id(self._db, "Backups")
        if not backup_topic_id:
            logger.error("Backups topic not found in database")
            await utils.answer(
                message,
                "<b>Backups topic not found in database. Please run quickstart to create it.</b>",
            )
            return

        backup_msg = await self.inline.bot.send_document(
            int(f"-100{self._content_channel_id}"),
            archive,
            caption=self._caption(
                self.strings["backupall_info"].format(
                    prefix=utils.escape_html(self.get_prefix()),
                )
            ),
            reply_markup=self._restore_markup(),
            message_thread_id=backup_topic_id,
        )

        await utils.answer(
            message,
            self.strings["backupall_sent"].format(
                f"https://t.me/c/{self._content_channel_id}/{backup_topic_id}/{self._message_id(backup_msg)}"
            ),
        )

    @loader.command()
    async def restoreall(self, message: Message):
        if not (reply := await message.get_reply_message()) or not reply.media:
            await utils.answer(message, self.strings["reply_to_file"])
            return

        status_message = await utils.answer(message, self.strings["restoring_backup"])
        try:
            file = await self._open_backup(await reply.download_media(bytes))
            self._restore_full_archive(file)
        except BackupCryptoError as e:
            await utils.answer(status_message, self._crypto_error_text(e))
            return
        except Exception:
            logger.exception("Restore all failed")
            await utils.answer(status_message, self.strings["reply_to_file"])
            return

        await utils.answer(status_message, self.strings["all_restored"])
        await self.invoke("restart", "-f", peer=message.peer_id)
