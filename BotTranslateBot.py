#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ForceReply, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
import logging
import pymysql as mdb
import ReadYaml
import json
import AddBot

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, cfg):
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
            state = True
        except mdb.err.IntegrityError:  # Update user, if exists
            self.cur.execute(update_query, values)
            state = False
        self.con.commit()
        return state

    def update_language(self, user_id, lang_code):
        self.cur.execute("UPDATE users SET lang_code=%s WHERE id=%s", (lang_code, user_id))
        self.con.commit()

    def delete_bot(self, bot_name):
        self.cur.execute("DELETE FROM bots WHERE name=%s;", (bot_name))
        self.con.commit()

    def insert_bot(self, bot_name, user_id):
        status = True
        try:
            self.cur.execute("INSERT INTO bots (name, owner_id) VALUES (%s, %s);", (bot_name, str(user_id)))
        except mdb.err.IntegrityError:
            status = False
        self.con.commit()
        return status

    def __get_bot_id(self, bot_name):
        self.cur.execute("SELECT id FROM bots WHERE name='" + bot_name + "'")
        bot_id = [item[0] for item in self.cur.fetchall()][0]
        return bot_id

    def insert_strings(self, bot_name, str_list):
        bot_id = self.__get_bot_id(bot_name)
        for string in str_list:
            self.cur.execute("SELECT id FROM strings WHERE name=%s and bot_id=%s", (string, str(bot_id)))
            length = len(self.cur.fetchall())
            if length == 0:
                self.cur.execute("INSERT INTO strings (bot_id, name) " + "VALUES (%s, %s);", (str(bot_id), string))
        self.con.commit()

    def insert_bot_language(self, bot_name, lang_list):
        bot_id = self.__get_bot_id(bot_name)
        for lang in lang_list:
            self.cur.execute("INSERT INTO translations (bot_id, lang_code, state) VALUES (%s, %s,  0);", (bot_id, lang))
        self.con.commit()

    def insert_words(self, str_dict, lang, bot_name, user_id):
        bot_id = self.__get_bot_id(bot_name)
        for key, value in str_dict.items():
            self.cur.execute("INSERT INTO words (translation_id, value, creator_id, string_id) " +
                             "VALUES ((SELECT MAX(id) FROM translations), %s, %s, (SELECT id FROM strings WHERE name=%s"
                             + " AND bot_id=%s))", (value, user_id, key, bot_id))
        self.con.commit()

    def insert_languages(self, data):
        query_insert = "INSERT INTO languages (name, native_name, flag, language_code) VALUES (%s, %s, %s, %s)"
        query_update = "UPDATE languages SET name=%s, native_name=%s, flag=%s WHERE language_code=%s"
        for lang in data:
            flag = lang['flag'].encode('unicode-escape') if 'flag' in lang else ''
            values = (lang['name'], lang['nativeName'].encode('unicode-escape'), flag, lang['code'])
            try:
                self.cur.execute(query_insert, values)
            except mdb.err.IntegrityError:
                self.cur.execute(query_update, values)
        self.con.commit()

    def get_user_data(self, user_id):
        self.cur.execute("SELECT lang_code FROM users WHERE id=" + str(user_id))
        language = [item[0] for item in self.cur.fetchall()][0]
        return language

    def get_languages(self, bot_name):
        self.cur.execute("SELECT lang_code FROM translations t INNER JOIN bots b ON t.bot_id=b.id WHERE b.name=%s",
                         (bot_name,))
        result = [lang[0] for lang in self.cur.fetchall()]
        return result

    def search_language(self, letter):
        self.cur.execute(
            "SELECT name, flag, language_code, native_name FROM languages WHERE language_code LIKE '" + letter +
            "' OR name LIKE '" + letter + "%' OR native_name LIKE '" + letter + "%'")
        result = {item[2]: [item[0] + ' ' + item[1].encode('utf-8').decode('unicode-escape') if item[1] else item[0],
                            item[3].encode('utf-8').decode('unicode-escape')] for item in
                  self.cur.fetchall()}
        return result

    def get_language(self, lang_code):
        self.cur.execute("SELECT native_name, flag, name FROM languages WHERE language_code=%s", (lang_code,))
        lang_native, flag, lang = self.cur.fetchall()[:][0]
        return [lang_native.encode('utf-8').decode('unicode-escape'), flag.encode('utf-8').decode(
            'unicode-escape') if flag else None, lang]

    def get_bot_number(self, user_id):
        query = """SELECT COUNT(name), SUM(string), SUM(lang), SUM(value) FROM ( SELECT b.name, COUNT(DISTINCT s.name) 
        AS string, COUNT(DISTINCT t.lang_code) as lang, COUNT(w.value) as value FROM bots b INNER JOIN strings s ON 
        b.id=s.bot_id INNER JOIN translations t ON b.id=t.bot_id INNER JOIN words w ON s.id=w.string_id WHERE 
        b.owner_id=%s GROUP BY b.id ) AS results"""
        self.cur.execute(query, (str(user_id),))
        result = self.cur.fetchall()[0]
        return result

    def rollback(self):
        self.con.rollback()

    def __del__(self):
        self.con.close()


