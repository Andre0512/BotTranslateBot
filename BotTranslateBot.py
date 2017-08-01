#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ForceReply, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import pymysql as mdb
import ReadYaml
import json
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        mdb.install_as_MySQLdb()
        self.con = mdb.connect(cfg['database']['host'], cfg['database']['user'], cfg['database']['password'],
                               cfg['database']['database'], charset='utf8', init_command='SET NAMES UTF8')
        self.cur = self.con.cursor()

    def insert_user(self, user):
        insert_query = """INSERT INTO users (forename, lang_code, country_code, surname, username, id) 
                 VALUES (%s, %s, %s, %s, %s ,%s);"""
        update_query = """UPDATE users SET forename=%s, lang_code=%s, country_code=%s, surname=%s, username=%s 
                        WHERE id=%s"""
        values = (user.first_name, user.language_code.split("-")[0], user.language_code.split("-")[-1],
                  user.last_name if user.last_name else '', user.username if user.username else '', str(user.id))
        try:
            self.cur.execute(insert_query, values)
        except mdb.err.IntegrityError:  # Update user, if exists
            self.cur.execute(update_query, values)
        self.con.commit()

    def insert_bot(self, bot_name, user_id):
        self.cur.execute("INSERT INTO bots (name, owner_id) VALUES (%s, %s);", (bot_name, str(user_id)))
        self.con.commit()

    def insert_translation(self, bot_name, lang_code):
        pass
        # self.cur.execute("INSERT INTO translations (bot_id, lang_code) " +
        #                 "VALUES ((SELECT id FROM bots WHERE name=%s), %s);", (bot_name, lang_code))
        # self.con.commit()

    def __get_bot_id(self, bot_name):
        self.cur.execute("SELECT id FROM bots WHERE name='" + bot_name + "'")
        bot_id = [item[0] for item in self.cur.fetchall()][0]
        return bot_id

    def insert_strings(self, bot_name, str_list):
        bot_id = self.__get_bot_id(bot_name)
        for string in str_list:
            self.cur.execute("INSERT INTO strings (bot_id, name) " +
                             "VALUES (%s, %s);", (str(bot_id), string))
        self.con.commit()

    def insert_words(self, str_dict, lang, bot_name):
        bot_id = self.__get_bot_id(bot_name)
        for keys, values in str_dict.items():
            self.cur.execute("INSERT INTO words (string_id, lang_code, value) " +
                             "VALUES ((SELECT id FROM strings WHERE name=%s and bot_id=%s), %s, %s);",
                             (keys, bot_id, lang, values))
        self.con.commit()

    def insert_languages(self, data):
        query = "INSERT INTO languages (language_code, name, native_name) VALUES (%s, %s, %s)"
        for lang in data:
            try:
                self.cur.execute(query, (lang['code'], lang['name'], lang['nativeName'].encode('unicode-escape')))
            except mdb.err.IntegrityError:  # Do nothing, if language exists
                pass
        self.con.commit()

    def get_user_data(self, user_id):
        self.cur.execute("SELECT lang_code FROM users WHERE id=" + str(user_id))
        language = [item[0] for item in self.cur.fetchall()][0]
        return language

    def search_language(self, letter):
        self.cur.execute(
            "SELECT CONCAT(name, ' ', flag), language_code, native_name FROM languages WHERE language_code LIKE '" + letter +
            "' OR name LIKE '" + letter + "%' OR native_name LIKE '" + letter + "%'")
        result = {item[1]: [item[0].rstrip(' '), item[2].encode('utf-8').decode('unicode-escape')] for item in
                  self.cur.fetchall()}
        return result

    def rollback(self):
        self.con.rollback()

    def __del__(self):
        self.con.close()


def get_lang_keyboard(chat_data):
    keyboard = [['qw', 'e', 'r', 't', 'y', 'u', 'i', 'op'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'kl'],
                ['z', 'x', 'c', 'v', 'b', 'n', 'm']]
    keyboard = [[InlineKeyboardButton(col, callback_data='langkeyboard_' + col) for col in row] for row in keyboard]
    if 'bot_lang' in chat_data:
        keyboard.append(
            [InlineKeyboardButton('✔️ ' + strings[chat_data['lang']]['done'], callback_data='langchoosen')])
    else:
        keyboard.append(
            [InlineKeyboardButton('❌ ' + strings[chat_data['lang']]['cancel'], callback_data='exitadding')])
    return InlineKeyboardMarkup(keyboard)


