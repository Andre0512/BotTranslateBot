#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from telegram.ext.dispatcher import run_async
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ForceReply, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
import logging
import ReadYaml
import json
import AddBot
import TranslateBot
from Database import Database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def get_std_keyboard(chat_data):
    keyboard = ReplyKeyboardMarkup(
        [['➕ ' + strings[chat_data['lang']]['add_bot'], '👤 ' + strings[chat_data['lang']]['my_profile']]],
        resize_keyboard=True)
    return keyboard


def start(bot, update, chat_data):
    db = Database(cfg)
    state, lang = db.insert_user(update.message.from_user)
    if state:
        chat_data['lang'] = lang
    else:
        if 'lang' not in chat_data:
            chat_data['lang'] = db.get_user_data(update.message.from_user.id)
    if lang not in strings:
        chat_data['lang'] = 'en'
        chat_data['orginal_lang'] = lang
    if update.message.text.split(" ")[-1] == "/start":
        if state:
            TranslateBot.start_translate_new(update, chat_data)
        else:
            update.message.reply_text('Hi!', reply_markup=TranslateBot.get_std_keyboard(chat_data))
    else:
        chat_data['bot'] = update.message.text.split(" ")[-1]
        if state:
            TranslateBot.start_translate_new(update, chat_data)
        else:
            TranslateBot.start_translation(bot, update, chat_data)


def read_languages(bot, update):
    if update.message.from_user.id == cfg['bot']['owner']:  # Updating language list only possible for owner
        with open('languages.json', encoding='utf-8') as data_file:
            data = json.load(data_file)
        db = Database(cfg)
        db.insert_languages(data)
        update.message.reply_text('Erfolgreich!')


def help(bot, update):
    update.message.reply_text('Help!')


def reply(bot, update, chat_data):
    db = Database(cfg)
    if 'lang' not in chat_data:
        chat_data['lang'] = db.get_user_data(update.message.from_user.id)
    if update.message.reply_to_message:
        if re.match(strings[chat_data['lang']]['add_cmd'].split("@")[0], update.message.reply_to_message.text) \
                or re.match(strings[chat_data['lang']]['add_name_err'], update.message.reply_to_message.text):
            AddBot.set_bot_name(update, chat_data['lang'], chat_data, db)
    elif 'mode' in chat_data and chat_data['mode'] == "get_file":
        AddBot.analyse_str_msg(chat_data, update, bot)
    elif 'mode' in chat_data and chat_data['mode'].split('_')[0] == 'tr':
        if db.insert_word(update.message.text, chat_data['strings'][int(chat_data['mode'].split('_')[1])],
                          chat_data['tlangid'], update.message.from_user.id):
            chat_data['confirm_own'] = db.get_last_word_id()
            TranslateBot.translate_text(update, chat_data, db, int(chat_data['mode'].split('_')[1]), bot, first=True,
                                        confirm=True)
        else:
            add = '\n❌ ' + strings[chat_data['lang']]['tr_old']
            TranslateBot.translate_text(update, chat_data, db, int(chat_data['mode'].split('_')[1]), bot, first=True,
                                        add=add)
    else:
        if update.message.text == '➕ ' + strings[chat_data['lang']]['add_bot']:
            AddBot.add_bot(update, chat_data['lang'])
        elif update.message.text == '👤 ' + strings[chat_data['lang']]['my_profile']:
            TranslateBot.my_profile(update, chat_data)
        else:
            update.message.reply_text(update.message.text, reply_markup=TranslateBot.get_std_keyboard(chat_data))


def handle_file(bot, update, chat_data):
    AddBot.handle_file(bot, update, chat_data)


def reply_button(bot, update, chat_data):
    if 'lang' not in chat_data:
        db = Database(cfg)
        chat_data['lang'] = db.get_user_data(update.message.from_user.id)
    arg_list = update.callback_query.data.split("_")
    arg_one, arg_two = arg_list if len(arg_list) > 1 else [arg_list[0], None]
    if arg_one in ['langkeyboard', 'language', 'langchoosen', 'format', 'exitadding', 'langdelete']:
        AddBot.reply_button(bot, update, chat_data, arg_one, arg_two)
    if arg_one in ['langyes', 'langno', 'langcho', 'fromlang', 'tlang', 'searchkb', 'translnav', 'transldone', 'google',
                   'confirm']:
        TranslateBot.reply_button(bot, update, chat_data, arg_one, arg_two)
    update.callback_query.answer()


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    global cfg
    cfg, state = ReadYaml.get_yml('./config.yml')

    global strings
    strings, state = ReadYaml.get_yml('./strings.yml')

    AddBot.set_global(cfg, strings)
    TranslateBot.set_global(cfg, strings)

    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start, pass_chat_data=True))
    dp.add_handler(CommandHandler("readLanguages", read_languages))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, reply, pass_chat_data=True))
    dp.add_handler(MessageHandler(Filters.document, handle_file, pass_chat_data=True))
    dp.add_handler(CallbackQueryHandler(reply_button, pass_chat_data=True))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