def get_std_keyboard(chat_data):
    keyboard = ReplyKeyboardMarkup(
        [['➕ ' + strings[chat_data['lang']]['add_bot'], '👤 ' + strings[chat_data['lang']]['my_profile']]],
        resize_keyboard=True)
    return keyboard


def read_languages(bot, update):
    if update.message.from_user.id == cfg['bot']['owner']:  # Updating language list only possible for owner
        with open('languages.json', encoding='utf-8') as data_file:
            data = json.load(data_file)
        db = Database(cfg)
        db.insert_languages(data)
        update.message.reply_text('Erfolgreich!')


def start(bot, update, chat_data):
    db = Database(cfg)
    state = db.insert_user(update.message.from_user)
    lang = db.get_user_data(update.message.from_user.id)
    chat_data['lang'] = lang
    if not lang in strings:
        chat_data['lang'] = 'en'
        chat_data['orginal_lang'] = lang
    if update.message.text.split(" ")[-1] == "/start":
        update.message.reply_text('Hi!', reply_markup=get_std_keyboard(chat_data))
    else:
        chat_data['bot'] = update.message.text.split(" ")[-1]
        if state:
            start_translate_new(update, chat_data)
        else:
            start_translation(update, chat_data)
            # update.message.reply_text(update.message.text.split(" ")[-1], reply_markup=ReplyKeyboardMarkup([[
            #     strings[update.message.from_user.language_code.split("-")[0]]['add_bot']]], resize_keyboard=True))


def get_start_text(chat_data, add=None):
    msg = '@' + chat_data['bot'] + ' ' + strings[chat_data['lang']]['transl'] + " 🤖\n"
    msg = msg + strings[chat_data['lang']]['from'] + ': ' + (chat_data[
                                                                 'lang_from'] if 'lang_from' in chat_data else '') + '\n'
    msg = msg + strings[chat_data['lang']]['to'] + ': ' + (
        chat_data['lang_to'] if 'lang_to' in chat_data else ' ') + '\n'
    msg = msg + '\n\n' + add if add else msg
    return msg


def start_translation(update, chat_data, edit=False):
    db = Database(cfg)
    lang_list = db.get_languages(chat_data['bot'])
    lang_list = [db.get_language(language) + [language] for language in lang_list]
    lang_list = [[language[2] + ' ' + language[1] if language[1] else language[2], language[3]] for language in
                 lang_list]
    keyboard = get_tworow_keyboard(lang_list, 'fromlang_')
    msg = strings[chat_data['lang']]['tr_from'] + ' ⬇️'
    if edit:
        update.message.edit_text(get_start_text(chat_data, add=msg), reply_markup=keyboard)
    else:
        update.message.reply_text(get_start_text(chat_data, add=msg), reply_markup=keyboard)


def choose_lang_to(update, chat_data):
    db = Database(cfg)
    from_lang = db.get_language(chat_data['flang'])
    chat_data['lang_from'] = from_lang[0] + ' ' + from_lang[1] if from_lang[1] else from_lang[0]
    keyboard = AddBot.get_lang_keyboard(chat_data)
    update.callback_query.message.edit_text(get_start_text(chat_data), reply_markup=keyboard)


def start_translate_new(update, chat_data):
    # chat_data['orginal_lang'] = 'uk'
    db = Database(cfg)
    language, flag, x = db.get_language(chat_data['orginal_lang'] if 'orginal_lang' in chat_data else chat_data['lang'])
    msg = strings[chat_data['lang']]['tr_greeting'].replace('@name', update.message.from_user.first_name + ' ✌️')
    msg = msg.replace('@bot_name', '@' + chat_data['bot'])
    msg = msg + ' 🌏\n\n' + strings[chat_data['lang']]['tr_lang'].replace('@lang', language) + ' ☺️\n'
    yes = '✔️ ' + strings[chat_data['lang']]['agree'] + ' ' + (flag if flag else '')
    no = '❌ ' + strings[chat_data['lang']]['tr_lang_no'] + ' 🗺'
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(yes, callback_data='langyes'), InlineKeyboardButton(no, callback_data='langno')]])
    if 'orginal_lang' in chat_data:
        msg = msg + '\nUnfortunately nobody has translated me into ' + language + \
              ' 😕\nIs it okay when I speak to you in English?'
    else:
        msg = msg + strings[chat_data['lang']]['tr_lang_fnd'].replace('@lang', language)
    update.message.reply_text(msg, reply_markup=keyboard)