def get_adding_text(chat_data, add='', letter=None):
    msg = '🤖: @' + chat_data['bot_name'] + '\n🗣 ' + strings[chat_data['lang']]['cur_lang'] + '\n'
    if 'bot_lang' in chat_data:
        for language in chat_data['bot_lang']:
            msg = msg + chat_data['bot_languages'][language][1] + ' (' + chat_data['bot_languages'][language][
                0] + ')\n'
    msg = msg + letter if letter else msg
    msg = msg + '\n\n' + add
    return msg


def send_lang_results(update, chat_data):
    db = Database()
    lang_list = dict()
    keyboard = []
    for first in chat_data['letter_one']:
        for second in chat_data['letter_two']:
            lang_list = dict(list(lang_list.items()) + list(db.search_language(first + second).items()))
    chat_data['bot_languages'] = dict(list(chat_data['bot_languages'].items()) + list(
        lang_list.items())) if 'bot_languages' in chat_data else lang_list
    if bool(lang_list) and len(list(lang_list)) == 1:
        add_language(chat_data, list(lang_list)[0], update.callback_query)
    elif bool(lang_list):
        for key, value in lang_list.items():
            keyboard = keyboard + [[InlineKeyboardButton(value[0], callback_data='language_' + key)]]
        for button in range(4 - len(keyboard)):
            keyboard.append([InlineKeyboardButton('⬆️', callback_data='asfa')])
        keyboard = InlineKeyboardMarkup(keyboard)
        msg = strings[chat_data['lang']]['add_chos']
        update.callback_query.message.edit_text(
            get_adding_text(chat_data, add=msg, letter=chat_data['letter_one'] + chat_data['letter_two']),
            reply_markup=keyboard)
    else:
        update.callback_query.message.edit_text(
            get_adding_text(chat_data, add=strings[chat_data['lang']]['lang_nf']),
            reply_markup=get_lang_keyboard(chat_data))


def add_language(chat_data, lang_code, update):
    db = Database()
    chat_data['bot_lang'] = chat_data['bot_lang'] + [lang_code] if 'bot_lang' in chat_data else [lang_code]
    db.insert_translation(chat_data["bot_name"], lang_code)
    msg = strings[chat_data['lang']]['add_more'].replace("@done", '✔️ ' + strings[chat_data['lang']]['done'])
    update.message.edit_text(
        get_adding_text(chat_data, add=msg), reply_markup=get_lang_keyboard(chat_data),
        parse_mode=ParseMode.MARKDOWN)


def ask_for_strings(form, update, chat_data):
    chat_data['format'] = form
    add = strings[chat_data['lang']]['add_ask'] + '\n'
    if form == "mono":
        eg_yaml = '```´\nen:\n  greeting: Hello\n  state: "How are you?"```'
        eg_json = '```\n{\n  "en":\n    {\n      "greeting": "Hello",\n      "state": "How are you?"\n    }\n}```'
    else:
        eg_yaml = '```\ngreeting: Hello\nstate: "How are you?"```'
        eg_json = '```\n{\n  "greeting": "Hello",\n  "state": "How are you?"\n}```'
    add = add + strings[chat_data['lang']]['add_format'].replace("@examples",
                                                                 "\n*-YAML*\n@eg_yaml\n*-JSON*\n@eg_json")
    add = add.replace("@eg_yaml", eg_yaml).replace("@eg_json", eg_json)
    add = add + '\n' + strings[chat_data['lang']]['add_pos']
    if form == 'poli':
        add = add + '\n\n' + strings[chat_data['lang']]['add_lang'].replace('@language', chat_data['bot_languages'][
            chat_data['bot_lang'][0]][1] + ' (' + chat_data['bot_languages'][chat_data['bot_lang'][0]][
                                                                                0] + ')') + ' ⬇️'
        chat_data['lang_read'] = 0
    update.callback_query.message.edit_text(get_adding_text(chat_data, add=add), parse_mode=ParseMode.MARKDOWN)
    chat_data["mode"] = "get_file"


