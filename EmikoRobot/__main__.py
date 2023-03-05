import html
import os
import json
import importlib
import time
import re
import sys
import traceback
import EmikoRobot.modules.sql.users_sql as sql
from sys import argv
from typing import Optional
from telegram import __version__ as peler
from platform import python_version as memek
from EmikoRobot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    BOT_USERNAME as bu,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from EmikoRobot.modules import ALL_MODULES
from EmikoRobot.modules.helper_funcs.chat_status import is_user_admin
from EmikoRobot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
*𝙷𝙴𝙻𝙻𝙾 {} !*
[🤖] 𝙸'𝙼 𝙰𝙽 𝙰𝙽𝙸𝙼𝙴-𝚃𝙷𝙴𝙼𝙴 𝙼𝙰𝙽𝙰𝙶𝙴𝙼𝙴𝙽𝚃 𝙱𝙾𝚃 [🤖](https://telegra.ph/file/04a8f86a31f16aacdc2f8.jpg)
────────────────────────
※ 𝚄𝙿𝚃𝙸𝙼𝙴 : `{}`
※ 𝚄𝚂𝙴𝚁𝚂 : `{}`
※ 𝙶𝚁𝙾𝚄𝙿 : `{}` 
────────────────────────
𝙷𝙸𝚃 » /help « 𝚃𝙾 𝚂𝙴𝙴 𝙼𝚈 𝙰𝚅𝙰𝙸𝙻𝙰𝙱𝙻𝙴 𝙲𝙾𝙼𝙼𝙰𝙽𝙳𝚂 !!
"""

buttons = [
    [
        InlineKeyboardButton(text=f"𝙰𝙱𝙾𝚄𝚃 {dispatcher.bot.first_name}", callback_data="emiko_"),
    ],
    [
        InlineKeyboardButton(text="𝙶𝙴𝚃 𝙷𝙴𝙻𝙿", callback_data="help_back"),
        InlineKeyboardButton(
            text="𝚃𝚁𝚈 𝙸𝙽𝙻𝙸𝙽𝙴!", switch_inline_query_current_chat=""
        ),
    ],
    [
        InlineKeyboardButton(
            text="🤖 𝙰𝙳𝙳 𝙼𝙴 𝚃𝙾 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿 🤖", url=f"t.me/{bu}?startgroup=new"),
    ],
]


HELP_STRINGS = """
𝙲𝙻𝙸𝙲𝙺 𝙾𝙽 𝚃𝙷𝙴 𝙱𝚄𝚃𝚃𝙾𝙽 𝙱𝙴𝙻𝙻𝙾𝚆 𝚃𝙾 𝙶𝙴𝚃 𝙳𝙴𝚂𝙲𝚁𝙸𝙿𝚃𝙸𝙾𝙽 𝙰𝙱𝙾𝚄𝚃 𝚂𝙿𝙴𝙲𝙸𝙵𝙸𝙲𝚂 𝙲𝙾𝙼𝙼𝙰𝙽𝙳."""


DONATE_STRING = """𝙷𝙴𝚈𝙰, 𝙶𝙻𝙰𝙳 𝚃𝙾 𝙷𝙴𝙰𝚁 𝚈𝙾𝚄 𝚆𝙰𝙽𝚃 𝚃𝙾 𝙳𝙾𝙽𝙰𝚃𝙴!
 𝚈𝙾𝚄 𝙲𝙰𝙽 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝚃𝙷𝙴 𝙿𝚁𝙾𝙹𝙴𝙲𝚃 𝙱𝚈 𝙲𝙾𝙽𝚃𝙰𝙲𝚃𝙸𝙽𝙶 @ZenzNT \
 𝚂𝚄𝙿𝙿𝙾𝚁𝚃𝙸𝙽𝙶 𝙸𝚂𝙽𝚃 𝙰𝙻𝚆𝙰𝚈𝚂 𝙵𝙸𝙽𝙰𝙽𝙲𝙸𝙰𝙻! \
 𝚃𝙷𝙾𝚂𝙴 𝚆𝙷𝙾 𝙲𝙰𝙽𝙽𝙾𝚃 𝙿𝚁𝙾𝚅𝙸𝙳𝙴 𝙼𝙾𝙽𝙴𝚃𝙰𝚁𝚈 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙰𝚁𝙴 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝚃𝙾 𝙷𝙴𝙻𝙿 𝚄𝚂 𝙳𝙴𝚅𝙴𝙻𝙾𝙿 𝚃𝙷𝙴 𝙱𝙾𝚃 𝙰𝚃."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("EmikoRobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            uptime = get_readable_time((time.time() - StartTime))
            update.effective_message.reply_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),                        
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
            )
    else:
        update.effective_message.reply_text(
            f"👋 Hi, I'm {dispatcher.bot.first_name}. Nice to meet You.",
            parse_mode=ParseMode.HTML
       )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


