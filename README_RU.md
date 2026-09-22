<div align="center">
  <img src="assets/img/info.png" alt="Kage" width="720">
  <h1>🖤 Kage</h1>
  <p><b>影 — «тень».</b> Модульный юзербот для Telegram, который тихо работает на твоём аккаунте.</p>
  <p>
    <img src="https://img.shields.io/github/license/gerdaroot/Kage" alt="License">
    <img src="https://img.shields.io/github/stars/gerdaroot/Kage" alt="Stars">
    <a href="README.md"><img src="https://img.shields.io/badge/lang-en-red.svg" alt="English"></a>
  </p>
</div>

---

Kage — форк [Heroku](https://github.com/coddrago/Heroku), который в свою очередь вырос из [Hikka](https://github.com/hikariatama/Hikka).
**Модули от Hikka и Heroku работают без изменений**: импорты `hikka`, `heroku`, `hikkatl`, `telethon`
перенаправляются на Kage, а `client.heroku_me` / `heroku_db` и `# scope: heroku_min` по-прежнему понимаются.

## ✨ Чем Kage отличается от Heroku

- 🖤 Своё оформление: баннеры, логотип, премиум-эмодзи, картинки лежат прямо в репозитории
  (у Heroku они грузились из стороннего репозитория, который уже удалён).
- 🔒 Меньше удалённого контроля со стороны авторов апстрима:
  - обновления и объявления приходят только из этого репозитория;
  - при первом запуске не предлагается вступить в сторонние чаты;
  - из папки «Kage» убраны зашитые ID чужих чатов;
  - из наборов модулей убраны `DoxTool` и `hardspam`.
- 🐳 Нормальный Docker: код в образе, сессия и данные в отдельном томе, запуск **не от root**,
  готовый образ `ghcr.io/gerdaroot/kage` для amd64 и arm64.

## 🚀 Установка

### Docker (рекомендуется)

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage
docker compose run --rm kage     # первый запуск: API ID/hash и вход по QR или номеру
docker compose up -d             # дальше работает в фоне
docker compose logs -f           # логи
```

Одной командой (поставит Docker, если его нет):

```bash
curl -fsSL https://raw.githubusercontent.com/gerdaroot/Kage/master/docker.sh | bash
```

Обновление: `docker compose pull && docker compose up -d`. Сессия и модули хранятся в томе `kage-data` и не теряются.

### Без Docker (VPS / Linux / macOS)

```bash
git clone https://github.com/gerdaroot/Kage && cd Kage
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m kage
```

`API_ID` и `API_HASH` берутся на https://my.telegram.org → API development tools.

## 🧩 Модули

```
.dlm <ссылка>      загрузить модуль по ссылке
.lm                (ответом на .py-файл) загрузить модуль из файла
.ulm <имя>         выгрузить модуль
.help              список модулей
```

Документация по написанию модулей у Heroku подходит и для Kage: https://dev.heroku-ub.xyz

> ⚠️ **Модуль — это код с полным доступом к твоему аккаунту.** Ставь модули только от тех, кому доверяешь,
> и читай код перед установкой. Модуль может украсть сессию, писать от твоего имени и удалить чаты.
> Включи облачный пароль (двухэтапную аутентификацию) и иногда проверяй «Настройки → Устройства».

## 📜 Лицензия и авторы

[GNU AGPLv3](LICENSE). Если ты даёшь пользоваться своей изменённой версией другим — открой её исходный код.

- © Dan Gazizullin ([hikariatama](https://github.com/hikariatama)) — Hikka, 2021–2023
- © [Codrago](https://github.com/coddrago) — Heroku, 2024+
- 🖤 [gerdaroot](https://github.com/gerdaroot) — Kage
