#!/usr/bin/env python
# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import pymysql as mdb
import ReadYaml
import json

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
        values = (user.first_name, user.language_code.split("-")[0], user.language_code.split("-")[1],
                  user.last_name if user.last_name else '', user.username if user.username else '', str(user.id))
        try:
            self.cur.execute(insert_query, values)
        except mdb.err.IntegrityError:
            self.cur.execute(update_query, values)
        self.con.commit()

    def insert_languages(self, data):
        query = "INSERT INTO languages (language_code, name, native_name) VALUES (%s, %s, %s)"
        for lang in data:
            try:
                self.cur.execute(query, (lang['code'], lang['name'], lang['nativeName'].encode('unicode-escape')))
            except mdb.err.IntegrityError:
                pass
        self.con.commit()

    def rollback(self):
        self.con.rollback()

    def __del__(self):
        self.con.close()


def read_languages(bot, update):
    if update.message.from_user.id == cfg['bot']['owner']:
        with open('languages.json', encoding='utf-8') as data_file:
            data = json.load(data_file)
        db = Database()
        db.insert_languages(data)
        update.message.reply_text('Erfolgreich!')


def start(bot, update):
    db = Database()
    db.insert_user(update.message.from_user)
    update.message.reply_text('Hi!')


def help(bot, update):
    update.message.reply_text('Help!')


def reply(bot, update):
    update.message.reply_text(update.message.text)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def main():
    global cfg
    cfg = ReadYaml.get_yml('./config.yml')

    updater = Updater(cfg['bot']['token'])

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("readLanguages", read_languages))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, reply))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