def read_languages(bot, update):
    if update.message.from_user.id == cfg['bot']['owner']:  # Updating language list only possible for owner
        with open('languages.json', encoding='utf-8') as data_file:
            data = json.load(data_file)
        db = Database()
        db.insert_languages(data)
        update.message.reply_text('Erfolgreich!')


def add_bot(update, lang):
    msg = strings[lang]['add_cmd']
    msg = msg.replace('@example', '`AgeCalculatorBot`')
    update.message.reply_text(msg, reply_markup=ForceReply(), parse_mode=ParseMode.MARKDOWN)


def set_bot_name(update, lang, chat_data, db):
    bot_name = update.message.text[1:] if update.message.text[:1] == '@' else update.message.text
    db.insert_bot(bot_name, update.message.from_user.id)
    chat_data['bot_name'] = bot_name
    update.message.reply_text(
        get_adding_text(chat_data, strings[lang]['add_answ'] + '\n' + strings[chat_data['lang']]['add_hint']),
        reply_markup=get_lang_keyboard(chat_data),
        parse_mode=ParseMode.MARKDOWN)


def start(bot, update, chat_data):
    db = Database()
    db.insert_user(update.message.from_user)
    lang = db.get_user_data(update.message.from_user.id)
    chat_data['lang'] = lang
    update.message.reply_text('Hi!', reply_markup=ReplyKeyboardMarkup([[
        strings[update.message.from_user.language_code.split("-")[0]]['add_bot']]], resize_keyboard=True))


def help(bot, update):
    update.message.reply_text('Help!')


def reply(bot, update, chat_data):
    db = Database()
    lang = db.get_user_data(update.message.from_user.id)
    if update.message.reply_to_message:
        if re.match(strings[lang]['add_cmd'].split("@")[0], update.message.reply_to_message.text):
            set_bot_name(update, lang, chat_data, db)
    elif 'mode' in chat_data and chat_data['mode'] == "get_file":
        analyse_str_msg(chat_data, update, bot)
    else:
        if update.message.text == strings[lang]['add_bot']:
            add_bot(update, lang)
        else:
            update.message.reply_text(update.message.text)


def analyse_str_msg(chat_data, update, bot):
    data = update.message.text
    file_type = "json" if data[:1] == '[' or data[:1] == '{' else False
    file_type = "yaml" if re.match('^.{1,32}:', data) else file_type
    if bool(file_type):
        msg = file_type.upper() + strings[chat_data['lang']]['add_text'] + ' ✅'
        message_id = update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        file_name = str(update.message.from_user.id) + '.' + file_type
        with open(os.path.join(os.path.dirname(__file__), './downloads/' + file_name), "wb") as text_file:
            text_file.write(data.encode('utf-8'))
        read_string_file(file_name, msg, message_id, bot, chat_data)
    else:
        update.message.reply_text(strings[chat_data['lang']]['add_err'])


def read_json(file_name):
    state = True
    try:
        with open(os.path.join(os.path.dirname(__file__), file_name), encoding="utf-8") as data_file:
            data = json.load(data_file)
    except json.decoder.JSONDecodeError:
        try:
            with open(os.path.join(os.path.dirname(__file__), file_name), encoding="utf-8-sig") as data_file:
                data = json.load(data_file)
        except json.decoder.JSONDecodeError as e:
            data = None
            state = str(e)
    return data, state


