<div align="center">
  <img src="assets/img/avatar.png" height="120" alt="Kage">
  <h1>🖤 Kage Userbot</h1>
  <p><b>影 — «тень».</b> Модульный юзербот для Telegram, который тихо работает на твоём аккаунте</p>

  <p>
    <a href="#">
      <img src="https://img.shields.io/github/languages/code-size/gerdaroot/Kage" alt="Code Size">
    </a>
    <a href="#">
      <img src="https://img.shields.io/github/issues-raw/gerdaroot/Kage" alt="Open Issues">
    </a>
    <a href="#">
      <img src="https://img.shields.io/github/license/gerdaroot/Kage" alt="License">
    </a>
    <a href="#">
      <img src="https://img.shields.io/github/commit-activity/m/gerdaroot/Kage" alt="Commit Activity">
    </a>
    <br>
    <a href="#">
      <img src="https://img.shields.io/github/forks/gerdaroot/Kage?style=flat" alt="Forks">
    </a>
    <a href="#">
      <img src="https://img.shields.io/github/stars/gerdaroot/Kage" alt="Stars">
    </a>
    <a href="https://github.com/gerdaroot/Kage/pkgs/container/kage">
      <img src="https://img.shields.io/badge/docker-ghcr.io%2Fgerdaroot%2Fkage-8c4dff?logo=docker&logoColor=white" alt="Docker">
    </a>
    <br>
    <a href="https://github.com/gerdaroot/Kage/blob/master/README.md">
      <img src="https://img.shields.io/badge/lang-en-red.svg" alt="En">
    </a>
    <a href="https://github.com/gerdaroot/Kage/blob/master/README_RU.md">
      <img src="https://img.shields.io/badge/lang-ru-green.svg" alt="Ru">
    </a>
  </p>

  <img src="assets/img/started.png" width="640" alt="Kage запущен">
</div>

---

## ⚠️ Уведомление о безопасности

> **Важное предупреждение**
> Модуль — это Python-код с полным доступом к твоему аккаунту. Модуль от ненадёжного разработчика может
> украсть сессию, писать от твоего имени или удалить чаты.
>
> **Рекомендации:**
> - ✅ Ставь модули только из репозиториев и от разработчиков, которым доверяешь, и читай код перед установкой
> - ❌ НЕ устанавливай модули, если не уверен в их безопасности
> - ⚠️ Осторожно с мощными командами (`.terminal`, `.e`, `.ecpp` и т.д.)
> - 🔐 Включи облачный пароль Telegram и иногда проверяй «Настройки → Устройства»

---

## 🚀 Установка

### 🐳 Docker (рекомендуется)

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage
docker compose run --rm kage     # первый запуск: API ID/hash и вход по QR или номеру
docker compose up -d             # дальше работает в фоне
```

Или одной командой (поставит Docker, если его нет):

```bash
curl -fsSL https://raw.githubusercontent.com/gerdaroot/Kage/master/docker.sh | bash
```

Обновление: `docker compose pull && docker compose up -d`. Сессия и модули хранятся в томе `kage-data`.

> На одну сессию — **один** запущенный Kage: сначала закрой контейнер первого запуска (`Ctrl+C`), потом `docker compose up -d`.

### VPS/VDS
> **Примечание для VPS/VDS:**
> Если запускаешь от root, добавь `--root` (чтобы не вводить force_insecure).

<details>
<summary><b>Ubuntu / Debian</b></summary>

```bash
sudo apt update && sudo apt install git python3 python3-venv -y && \
git clone https://github.com/gerdaroot/Kage && \
cd Kage && \
python3 -m venv .venv && \
source .venv/bin/activate && \
pip install -r requirements.txt && \
python3 -m kage
```
</details>

<details>
<summary><b>Fedora</b></summary>

```bash
sudo dnf update -y && sudo dnf install git python3 -y && \
git clone https://github.com/gerdaroot/Kage && \
cd Kage && \
python3 -m venv .venv && \
source .venv/bin/activate && \
python3 -m pip install -r requirements.txt && \
python3 -m kage
```
</details>

<details>
<summary><b>Arch Linux</b></summary>

```bash
sudo pacman -Syu --noconfirm && sudo pacman -S git python --noconfirm --needed && \
git clone https://github.com/gerdaroot/Kage && \
cd Kage && \
python3 -m venv .venv && \
source .venv/bin/activate && \
python3 -m pip install -r requirements.txt && \
python3 -m kage
```
</details>

<details>
<summary><b>macOS</b></summary>

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage && \
python3 -m venv .venv && source .venv/bin/activate && \
pip install -r requirements.txt && python3 -m kage
```
</details>

### Другое

<details>
<summary><b>WSL (Windows)</b></summary>

> **⚠️ ВНИМАНИЕ: может работать нестабильно!**

