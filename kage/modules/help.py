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

import difflib
import inspect
import logging
import re

import herokutl.extensions.html
from herokutl.tl.types import Message
from herokutl.types import InputMediaWebPage


from .. import loader, utils

logger = logging.getLogger(__name__)

CORE_CATEGORIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cat_modules", ("LoaderMod", "Presets", "LoaderRestrictor")),
    ("cat_security", ("KageSecurityMod", "APIRatelimiterMod")),
    ("cat_settings", ("KageSettingsMod", "CoreMod", "KageConfigMod", "InlineStuff")),
    ("cat_backups", ("KageBackupMod",)),
    ("cat_updates", ("UpdaterMod",)),
    ("cat_info", ("KageInfoMod", "TestMod", "Help", "Quickstart")),
    ("cat_accounts", ("KageWebMod",)),
    ("cat_dev", ("Evaluator", "TerminalMod")),
    ("cat_lang", ("Translations", "Translator")),
)
CORE_CATEGORY_BY_CLASS = {
    class_name: category
    for category, class_names in CORE_CATEGORIES
    for class_name in class_names
}
CORE_MODULE_RANK = {
    class_name: rank for rank, class_name in enumerate(CORE_CATEGORY_BY_CLASS)
}
OTHER_CORE_CATEGORY = "cat_other"
INSTALLED_CATEGORY = "cat_installed"
CATEGORY_ORDER = (
    *(category for category, _ in CORE_CATEGORIES),
    OTHER_CORE_CATEGORY,
    INSTALLED_CATEGORY,
)

MESSAGE_LIMIT = 4096
# descriptions are shortened step by step until the list fits into one message
DESC_LENGTHS = (80, 50, 40, 32, 28, 24, 20)
# Matches "<args> [opts] | description" and "[args] - description" docstrings
DOC_ARGS_RE = re.compile(r"^((?:[<\[(][^>\])]*[>\])]\s*)*)[|\-—–]\s*(.*)$")

CommandInfo = tuple[str, str, str]
ModuleCommands = tuple[str, list[CommandInfo]]