def read_string_file(file_name, msg, message_id, bot, chat_data):
    state = True
    data = None
    file_type = file_name.split(".")[-1]
    if file_type == "json":
        data, state = read_json("downloads/" + file_name)
    elif file_type == "yaml":
        data, state = ReadYaml.get_yml("downloads/" + file_name)
        state = re.sub('\"[^"]*\"', 'file', state) if not state is True else state
    if not state is True:
        msg = msg + "\n\n" + strings[chat_data['lang']]['error'] + " ☹️\n`" + state + "` "
    else:
        msg = msg + "\n\n" + file_type.upper() + strings[chat_data['lang']]['add_file'] + " ✅"
    bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                          parse_mode=ParseMode.MARKDOWN)
    bot_lang = 0 if not 'lang_read' in chat_data else chat_data['lang_read']
    if not chat_data["format"] == "mono":
        str_list = list(data.keys())
        db = Database()
        if bot_lang == 0:
            db.insert_strings(chat_data["bot_name"], str_list)
            msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_strings'] + " ✅"
            bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                                  parse_mode=ParseMode.MARKDOWN)
        db.insert_words(data, chat_data["bot_lang"][bot_lang], chat_data["bot_name"])
        language = chat_data['bot_languages'][chat_data['bot_lang'][bot_lang]][1] + ' (' + \
                   chat_data['bot_languages'][chat_data['bot_lang'][bot_lang]][0] + ')'
        msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_words'].replace("@lang",
                                                                                                        language) + " ✅"
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              parse_mode=ParseMode.MARKDOWN)
        if chat_data['format'] == "poli":
            if len(chat_data['bot_lang']) > bot_lang:
                chat_data['lang_read'] = chat_data['lang_read'] + 1
                lango = chat_data['bot_languages'][chat_data['bot_lang'][chat_data['lang_read']]][1] + ' (' + \
                        chat_data['bot_languages'][chat_data['bot_lang'][chat_data['lang_read']]][0] + ')'
                add = '\n\n' + strings[chat_data['lang']]['add_lango'].replace('@language', lango) + ' ⬇️'
                bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg + add,
                                      parse_mode=ParseMode.MARKDOWN)
    else:
        str_list = list(next(iter(data.values())))
        db = Database()
        db.insert_strings(chat_data["bot_name"], str_list)
        msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_strings'] + " ✅"
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              parse_mode=ParseMode.MARKDOWN)
        for key, value in data.items():
            db.insert_words(value, key, chat_data["bot_name"])
            language = chat_data['bot_languages'][key][1] + ' (' + chat_data['bot_languages'][key][0] + ')'
            msg = msg + '\n\n' + str(len(list(value.keys()))) + " " + strings[chat_data['lang']][
                'add_words'].replace("@lang",
                                     language) + " ✅"
            bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                                  parse_mode=ParseMode.MARKDOWN)


def handle_file(bot, update, chat_data):
    file_type = update.message.document.file_name.split(".")[-1]
    file_name = str(update.message.from_user.id) + "_" + update.message.document.file_name
    if file_type in ["json", "yaml"]:
        file_id = bot.getFile(update.message.document.file_id)
        file_id.download(custom_path=os.path.join(os.path.dirname(__file__), "downloads/") + file_name)
        msg = strings[chat_data['lang']]['add_receiv'].replace("@filename",
                                                               "`" + update.message.document.file_name + "`")
        message_id = update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        read_string_file(file_name, msg, message_id, bot, chat_data)


def reply_button(bot, update, chat_data):
    update.callback_query.answer()
    arg_list = update.callback_query.data.split("_")
    arg_one, arg_two = arg_list if len(arg_list) > 1 else [arg_list[0], None]
    if arg_one == 'langkeyboard':
        if 'letter_one' in chat_data:
            chat_data['letter_two'] = arg_two
            send_lang_results(update, chat_data)
            chat_data.pop("letter_one", None)
            chat_data.pop("letter_two", None)
        else:
            chat_data['letter_one'] = arg_two
            update.callback_query.message.edit_text(
                get_adding_text(chat_data, add=strings[chat_data['lang']]['add_answ'], letter=arg_two),
                reply_markup=get_lang_keyboard(chat_data))
    if arg_one == 'language':
        add_language(chat_data, arg_two, update.callback_query)
    if arg_one == 'langchoosen':
        if len(chat_data["bot_lang"]) > 1:
            add = strings[chat_data['lang']]['add_type']
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton('☝️ ' + strings[chat_data['lang']]['add_mono'],
                                       callback_data='format_mono')],
                 [InlineKeyboardButton('✋️ ' + strings[chat_data['lang']]['add_poli'],
                                       callback_data='format_poli')]])
            update.callback_query.message.edit_text(get_adding_text(chat_data, add=add), reply_markup=keyboard)
        else:
            ask_for_strings('sinlge', update, chat_data)
            # chat_data.pop("bot_lang", None)
            # chat_data.pop("bot_name", None)
            # chat_data.pop("bot_languages", None)
    if arg_one == 'format':
        ask_for_strings(arg_two, update, chat_data)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    global cfg
    cfg, state = ReadYaml.get_yml('./config.yml')

    global strings
    strings, state = ReadYaml.get_yml('./strings.yml')

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
