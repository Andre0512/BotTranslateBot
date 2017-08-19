#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql as mdb


class Database:
    def __init__(self, cfg):
        mdb.install_as_MySQLdb()
        self.con = mdb.connect(cfg['database']['host'], cfg['database']['user'], cfg['database']['password'],
                               cfg['database']['database'], charset='utf8', init_command='SET NAMES UTF8')
        self.cur = self.con.cursor()

    def insert_user(self, user):
        insert_query = """INSERT INTO users (forename, lang_code, orginal_lang, country_code, surname, username, id) 
                 VALUES (%s, %s, %s, %s, %s, %s ,%s);"""
        update_query = """UPDATE users SET forename=%s, orginal_lang=%s, country_code=%s, surname=%s, 
                    username=%s WHERE id=%s"""
        lang = user.language_code.split("-")[0] if user.language_code else 'en'
        country = user.language_code.split("-")[1] if user.language_code and len(
            user.language_code.split('-')[1]) > 1 else ''
        values = [user.first_name, lang, lang, country, user.last_name if user.last_name else '',
                  user.username if user.username else '', str(user.id)]
        try:
            self.cur.execute(insert_query, tuple(values))
            state = True
        except mdb.err.IntegrityError as e:  # Update user, if exists
            values.pop(2)
            self.cur.execute(update_query, tuple(values))
            state = False
        self.con.commit()
        return state, lang

    def update_language(self, user_id, lang_code):
        self.cur.execute("UPDATE users SET lang_code=%s WHERE id=%s", (lang_code, user_id))
        self.con.commit()

    def delete_bot(self, bot_name):
        self.cur.execute("DELETE FROM bots WHERE name=%s;", (bot_name))
        self.con.commit()

    def delete_word(self, word_id):
        self.cur.execute("DELETE FROM words WHERE id=%s;", (word_id))
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

    def insert_confirmation(self, word_id, string_id, user_id, transl_id):
        self.cur.execute("SELECT c.word_id FROM confirmations c INNER JOIN words w ON c.word_id=w.id "
                         + "WHERE w.string_id=%s and c.user_id=%s", (str(string_id), str(user_id)))
        cur_word = self.cur.fetchall()
        if not word_id:
            self.cur.execute("SELECT id FROM words WHERE string_id=%s AND creator_id=0 AND translation_id=%s",
                             (str(string_id), str(transl_id)))
            word_id = self.cur.fetchall()[0][0]
        if len(cur_word) > 0:
            self.cur.execute("DELETE FROM confirmations WHERE word_id=%s", (cur_word[0][0],))
            self.con.commit()
        self.cur.execute("INSERT INTO confirmations (word_id, user_id) " + "VALUES (%s, %s);",
                         (str(word_id), str(user_id)))
        self.con.commit()

    def insert_bot_language(self, bot_name, lang_list, state):
        bot_id = self.__get_bot_id(bot_name)
        for lang in lang_list:
            self.cur.execute("INSERT INTO translations (bot_id, lang_code, state) VALUES (%s, %s, %s);",
                             (bot_id, lang, state))
        self.con.commit()

    def insert_word(self, value, string_id, transl_id, user_id):
        self.cur.execute("SELECT value FROM words WHERE translation_id=%s AND string_id=%s", (transl_id, string_id))
        if value in [item[0] for item in self.cur.fetchall()]:
            return False
        self.cur.execute("INSERT INTO words (translation_id, value, creator_id, string_id) VALUES (%s, %s, %s, %s)",
                         (transl_id, value, user_id, string_id))
        self.con.commit()
        return True

    def insert_words(self, str_dict, lang, bot_name, user_id):
        bot_id = self.__get_bot_id(bot_name)
        for key, value in str_dict.items():
            self.cur.execute("INSERT INTO words (translation_id, value, creator_id, string_id) VALUES ((SELECT id FROM"
                             + " translations WHERE bot_id=%s AND lang_code=%s), %s, %s, (SELECT id FROM strings WHERE name=%s AND "
                             + "bot_id=%s))", (bot_id, lang, value, user_id, key, bot_id))
        self.con.commit()

    def insert_languages(self, data):
        query_insert = "INSERT INTO languages (name, native_name, flag, google, language_code) VALUES (%s, %s, %s, %s, %s)"
        query_update = "UPDATE languages SET name=%s, native_name=%s, flag=%s, google=%s WHERE language_code=%s"
        for lang in data:
            flag = lang['flag'].encode('unicode-escape') if 'flag' in lang else ''
            values = (lang['name'][:63], lang['nativeName'].encode('unicode-escape'), flag,
                      ('1' if 'google' in lang and lang['google'] == 'True' else '0'), lang['code'])
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
        self.cur.execute("SELECT lang_code FROM translations t INNER JOIN bots b ON t.bot_id=b.id WHERE b.name=%s "
                         + "AND t.state=0", (bot_name,))
        result = [lang[0] for lang in self.cur.fetchall()]
        return result

    def get_last_word_id(self):
        self.cur.execute("SELECT MAX(id) FROM words")
        result = [lang[0] for lang in self.cur.fetchall()][0]
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

    def get_strings(self, bot_name):
        self.cur.execute("SELECT s.id FROM strings s INNER JOIN bots b ON s.bot_id=b.id WHERE b.name=%s ORDER BY s.id",
                         (bot_name,))
        result = [item[0] for item in self.cur.fetchall()]
        return result

    def get_word(self, string_id, transl_id):
        self.cur.execute("SELECT value, id FROM words WHERE string_id=%s AND translation_id=%s",
                         (string_id, transl_id))
        result = [item[0] for item in self.cur.fetchall()]
        return result

    def get_bot_owner(self, bot_name):
        self.cur.execute("SELECT owner_id FROM bots WHERE name=%s", (bot_name,))
        result = self.cur.fetchall()[0][0]
        return result

    def get_words(self, string_id, transl_id):
        self.cur.execute(
            "SELECT w.value, w.id, COUNT(c.user_id), u.username, u.id FROM words w LEFT JOIN confirmations c ON"
            + " w.id=c.word_id INNER JOIN users u ON w.creator_id=u.id WHERE w.string_id=%s AND"
            + " w.translation_id=%s GROUP BY w.id ORDER BY u.id", (string_id, transl_id))
        result = [item[0:5] for item in self.cur.fetchall()]
        return result

    def get_translation(self, bot_name, lang):
        self.cur.execute("SELECT t.id FROM translations t INNER JOIN bots b ON t.bot_id=b.id WHERE t.lang_code=%s AND"
                         + " b.name=%s", (lang, bot_name))
        items = self.cur.fetchall()
        result = None if len(items) == 0 else items[0][0]
        return result

    def get_conf_stats(self, user_id, transl_id):
        self.cur.execute(
            "SELECT COUNT(w.creator_id), w.creator_id FROM confirmations c INNER JOIN words w ON " +
            "c.word_id=w.id WHERE c.user_id=%s AND w.translation_id=%s GROUP BY w.creator_id", (user_id, transl_id))
        result = {item[1]: item[0] for item in self.cur.fetchall()}
        return result

    def get_own_words(self, user_id, transl_id):
        self.cur.execute("SELECT COUNT(id) FROM words WHERE translation_id=%s AND creator_id=%s", (transl_id, user_id))
        result = self.cur.fetchall()[0][0]
        return result

    def rollback(self):
        self.con.rollback()

    def __del__(self):
        self.con.close()