def help(bot, update):
    update.message.reply_text('Help!')


def reply(bot, update, chat_data):
    db = Database(cfg)
    lang = db.get_user_data(update.message.from_user.id)
    if update.message.reply_to_message:
        if re.match(strings[lang]['add_cmd'].split("@")[0], update.message.reply_to_message.text) \
                or re.match(strings[chat_data['lang']]['add_name_err'], update.message.reply_to_message.text):
            AddBot.set_bot_name(update, lang, chat_data, db)
    elif 'mode' in chat_data and chat_data['mode'] == "get_file":
        AddBot.analyse_str_msg(chat_data, update, bot)
    else:
        if update.message.text == '➕ ' + strings[lang]['add_bot']:
            AddBot.add_bot(update, lang)
        elif update.message.text == '👤 ' + strings[chat_data['lang']]['my_profile']:
            my_profile(update, chat_data)
        else:
            update.message.reply_text(update.message.text, reply_markup=get_std_keyboard(chat_data))


def get_profile_text(chat_data):
    return '🤖 *' + str(chat_data['bot_count']) + '* Bots\n🌎 *' + str(chat_data['lang_count']) + '* ' + \
           strings[chat_data['lang']]['langs'] + '\n🗨 *' + str(chat_data['str_count']) + '* Strings\n🗣 *' + str(
        chat_data['val_count']) + '* ' + strings[chat_data['lang']]['trans']


def my_profile(update, chat_data):
    db = Database(cfg)
    chat_data['bot_count'], chat_data['str_count'], chat_data['lang_count'], chat_data['val_count'] = db.get_bot_number(
        update.message.from_user.id)
    get_profile_text(chat_data)
    update.message.reply_text(get_profile_text(chat_data), parse_mode=ParseMode.MARKDOWN)


def handle_file(bot, update, chat_data):
    AddBot.handle_file(bot, update, chat_data)


def reply_button(bot, update, chat_data):
    update.callback_query.answer()
    arg_list = update.callback_query.data.split("_")
    arg_one, arg_two = arg_list if len(arg_list) > 1 else [arg_list[0], None]
    if arg_one in ['langkeyboard', 'language', 'langchoosen', 'format', 'exitadding', 'langdelete']:
        AddBot.reply_button(bot, update, chat_data, arg_one, arg_two)
    elif arg_one == 'langyes':
        start_translation(update.callback_query, chat_data, edit=True)
    elif arg_one == 'langno':
        db = Database(cfg)
        msg = strings[chat_data['lang']]['ok'] + '! 😬\n' + strings[chat_data['lang']]['tr_lang_cho'] + ' ⬇️'
        if 'orginal_lang' in chat_data:
            msg = msg + "\n\nIf you want to help translate this bot into " + db.get_language(chat_data["orginal_lang"])[
                0] + ", follow [this link](" + 'https://t.me/' + cfg['bot']['name'] + '?start=' + cfg['bot'][
                      'name'] + ') ☺️'
            chat_data.pop("orginal_lang", None)
        languages = []
        for lang in list(strings):
            language, flag = db.get_language(lang)
            languages.append([language + ' ' + flag if flag else language, lang])
        keyboard = get_tworow_keyboard(languages, "langcho_")
        update.callback_query.message.edit_text(msg, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    elif arg_one == 'langcho':
        db = Database(cfg)
        db.update_language(update.callback_query.message.chat.id, arg_two)
        start_translation(update.callback_query, chat_data, edit=True)
    elif arg_one == 'fromlang':
        chat_data['flang'] = arg_two
        choose_lang_to(update, chat_data)


def get_tworow_keyboard(str_list, callback):
    keyboard = [InlineKeyboardButton(lang[0], callback_data=callback + lang[1]) for lang in str_list]
    keyboard = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]
    return InlineKeyboardMarkup(keyboard)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    global cfg
    cfg, state = ReadYaml.get_yml('./config.yml')

    global strings
    strings, state = ReadYaml.get_yml('./strings.yml')

    AddBot.set_gloabl(cfg, strings)

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