def emiko_about_callback(update, context):
    query = update.callback_query
    if query.data == "emiko_":
        query.message.edit_text(
            text=f"𝙸'𝙼 *{dispatcher.bot.first_name}*, 𝙰 𝙿𝙾𝚆𝙴𝚁𝙵𝚄𝙻 𝙶𝚁𝙾𝚄𝙿 𝙼𝙰𝙽𝙰𝙶𝙴𝙼𝙴𝙽𝚃 𝙱𝙾𝚃 𝙱𝚄𝙸𝙻𝚃 𝚃𝙾 𝙷𝙴𝙻𝙿 𝚈𝙾𝚄 𝙼𝙰𝙽𝙰𝙶𝙴 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿 𝙴𝙰𝚂𝙸𝙻𝚈."
            "\n ※ 𝙸 𝙲𝙰𝙽 𝚁𝙴𝚂𝚃𝚁𝙸𝙲𝚃 𝚄𝚂𝙴𝚁𝚂."
            "\n ※ 𝙸 𝙲𝙰𝙽 𝙶𝚁𝙴𝙴𝚃 𝚄𝚂𝙴𝚁𝚂 𝚆𝙸𝚃𝙷 𝙲𝚄𝚂𝚃𝙾𝙼𝙸𝚉𝙰𝙱𝙻𝙴 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝙼𝙴𝚂𝚂𝙰𝙶𝙴𝚂 𝙰𝙽𝙳 𝙴𝚅𝙴𝙽 𝚂𝙴𝚃 𝙰 𝙶𝚁𝙾𝚄𝙿'𝚂 𝚁𝚄𝙻𝙴𝚂."
            "\n ※ 𝙸 𝙷𝙰𝚅𝙴 𝙰𝙽 𝙰𝙳𝚅𝙰𝙽𝙲𝙴𝙳 𝙰𝙽𝚃𝙸-𝙵𝙻𝙾𝙾𝙳 𝚂𝚈𝚂𝚃𝙴𝙼."
            "\n ※ 𝙸 𝙲𝙰𝙽 𝚆𝙰𝚁𝙽 𝚄𝚂𝙴𝚁𝚂 𝚄𝙽𝚃𝙸𝙻 𝚃𝙷𝙴𝚈 𝚁𝙴𝙰𝙲𝙷 𝙼𝙰𝚇 𝚆𝙰𝚁𝙽𝚂, 𝚆𝙸𝚃𝙷 𝙴𝙰𝙲𝙷 𝙿𝚁𝙴𝙳𝙴𝙵𝙸𝙽𝙴𝙳 𝙰𝙲𝚃𝙸𝙾𝙽𝚂 𝚂𝚄𝙲𝙷 𝙰𝚂 𝙱𝙰𝙽, 𝙼𝚄𝚃𝙴, 𝙺𝙸𝙲𝙺, 𝙴𝚃𝙲."
            "\n ※ 𝙸 𝙷𝙰𝚅𝙴 𝙰 𝙽𝙾𝚃𝙴 𝙺𝙴𝙴𝙿𝙸𝙽𝙶 𝚂𝚈𝚂𝚃𝙴𝙼, 𝙱𝙻𝙰𝙲𝙺𝙻𝙸𝚂𝚃𝚂, 𝙰𝙽𝙳 𝙴𝚅𝙴𝙽 𝙿𝚁𝙴𝙳𝙴𝚃𝙴𝚁𝙼𝙸𝙽𝙴𝙳 𝚁𝙴𝙿𝙻𝙸𝙴𝚂 𝙾𝙽 𝙲𝙴𝚁𝚃𝙰𝙸𝙽 𝙺𝙴𝚈𝚆𝙾𝚁𝙳𝚂."
            "\n ※ 𝙸 𝙲𝙷𝙴𝙲𝙺 𝙵𝙾𝚁 𝙰𝙳𝙼𝙸𝙽𝚂' 𝙿𝙴𝚁𝙼𝙸𝚂𝚂𝙸𝙾𝙽𝚂 𝙱𝙴𝙵𝙾𝚁𝙴 𝙴𝚇𝙴𝙲𝚄𝚃𝙸𝙽𝙶 𝙰𝙽𝚈 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 𝙰𝙽𝙳 𝙼𝙾𝚁𝙴 𝚂𝚃𝚄𝙵𝙵𝚂."
            f"\n\n_*{dispatcher.bot.first_name}*'𝚂 𝙻𝙸𝙲𝙴𝙽𝚂𝙴𝙳 𝚄𝙽𝙳𝙴𝚁 𝚃𝙷𝙴 𝙶𝙽𝚄 𝙶𝙴𝙽𝙴𝚁𝙰𝙻 𝙿𝚄𝙱𝙻𝙸𝙲 𝙻𝙸𝙲𝙴𝙽𝚂𝙴 𝚅3.0_"
            f"\n\n𝙲𝙻𝙸𝙲𝙺 𝙾𝙽 𝙱𝚄𝚃𝚃𝙾𝙽 𝙱𝙴𝙻𝙻𝙾𝚆 𝚃𝙾 𝙶𝙴𝚃 𝙱𝙰𝚂𝙸𝙲 𝙷𝙴𝙻𝙿 𝙵𝙾𝚁 *{dispatcher.bot.first_name}*",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="𝙰𝙳𝙼𝙸𝙽", callback_data="emiko_admin"),
                    InlineKeyboardButton(text="𝙽𝙾𝚃𝙴𝚂", callback_data="emiko_notes"),
                 ],
                 [
                    InlineKeyboardButton(text="𝚂𝚄𝙿𝙿𝙾𝚁𝚃", callback_data="emiko_support"),
                    InlineKeyboardButton(text="𝙲𝚁𝙴𝙳𝙸𝚃𝚂", callback_data="emiko_credit"),
                 ],
                 [
                    InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="source_back"),
                 ]
                ]
            ),
        )

    elif query.data == "emiko_admin":
        query.message.edit_text(
            text=f"\n*※ 𝙻𝙴𝚃'𝚂 𝙼𝙰𝙺𝙴 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿 𝙱𝙸𝚃 𝙴𝙵𝙵𝙴𝙲𝚃𝙸𝚅𝙴 𝙽𝙾𝚆*"
            f"\n𝙲𝙾𝙽𝙶𝚁𝙰𝚃𝚄𝙻𝙰𝚃𝙸𝙾𝙽𝚂, {dispatcher.bot.first_name} 𝙽𝙾𝚆 𝚁𝙴𝙰𝙳𝚈 𝚃𝙾 𝙼𝙰𝙽𝙰𝙶𝙴 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿."
            "\n\n*※ 𝙰𝙳𝙼𝙸𝙽 𝚃𝙾𝙾𝙻𝚂*"
            "\n𝙱𝙰𝚂𝙸𝙲 𝙰𝙳𝙼𝙸𝙽 𝚃𝙾𝙾𝙻𝚂 𝙷𝙴𝙻𝙿 𝚈𝙾𝚄 𝚃𝙾 𝙿𝚁𝙾𝚃𝙴𝙲𝚃 𝙰𝙽𝙳 𝙿𝙾𝚆𝙴𝚁𝚄𝙿 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿."
            "\n𝚈𝙾𝚄 𝙲𝙰𝙽 𝙱𝙰𝙽 𝙼𝙴𝙼𝙱𝙴𝚁𝚂, 𝙺𝙸𝙲𝙺 𝙼𝙴𝙼𝙱𝙴𝚁𝚂, 𝙿𝚁𝙾𝙼𝙾𝚃𝙴 𝚂𝙾𝙼𝙴𝙾𝙽𝙴 𝙰𝚂 𝙰𝙳𝙼𝙸𝙽 𝚃𝙷𝚁𝙾𝚄𝙶𝙷 𝙲𝙾𝙼𝙼𝙰𝙽𝙳𝚂 𝙾𝙵 𝙱𝙾𝚃."
            "\n\n*※ 𝙶𝚁𝙴𝙴𝚃𝙸𝙽𝙶𝚂*"
            "\n𝙻𝙴𝚃𝚂 𝚂𝙴𝚃 𝙰 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝙼𝙴𝚂𝚂𝙰𝙶𝙴 𝚃𝙾 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝙽𝙴𝚆 𝚄𝚂𝙴𝚁𝚂 𝙲𝙾𝙼𝙸𝙽𝙶 𝚃𝙾 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿."
            "\n𝚂𝙴𝙽𝙳 /setwelcome [𝙼𝙴𝚂𝚂𝙰𝙶𝙴] 𝚃𝙾 𝚂𝙴𝚃 𝙰 𝚆𝙴𝙻𝙲𝙾𝙼𝙴 𝙼𝙴𝚂𝚂𝙰𝙶𝙴!"
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="emiko_")]]
            ),
        )

    elif query.data == "emiko_notes":
        query.message.edit_text(
            text=f"<b>※ 𝚂𝙴𝚃𝚃𝙸𝙽𝙶 𝚄𝙿 𝙽𝙾𝚃𝙴𝚂</b>"
            f"\n𝚈𝙾𝚄 𝙲𝙰𝙽 𝚂𝙰𝚅𝙴 𝙼𝙴𝚂𝚂𝙰𝙶𝙴/𝙼𝙴𝙳𝙸𝙰/𝙰𝚄𝙳𝙸𝙾 𝙾𝚁 𝙰𝙽𝚈𝚃𝙷𝙸𝙽𝙶 𝙰𝚂 𝙽𝙾𝚃𝙴𝚂"
            f"\n𝚃𝙾 𝙶𝙴𝚃 𝙰 𝙽𝙾𝚃𝙴 𝚂𝙸𝙼𝙿𝙻𝚈 𝚄𝚂𝙴 # 𝙰𝚃 𝚃𝙷𝙴 𝙱𝙴𝙶𝙸𝙽𝙽𝙸𝙽𝙶 𝙾𝙵 𝙰 𝚆𝙾𝚁𝙳"
            f"\n\n𝚈𝙾𝚄 𝙲𝙰𝙽 𝙰𝙻𝚂𝙾 𝚂𝙴𝚃 𝙱𝚄𝚃𝚃𝙾𝙽𝚂 𝙵𝙾𝚁 𝙽𝙾𝚃𝙴𝚂 𝙰𝙽𝙳 𝙵𝙸𝙻𝚃𝙴𝚁𝚂 (𝚁𝙴𝙵𝙴𝚁 𝙷𝙴𝙻𝙿 𝙼𝙴𝙽𝚄)",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="emiko_")]]
            ),
        )
    elif query.data == "emiko_support":
        query.message.edit_text(
            text="*※ 𝚁𝙰𝙶𝙽𝙰 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙲𝙷𝙰𝚃*"
            f"\n𝙹𝙾𝙸𝙽 𝙼𝚈 𝚂𝚄𝙿𝙿𝙾𝚁𝚃 𝙶𝚁𝙾𝚄𝙿 𝙵𝙾𝚁 𝚂𝙴𝙴 𝙾𝚁 𝚁𝙴𝙿𝙾𝚁𝚃 𝙰 𝙿𝚁𝙾𝙱𝙻𝙴𝙼 𝙾𝙽 {dispatcher.bot.first_name}.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="𝚂𝚄𝙿𝙿𝙾𝚁𝚃", url="https://t.me/ZenzProject"),
                    InlineKeyboardButton(text="𝚄𝙿𝙳𝙰𝚃𝙴𝚂", url="https://t.me/ZenzProject"),
                 ],
                 [
                    InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="emiko_"),
                 
                 ]
                ]
            ),
        )


    elif query.data == "emiko_credit":
        query.message.edit_text(
            text=f"*※ 𝙲𝚁𝙴𝙳𝙸𝚃𝚂 𝙵𝙾𝚁 {dispatcher.bot.first_name}*\n"
            f"\n𝙷𝙴𝚁𝙴 𝙳𝙴𝚅𝙴𝙻𝙾𝙿𝙴𝚁𝚂 𝙼𝙰𝙺𝙸𝙽𝙶 𝙰𝙽𝙳 𝙶𝙸𝚅𝙴 𝙸𝙽𝚂𝙿𝙸𝚁𝙰𝚃𝙸𝙾𝙽 𝙵𝙾𝚁 𝙼𝙰𝙳𝙴 𝚃𝙷𝙴 {dispatcher.bot.first_name}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="𝚉𝙴𝙽", url="https://t.me/ZenzNT"), 
                 ],
                 [
                    InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="emiko_"),
                 ]
                ]
            ),
        )

