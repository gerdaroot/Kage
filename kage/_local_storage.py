"""Saves modules to disk and fetches them if remote storage is not available."""

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
import hashlib
import logging
import os

import requests

from . import utils
from .tl_cache import CustomTelegramClient
from .version import __version__

logger = logging.getLogger(__name__)

MAX_FILESIZE = 1024 * 1024 * 5  # 5 MB
MAX_TOTALSIZE = 1024 * 1024 * 100  # 100 MB


def source_sha256(source: str) -> str:
    """SHA-256 hex digest of a module's source code."""
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _matches_pin(source: str, expected_sha256: str | None) -> bool:
    return expected_sha256 is None or source_sha256(source) == expected_sha256


class LocalStorage:
    """Saves modules to disk and fetches them if remote storage is not available."""

    def __init__(self):
        # in Docker the home dir is wiped with the container; /data is the persistent volume
        root = "/data" if "DOCKER" in os.environ else os.path.expanduser("~")
        self._path = os.path.join(root, ".kage", "modules_cache")
        self._tracked_total_size: int | None = None
        self._ensure_dirs()

    @property
    def _total_size(self) -> int:
        if self._tracked_total_size is None:
            self._tracked_total_size = sum(
                entry.stat().st_size
                for entry in os.scandir(self._path)
                if entry.is_file()
            )

        return self._tracked_total_size

    def _ensure_dirs(self):
        """Ensures that the local storage directory exists."""
        if not os.path.isdir(self._path):
            os.makedirs(self._path)

    def _get_path(self, repo: str, module_name: str) -> str:
        return os.path.join(
            self._path,
            hashlib.sha256(f"{repo}_{module_name}".encode()).hexdigest() + ".py",
        )

    def save(self, repo: str, module_name: str, module_code: str):
        """
        Saves module to disk.
        :param repo: Repository name.
        :param module_name: Module name.
        :param module_code: Module source code.
        """
        size = len(module_code)
        if size > MAX_FILESIZE:
            logger.warning(
                "Module %s from %s is too large (%s bytes) to save to local cache.",
                module_name,
                repo,
                size,
            )
            return

        if self._total_size + size > MAX_TOTALSIZE:
            logger.warning(
                "Local storage is full, cannot save module %s from %s.",
                module_name,
                repo,
            )
            return

        path = self._get_path(repo, module_name)
        previous_size = os.path.getsize(path) if os.path.isfile(path) else 0

        # newline="" keeps the bytes as downloaded, otherwise CRLF sources change their hash
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(module_code)

        self._tracked_total_size = self._total_size + size - previous_size
        logger.debug("Saved module %s from %s to local cache.", module_name, repo)

    def fetch(self, repo: str, module_name: str) -> str | None:
        """
        Fetches module from disk.
        :param repo: Repository name.
        :param module_name: Module name.
        :return: Module source code or None.
        """
        path = self._get_path(repo, module_name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8", newline="") as f:
                return f.read()

        return None


class RemoteStorage:
    def __init__(self, client: CustomTelegramClient):
        self._local_storage = LocalStorage()
        self._client = client

    async def preload(self, urls: list[str], pinned: dict[str, str] | None = None):
        """
        Preloads modules from remote storage.
        :param urls: Module URLs to cache.
        :param pinned: URL -> pinned SHA-256; a changed remote copy won't replace the cached one.
        """
        logger.debug("Preloading modules from remote storage.")
        pinned = pinned or {}
        for url in urls:
            logger.debug("Preloading module %s", url)

            with contextlib.suppress(Exception):
                await self.fetch(url, expected_sha256=pinned.get(url))

            await asyncio.sleep(5)

    @staticmethod
    def _parse_url(url: str) -> tuple[str, str, str]:
        """
        Parses a URL into a repository and module name.
        :param url: URL to parse.
        :return: Tuple of (url, repo, module_name).
        """
        domain_name = url.split("/")[2]

        match domain_name:
            case "raw.githubusercontent.com":
                owner, repo, branch = url.split("/")[3:6]
                module_name = url.split("/")[-1].split(".")[0]
                repo = f"git+{owner}/{repo}:{branch}"
            case "github.com":
                owner, repo, _, branch = url.split("/")[3:7]
                module_name = url.split("/")[-1].split(".")[0]
                repo = f"git+{owner}/{repo}:{branch}"
            case _:
                repo, module_name = url.rsplit("/", maxsplit=1)
                repo = repo.strip("/")

        return url, repo, module_name

    async def fetch(
        self,
        url: str,
        auth: str | None = None,
        prefer_local: bool = False,
        expected_sha256: str | None = None,
    ) -> str:
        """
        Fetches the module from the remote storage.
        :param url: URL to the module.
        :param auth: Optional authentication string in the format "username:password".
        :param prefer_local: Use the cached copy when there is one (restarts), so a changed
            remote file can't silently run new code on the account
        :param expected_sha256: Pinned hash. A cached copy that doesn't match it is ignored,
            and a downloaded copy that doesn't match it is returned but never cached
        :return: Module source code.
        """
        url, repo, module_name = self._parse_url(url)
        cached = self._local_storage.fetch(repo, module_name)
        if cached is not None and not _matches_pin(cached, expected_sha256):
            logger.warning(
                "Cached copy of %s doesn't match its pinned hash, ignoring it", url
            )
            cached = None

        if prefer_local and cached:
            return cached

        try:
            r = await utils.run_sync(
                requests.get,
                url,
                auth=(tuple(auth.split(":", 1)) if auth else None),
            )
            r.raise_for_status()
        except Exception:
            logger.debug(
                "Can't load module from remote storage. Trying local storage.",
                exc_info=True,
            )
            if cached:
                logger.debug("Module source loaded from local storage.")
                return cached

            raise

        if _matches_pin(r.text, expected_sha256):
            self._local_storage.save(repo, module_name, r.text)

        return r.text

    def fetch_cached(self, url: str, expected_sha256: str | None = None) -> str | None:
        """
        Returns the cached copy of the module without network access.
        :param url: URL to the module.
        :param expected_sha256: If set, a cached copy with another hash is treated as missing.
        :return: Module source code or None.
        """
        _, repo, module_name = self._parse_url(url)
        cached = self._local_storage.fetch(repo, module_name)
        return cached if cached and _matches_pin(cached, expected_sha256) else None

    def store(self, url: str, source: str):
        """Caches a module source the owner has approved."""
        _, repo, module_name = self._parse_url(url)
        self._local_storage.save(repo, module_name, source)