@loader.tds
class Help(loader.Module):
    """Shows help for modules and commands"""

    strings = {
        "name": "Help",
        "cmds_header": "<b>Kage — commands</b> (prefix «{}»)",
        "cat_modules": "📦 Modules",
        "cat_security": "🛡 Security & owners",
        "cat_settings": "⚙️ Settings & aliases",
        "cat_backups": "💾 Backups",
        "cat_updates": "🔄 Updates",
        "cat_info": "ℹ️ Info & diagnostics",
        "cat_accounts": "👥 Accounts",
        "cat_dev": "🧑‍💻 Developer tools",
        "cat_lang": "🌐 Translation & langpacks",
        "cat_other": "🗂 Other built-in",
        "cat_installed": "🧩 Installed modules",
        "hidden_note": "👁‍🗨 <i>Hidden modules: {}</i>",
        "compact_note": (
            "✂️ <i>Too many commands for one message, showing names only."
            " Details: </i><code>{}help &lt;module&gt;</code>"
        ),
        "truncated": "… +{} more",
        "only_permitted": "<i>You have permissions to execute only these commands</i>",
    }

    strings_ru = {
        "cmds_header": "<b>Kage — команды</b> (префикс «{}»)",
        "cat_modules": "📦 Модули",
        "cat_security": "🛡 Безопасность и владельцы",
        "cat_settings": "⚙️ Настройки и алиасы",
        "cat_backups": "💾 Бэкапы",
        "cat_updates": "🔄 Обновления",
        "cat_info": "ℹ️ Информация и диагностика",
        "cat_accounts": "👥 Аккаунты",
        "cat_dev": "🧑‍💻 Инструменты разработчика",
        "cat_lang": "🌐 Перевод и языки",
        "cat_other": "🗂 Прочие встроенные",
        "cat_installed": "🧩 Установленные модули",
        "hidden_note": "👁‍🗨 <i>Скрыто модулей: {}</i>",
        "compact_note": (
            "✂️ <i>Команд слишком много для одного сообщения, показаны только"
            " названия. Подробнее: </i><code>{}help &lt;модуль&gt;</code>"
        ),
        "truncated": "… и ещё {}",
        "only_permitted": "<i>Вам доступны только эти команды</i>",
    }

    strings_ua = {
        "cmds_header": "<b>Kage — команди</b> (префікс «{}»)",
        "cat_modules": "📦 Модулі",
        "cat_security": "🛡 Безпека та власники",
        "cat_settings": "⚙️ Налаштування та аліаси",
        "cat_backups": "💾 Бекапи",
        "cat_updates": "🔄 Оновлення",
        "cat_info": "ℹ️ Інформація та діагностика",
        "cat_accounts": "👥 Акаунти",
        "cat_dev": "🧑‍💻 Інструменти розробника",
        "cat_lang": "🌐 Переклад і мови",
        "cat_other": "🗂 Інші вбудовані",
        "cat_installed": "🧩 Встановлені модулі",
        "hidden_note": "👁‍🗨 <i>Приховано модулів: {}</i>",
        "compact_note": (
            "✂️ <i>Команд забагато для одного повідомлення, показано лише"
            " назви. Докладніше: </i><code>{}help &lt;модуль&gt;</code>"
        ),
        "truncated": "… і ще {}",
        "only_permitted": "<i>Вам доступні лише ці команди</i>",
    }

    strings_de = {
        "cmds_header": "<b>Kage — Befehle</b> (Präfix «{}»)",
        "cat_modules": "📦 Module",
        "cat_security": "🛡 Sicherheit & Besitzer",
        "cat_settings": "⚙️ Einstellungen & Aliase",
        "cat_backups": "💾 Backups",
        "cat_updates": "🔄 Updates",
        "cat_info": "ℹ️ Info & Diagnose",
        "cat_accounts": "👥 Konten",
        "cat_dev": "🧑‍💻 Entwicklerwerkzeuge",
        "cat_lang": "🌐 Übersetzung & Sprachen",
        "cat_other": "🗂 Weitere integrierte",
        "cat_installed": "🧩 Installierte Module",
        "hidden_note": "👁‍🗨 <i>Versteckte Module: {}</i>",
        "compact_note": (
            "✂️ <i>Zu viele Befehle für eine Nachricht, nur Namen werden"
            " angezeigt. Details: </i><code>{}help &lt;Modul&gt;</code>"
        ),
        "truncated": "… und {} weitere",
        "only_permitted": "<i>Sie dürfen nur diese Befehle ausführen</i>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "core_emoji",
                "<tg-emoji emoji-id=4974681956907221809>▪️</tg-emoji>",
                lambda: "Core module bullet",
            ),
            loader.ConfigValue(
                "plain_emoji",
                "<tg-emoji emoji-id=4974508259839836856>▪️</tg-emoji>",
                lambda: "Plain module bullet",
            ),
            loader.ConfigValue(
                "empty_emoji",
                "<tg-emoji emoji-id=5100652175172830068>🟠</tg-emoji>",
                lambda: "Empty modules bullet",
            ),
            loader.ConfigValue(
                "desc_icon",
                "<tg-emoji emoji-id=5449692618151695997>🖤</tg-emoji>",
                lambda: "Desc emoji",
            ),
            loader.ConfigValue(
                "command_emoji",
                "<tg-emoji emoji-id=5197195523794157505>▫️</tg-emoji>",
                lambda: "Emoji for command",
            ),
            loader.ConfigValue(
                "banner_url",
                None,
                lambda: "Banner for .help",
                validator=loader.validators.RandomLink(),
            ),
            loader.ConfigValue(
                "media_quote",
                "False",
                lambda: "quote a banner in help",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "invert_media",
                "False",
                lambda: "invert banner",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "show_preview_in_help",
                True,
                lambda: self.strings["show_preview_in_help"],
                validator=loader.validators.Boolean(),
            ),
        )

    def _get_banner_url(self, doc: str):
        match = re.search(r"# ?meta banner: ?(.+)", doc)
        return match.group(1).strip() if match else None

    @loader.command(
        ru_doc="[args] | Спрячет ваши модули",
        ua_doc="[args] | Сховає ваші модулі",
        de_doc="[args] | Versteckt Ihre Module",
    )
    async def helphide(self, message: Message):
        """[args] | hide your modules"""
        if not (modules := utils.get_args(message)):
            await utils.answer(message, self.strings["no_mod"])
            return

        currently_hidden = self.get("hide", [])
        hidden, shown = [], []
        for module in filter(lambda module: self.lookup(module), modules):
            module = self.lookup(module)
            module = module.__class__.__name__
            if module in currently_hidden:
                currently_hidden.remove(module)
                shown += [module]
            else:
                currently_hidden += [module]
                hidden += [module]

        self.set("hide", currently_hidden)

        await utils.answer(
            message,
            self.strings["hidden_shown"].format(
                len(hidden),
                len(shown),
                "\n".join([f"👁‍🗨 <i>{m}</i>" for m in hidden]),
                "\n".join([f"👁 <i>{m}</i>" for m in shown]),
            ),
        )

    def find_aliases(self, command: str) -> list:
        """Find aliases for command"""
        aliases = []
        _command = self.allmodules.commands[command]
        if getattr(_command, "alias", None) and not (
            aliases := getattr(_command, "aliases", None)
        ):
            aliases = [_command.alias]

        return aliases or []

    async def modhelp(self, message: Message, args: str):
        exact = True
        if not (module := self.lookup(args)):
            if method := self.allmodules.dispatch(
                args.lower().strip(self.get_prefix())
            )[1]:
                module = method.__self__
            else:
                module = self.lookup(
                    next(
                        (
                            reversed(
                                sorted(
                                    [
                                        module.strings["name"]
                                        for module in self.allmodules.modules
                                    ],
                                    key=lambda x: difflib.SequenceMatcher(
                                        None,
                                        args.lower(),
                                        x,
                                    ).ratio(),
                                )
                            )
                        ),
                        None,
                    )
                )

                exact = False

        try:
            name = module.strings("name")
        except (KeyError, AttributeError):
            name = getattr(module, "name", "ERROR")

        _name = (
            "{} (v{})".format(
                utils.escape_html(name), ".".join(map(str, module.__version__))
            )
            if hasattr(module, "__version__")
            else utils.escape_html(name)
        )

        reply = "{} <b>{}</b>:".format(
            "<tg-emoji emoji-id=5449692618151695997>🖤</tg-emoji>",
            _name,
        )
        inline_cmd = ""
        cmds = ""
        if module.__doc__:
            reply += (
                "\n<i><tg-emoji emoji-id=5879813604068298387>ℹ️</tg-emoji> "
                + utils.escape_html(inspect.getdoc(module))
                + "\n</i>"
            )

        if isinstance(self.lookup(args), loader.Library):
            return await utils.answer(message, self.strings["help_lib"].format(name))

        commands = {
            name: func
            for name, func in module.commands.items()
            if await self.allmodules.check_security(message, func)
        }

        if hasattr(module, "inline_handlers"):
            for name, fun in module.inline_handlers.items():
                inline_cmd += (
                    "\n<tg-emoji emoji-id=5372981976804366741>🤖</tg-emoji>"
                    " <code>{}</code> {}".format(
                        f"@{self.inline.bot_username} {name}",
                        (
                            utils.escape_html(inspect.getdoc(fun))
                            if fun.__doc__
                            else self.strings["undoc"]
                        ),
                    )
                )

        lines = []
        for name, fun in commands.items():
            lines.append(
                f'{self.config["command_emoji"]}'
                " <code>{}{}</code>{} {}".format(
                    utils.escape_html(self.get_prefix()),
                    name,
                    (
                        " ({})".format(
                            ", ".join(
                                "<code>{}{}</code>".format(
                                    utils.escape_html(self.get_prefix()),
                                    alias,
                                )
                                for alias in self.find_aliases(name)
                            )
                        )
                        if self.find_aliases(name)
                        else ""
                    ),
                    (
                        utils.escape_html(inspect.getdoc(fun))
                        if fun.__doc__
                        else self.strings["undoc"]
                    ),
                )
            )
        cmds = "\n".join(lines)
        developer = re.search(
            r"# ?meta developer: ?(.+)", getattr(module, "__source__", None)
        )
        dev_text = developer.group(1) if developer else None
        placeholders = "\n".join(
            utils.help_placeholders(module.__class__.__name__, self)
        )

        banner_kwargs = {}
        if self.config["show_preview_in_help"]:
            try:
                source = getattr(module, "__source__", None)
                if source:
                    banner_url = self._get_banner_url(source)
                    if banner_url:
                        banner_kwargs = {
                            "file": InputMediaWebPage(banner_url, optional=True),
                            "invert_media": True,
                        }
            except Exception:
                pass

        await utils.answer(
            message,
            f"{reply}<blockquote expandable>{cmds}{inline_cmd}</blockquote>"
            + (
                f"<blockquote expandable>\n{placeholders}</blockquote>"
                if placeholders
                else ""
            )
            + (f"\n\n{self.strings['developer']}".format(dev_text) if dev_text else "")
            + (f"\n\n{self.strings['not_exact']}" if not exact else "")
            + (
                f"\n{self.strings['core_notice']}"
                if module.__origin__.startswith("<core")
                else ""
            ),
            **banner_kwargs,
        )

    @staticmethod
    def _split_doc(doc: str | None) -> tuple[str, str]:
        first_line = next(iter((doc or "").strip().splitlines()), "").strip()
        if match := DOC_ARGS_RE.match(first_line):
            args, description = match.group(1).strip(), match.group(2).strip()
        else:
            args, description = "", first_line

        return args, description

    @staticmethod
    def _module_name(mod: loader.Module) -> str:
        try:
            return mod.strings["name"]
        except (KeyError, AttributeError):
            return getattr(mod, "name", "ERROR")

    @staticmethod
    def _category_of(mod: loader.Module) -> str:
        if not mod.__origin__.startswith("<core"):
            return INSTALLED_CATEGORY

        return CORE_CATEGORY_BY_CLASS.get(mod.__class__.__name__, OTHER_CORE_CATEGORY)

    def _module_sort_key(self, mod: loader.Module) -> tuple[int, str]:
        return (
            CORE_MODULE_RANK.get(mod.__class__.__name__, len(CORE_MODULE_RANK)),
            self._module_name(mod).lower(),
        )

    async def _collect_sections(
        self,
        message: Message,
        force: bool,
    ) -> tuple[dict[str, list[ModuleCommands]], bool]:
        hidden = self.get("hide", [])
        sections: dict[str, list[ModuleCommands]] = {}
        is_restricted = False

        for mod in sorted(self.allmodules.modules, key=self._module_sort_key):
            if not getattr(mod, "commands", None):
                continue

            if mod.__class__.__name__ in hidden and not force:
                continue

            commands = [
                (name, *self._split_doc(inspect.getdoc(func)))
                for name, func in mod.commands.items()
                if force or await self.allmodules.check_security(message, func)
            ]
            if not commands:
                is_restricted = True
                continue

            sections.setdefault(self._category_of(mod), []).append(
                (self._module_name(mod), commands)
            )

        return sections, is_restricted

    def _format_command(self, command: CommandInfo, desc_len: int) -> str:
        name, args, description = command
        if len(description) > desc_len:
            cut = description[: desc_len - 1]
            # cut at a word boundary unless that throws away most of the text
            if (space := cut.rfind(" ")) > desc_len // 2:
                cut = cut[:space]
            description = cut.rstrip(" ,.;:—-") + "…"

        line = utils.escape_html(f"{self.get_prefix()}{name}")
        if args and desc_len > DESC_LENGTHS[-1]:
            line += f" {utils.escape_html(args)}"
        if description:
            line += f" — {utils.escape_html(description)}"

        return line

    def _render_section(
        self,
        category: str,
        modules: list[ModuleCommands],
        desc_len: int | None,
    ) -> str:
        show_module_names = category == INSTALLED_CATEGORY
        lines = []
        for module_name, commands in modules:
            title = (
                f"<b>{utils.escape_html(module_name)}</b>" if show_module_names else ""
            )
            if desc_len:
                lines += [title] if title else []
                lines += [
                    self._format_command(command, desc_len) for command in commands
                ]
                continue

            names = " | ".join(
                utils.escape_html(f"{self.get_prefix()}{name}")
                for name, _, _ in commands
            )
            lines.append(f"{title}: {names}" if title else names)

        body = "\n".join(lines)
        return (
            f"<blockquote expandable><b>{self.strings[category]}</b>\n"
            f"{body}</blockquote>"
        )

    def _render_sections(
        self,
        sections: dict[str, list[ModuleCommands]],
        desc_len: int | None,
    ) -> str:
        return "".join(
            self._render_section(category, sections[category], desc_len)
            for category in CATEGORY_ORDER
            if sections.get(category)
        )

    @staticmethod
    def _fits_message(text: str) -> bool:
        plain_text, _ = herokutl.extensions.html.parse(text)
        # Telegram counts the limit in UTF-16 code units of the parsed text
        return len(plain_text.encode("utf-16-le")) // 2 <= MESSAGE_LIMIT

    def _help_footer(self, force: bool) -> str:
        notes = []
        hidden = self.get("hide", [])
        hidden_count = (
            0
            if force
            else sum(
                mod.__class__.__name__ in hidden for mod in self.allmodules.modules
            )
        )
        if hidden_count:
            notes.append(self.strings["hidden_note"].format(hidden_count))

        if not self.lookup("LoaderMod").fully_loaded:
            notes.append(self.strings["partial_load"])

        return "".join(f"\n{note}" for note in notes)

    def _render_help(
        self,
        sections: dict[str, list[ModuleCommands]],
        is_restricted: bool,
        footer: str,
    ) -> str:
        prefix = utils.escape_html(self.get_prefix())
        header = "{}{} {}\n".format(
            f"{self.strings['only_permitted']}\n" if is_restricted else "",
            self.config["desc_icon"],
            self.strings["cmds_header"].format(prefix),
        )

        for desc_len in DESC_LENGTHS:
            text = header + self._render_sections(sections, desc_len) + footer
            if self._fits_message(text):
                return text

        compact_footer = f"{footer}\n{self.strings['compact_note'].format(prefix)}"
        return self._render_truncated(header, sections, compact_footer)

    def _render_truncated(
        self,
        header: str,
        sections: dict[str, list[ModuleCommands]],
        footer: str,
    ) -> str:
        remaining = {category: list(mods) for category, mods in sections.items()}
        omitted = 0
        while True:
            truncated_note = (
                f"\n{self.strings['truncated'].format(omitted)}" if omitted else ""
            )
            text = (
                header
                + self._render_sections(remaining, None)
                + truncated_note
                + footer
            )
            if self._fits_message(text) or not any(remaining.values()):
                return text

            last_category = next(
                category
                for category in reversed(CATEGORY_ORDER)
                if remaining.get(category)
            )
            remaining[last_category].pop()
            omitted += 1

    @loader.command(
        ru_doc="[args] | Помощь с вашими модулями!",
        ua_doc="[args] | допоможіть з вашими модулями!",
        de_doc="[args] | Hilfe mit deinen Modulen!",
    )
    async def help(self, message: Message):
        """[args] | help with your modules!"""

        args = utils.get_args_raw(message)

        banner = str(self.config["banner_url"])

        if self.config["banner_url"] and self.config["media_quote"] is True:
            banner = InputMediaWebPage(str(self.config["banner_url"]))

        if (
            self.config["banner_url"] and self.client.kage_me.premium is False
        ):  # bcs non-premium users can add in caption only 1024 symbols
            banner = InputMediaWebPage(str(self.config["banner_url"]))

        if not self.config["banner_url"]:
            banner = None

        force = False
        if "-f" in args:
            args = args.replace(" -f", "").replace("-f", "")
            force = True

        only_core = False
        if "-c" in args:
            args = args.replace(" -c", "").replace("-c", "")
            only_core = True
            force = True

        only_loaded = False
        if "-l" in args:
            args = args.replace(" -l", "").replace("-l", "")
            only_loaded = True
            force = True

        if args:
            await self.modhelp(message, args)
            return

        sections, is_restricted = await self._collect_sections(message, force)
        if only_core:
            sections.pop(INSTALLED_CATEGORY, None)
        if only_loaded:
            sections = {INSTALLED_CATEGORY: sections.get(INSTALLED_CATEGORY, [])}

        await utils.answer(
            message,
            self._render_help(sections, is_restricted, self._help_footer(force)),
            file=banner,
            invert_media=self.config["invert_media"],
        )

    @loader.command(
        ru_doc="| Ссылка на чат помощи",
        ua_doc="| посилання для чату служби підтримки",
        de_doc="| Link zum Support-Chat",
    )
    async def support(self, message):
        """| link for support chat"""

        await utils.answer(
            message,
            self.strings["offchats"],
        )
