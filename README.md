<div align="center">
  <img src="assets/img/info.png" alt="Kage" width="720">
  <h1>🖤 Kage</h1>
  <p><b>影 — "shadow".</b> A modular Telegram userbot that quietly works on your account.</p>
  <p>
    <img src="https://img.shields.io/github/license/gerdaroot/Kage" alt="License">
    <img src="https://img.shields.io/github/stars/gerdaroot/Kage" alt="Stars">
    <a href="README_RU.md"><img src="https://img.shields.io/badge/lang-ru-green.svg" alt="Русский"></a>
  </p>
</div>

---

Kage is a fork of [Heroku](https://github.com/coddrago/Heroku), which itself grew out of [Hikka](https://github.com/hikariatama/Hikka).
**Hikka and Heroku modules work unchanged**: `hikka`, `heroku`, `hikkatl` and `telethon` imports are redirected to Kage,
and `client.heroku_me` / `heroku_db` and `# scope: heroku_min` are still understood.

## ✨ How Kage differs from Heroku

- 🖤 Its own look: banners, logo and premium emoji. The images live in this repository;
  Heroku loaded them from a third-party repo that has since been deleted.
- 🔒 Upstream authors have less remote control:
  - updates and announcements come only from this repository;
  - first start doesn't ask you to join third-party chats;
  - hardcoded third-party chat IDs are removed from the "Kage" folder;
  - `DoxTool` and `hardspam` are dropped from module presets.
- 🐳 A sane Docker setup:
  - code ships in the image; your session and data live in a separate volume;
  - the bot runs as a **non-root** user;
  - a prebuilt image `ghcr.io/gerdaroot/kage` is available for amd64 and arm64.

## 🚀 Install

### Docker (recommended)

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage
docker compose run --rm kage     # first run: API ID/hash, then log in by QR code or phone
docker compose up -d             # keep it running in the background
docker compose logs -f           # logs
```

One-liner (installs Docker if missing):

```bash
curl -fsSL https://raw.githubusercontent.com/gerdaroot/Kage/master/docker.sh | bash
```

To update, run `docker compose pull && docker compose up -d`. Your session and modules stay in the `kage-data` volume.

### Without Docker (VPS / Linux / macOS)

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m kage
```

Get `API_ID` and `API_HASH` at https://my.telegram.org → API development tools.

## 🧩 Modules

```
.dlm <link>        load a module from a link
.lm                (reply to a .py file) load a module from the file
.ulm <name>        unload a module
.help              list modules
```

Heroku's module developer docs apply to Kage as well: https://dev.heroku-ub.xyz

> ⚠️ **A module is code with full access to your account.** Only install modules from people you trust, and read
> the code first. A module can steal your session, send messages as you or delete chats.
> Turn on a cloud password (2FA) and check Settings → Devices now and then.

## 📜 License and credits

[GNU AGPLv3](LICENSE). If you let others use your modified version, you must publish its source.

- © Dan Gazizullin ([hikariatama](https://github.com/hikariatama)) — Hikka, 2021–2023
- © [Codrago](https://github.com/coddrago) — Heroku, 2024+
- 🖤 [gerdaroot](https://github.com/gerdaroot) — Kage