1. **Установи WSL.** Открой PowerShell от администратора и выполни:
   ```powershell
   wsl --install -d Ubuntu-22.04
   ```
   > *Нужна Windows 10 build 2004+ или Windows 11 и ПК с поддержкой виртуализации.
   > Для более старых систем — [эта страница](https://learn.microsoft.com/ru-ru/windows/wsl/install-manual).*
2. **Перезагрузи ПК и открой Ubuntu 22.04.**
3. **Выполни:**
   ```bash
   sudo apt update && sudo apt install git python3 python3-venv -y && \
   git clone https://github.com/gerdaroot/Kage && cd Kage && \
   python3 -m venv .venv && source .venv/bin/activate && \
   pip install -r requirements.txt && python3 -m kage
   ```
</details>

<details>
<summary><b>Телефон (UserLAnd)</b></summary>

1. Установи <a href="https://play.google.com/store/apps/details?id=tech.ula">UserLAnd</a>.
2. Открой его и выбери **Ubuntu → Minimal → Terminal**.
3. Жди установки дистрибутива, можешь налить чаю.
4. В терминале выполни:
   ```bash
   sudo apt update && sudo apt upgrade -y && sudo apt install python3 git python3-pip python3-venv -y && \
   git clone https://github.com/gerdaroot/Kage && cd Kage && \
   python3 -m venv .venv && source .venv/bin/activate && \
   pip install -r requirements.txt && python3 -m kage
   ```
5. Следуй подсказкам: введи данные API и войди в аккаунт.

> **Вуаля! Kage работает на телефоне.**
</details>

> **🔗 Где взять API_ID и API_HASH?** [my.telegram.org](https://my.telegram.org/apps) → API development tools

---

## 🖤 Чем Kage отличается

| Особенность | Описание |
|-------------|----------|
| 🖤 **Своё оформление** | Логотип Kage, анимированное премиум-сердце, баннер в терминале, баннеры и аватарки лежат прямо в репозитории |
| 🕶 **Честный клиент** | Представляется Telegram как `Kage Userbot` с настоящей ОС, одинаково при каждом запуске. Никаких случайных устройств и маскировки под официальные приложения |
| 🔒 **Без удалённого контроля апстрима** | Обновления и объявления приходят только из этого репозитория. Никаких принудительных вступлений в чужие чаты и зашитых чужих ID |
| 🐳 **Нормальный Docker** | Код в образе, сессия и данные в томе. Запуск не от root. Готовый `ghcr.io/gerdaroot/kage` для amd64 и arm64 |
| 🧹 **Чище наборы модулей** | Из стандартных наборов убраны модули для деанона и спама |
| 🛟 **Надёжнее первый запуск** | Недоступная аватарка больше не роняет запуск; удалённый канал логов создаётся заново |

## ✨ Унаследовано от Hikka и Heroku

| Возможность | Описание |
|-------------|----------|
| 🔄 **Совместимость модулей** | Работают модули Hikka, Heroku, FTG и GeekTG. Импорты `hikka`/`heroku`/`telethon`/`hikkatl` перенаправляются автоматически |
| 🆕 **Свежий слой Telegram** | Форумы и новейшие функции Telegram |
| 🔒 **Правила безопасности** | Владельцы, группы безопасности, точечные правила для пользователей и чатов, защита от флуда API |
| ▶️ **Инлайн-элементы** | Формы, галереи и списки через твоего инлайн-бота |
| 💾 **Бэкапы** | Автоматические бэкапы базы и модулей в канал логов |
| 🌍 **Языки** | Русский, English, Українська, Deutsch, 日本語 и другие |

<details>
  <summary><b>🖼 Скриншоты</b></summary>
  <img src="assets/img/info.png" width="400">
  <img src="assets/img/ping.png" width="400">
  <img src="assets/img/updated.png" width="400">
  <img src="assets/img/installation.png" width="400">
</details>

---

## 🧩 Модули

```
.help               список модулей
.help <модуль>      команды модуля
.dlm <ссылка>       загрузить модуль по ссылке
.lm                 загрузить модуль из .py-файла (ответом на него)
.ulm <имя>          выгрузить модуль
```

Документация для разработчиков Heroku подходит для модулей Kage без изменений: [dev.heroku-ub.xyz](https://dev.heroku-ub.xyz/)

---

## 📋 Требования

- **Python 3.10+** (в Docker-образе 3.13)
- **Данные API** с [Telegram Apps](https://my.telegram.org/apps)

---

## 💬 Поддержка

[![GitHub Issues](https://img.shields.io/badge/GitHub-Issues-8c4dff?logo=github)](https://github.com/gerdaroot/Kage/issues)

---

## ⚠️ Отказ от ответственности

> Проект предоставляется как есть. Разработчик **НЕ несёт ответственности** за:
> - Баны и ограничения аккаунта
> - Удаление сообщений Telegram
> - Проблемы безопасности из-за скам-модулей
> - Утечки сессии через вредоносные модули
>
> **Рекомендации:**
> - Включи `.api_fw_protection`
> - Не ставь много модулей за раз
> - Ознакомься с [правилами Telegram](https://core.telegram.org/api/terms)

---

## 🙏 Благодарности

- [**Hikari**](https://github.com/hikariatama) — Hikka (основа проекта)
- [**Codrago**](https://github.com/coddrago) — Heroku (форк, на котором основан Kage)
- [**Lonami**](https://github.com/LonamiWebs) — Telethon (основа Heroku-TL)

Лицензия [GNU AGPLv3](LICENSE). Если даёшь пользоваться своей изменённой версией другим — открой её исходный код.