def Source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text="๏›› This advance command for Musicplayer."
            "\n\n๏ Command for admins only."
            "\n • `/reload` - For refreshing the adminlist."
            "\n • `/pause` - To pause the playback."
            "\n • `/resume` - To resuming the playback You've paused."
            "\n • `/skip` - To skipping the player."
            "\n • `/end` - For end the playback."
            "\n • `/musicplayer <on/off>` - Toggle for turn ON or turn OFF the musicplayer."
            "\n\n๏ Command for all members."
            "\n • `/play` <query /reply audio> - Playing music via YouTube."
            "\n • `/playlist` - To playing a playlist of groups or your personal playlist",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="emiko_")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="𝙷𝙴𝙻𝙿",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "Contact me in PM to get the list of possible commands.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="𝙷𝙴𝙻𝙿",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="𝙶𝙾 𝙱𝙰𝙲𝙺", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="𝙶𝙾 𝙱𝙰𝙲𝙺",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Settings",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1696941720:
            update.effective_message.reply_text(
                "I'm free for everyone ❤️ If you wanna make me smile, just join"
                "[My Channel]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(
                f"@{SUPPORT_CHAT}", 
                "👋 Hi, i'm alive.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_.*", run_async=True
    )

    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    about_callback_handler = CallbackQueryHandler(
        emiko_about_callback, pattern=r"emiko_", run_async=True
    )

    source_callback_handler = CallbackQueryHandler(
        Source_about_callback, pattern=r"source_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, drop_pending_updates=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
