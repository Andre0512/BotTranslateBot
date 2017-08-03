#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from telegram import ReplyKeyboardMarkup, ForceReply, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from BotTranslateBot import Database
import ReadYaml
import json
import os


def get_lang_keyboard(chat_data):
    keyboard = [['qw', 'e', 'r', 't', 'y', 'u', 'i', 'op'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'kl'],
                ['z', 'x', 'c', 'v', 'b', 'n', 'm']]
    keyboard = [[InlineKeyboardButton(col, callback_data='langkeyboard_' + col) for col in row] for row in keyboard]
    last = []
    if 'bot_lang' in chat_data and chat_data['bot_lang']:
        last = last + [InlineKeyboardButton('✔️ ' + strings[chat_data['lang']]['done'], callback_data='langchoosen'),
                       InlineKeyboardButton('❌ ' + chat_data['bot_lang'][-1],
                                            callback_data='langdelete_' + chat_data['bot_lang'][-1])]
    last = last + [InlineKeyboardButton('❌ ' + strings[chat_data['lang']]['cancel'], callback_data='exitadding')]
    keyboard.append(last)
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
    db = Database(cfg)
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
    db = Database(cfg)
    chat_data['bot_lang'] = chat_data['bot_lang'] + [lang_code] if 'bot_lang' in chat_data else [lang_code]
    msg = strings[chat_data['lang']]['add_more'].replace("@done", '✔️ ' + strings[chat_data['lang']]['done'])
    update.message.edit_text(
        get_adding_text(chat_data, add=msg), reply_markup=get_lang_keyboard(chat_data),
        parse_mode=ParseMode.MARKDOWN)


def ask_for_strings(form, update, chat_data):
    chat_data['format'] = form
    add = strings[chat_data['lang']]['add_ask'] + ' 😏\n'
    if form == "mono":
        eg_yaml = '```´\nen:\n  greeting: Hello\n  state: "How are you?"```'
        eg_json = '```\n{\n  "en":\n    {\n      "greeting": "Hello",\n      "state": "How are you?"\n    }\n}```'
    else:
        eg_yaml = '```\ngreeting: Hello\nstate: "How are you?"```'
        eg_json = '```\n{\n  "greeting": "Hello",\n  "state": "How are you?"\n}```'
    add = add + strings[chat_data['lang']]['add_format'].replace("@examples",
                                                                 "\n*-YAML*\n@eg_yaml\n*-JSON*\n@eg_json")
    add = add.replace("@eg_yaml", eg_yaml).replace("@eg_json", eg_json)
    add = add + '\n' + strings[chat_data['lang']]['add_pos'] + ' ☺️'
    if form == 'poli':
        add = add + '\n\n' + strings[chat_data['lang']]['add_lang'].replace('@language', chat_data['bot_languages'][
            chat_data['bot_lang'][0]][1] + ' (' + chat_data['bot_languages'][chat_data['bot_lang'][0]][
                                                                                0] + ')') + ' ⬇️'
        chat_data['lang_read'] = 0
    update.callback_query.message.edit_text(get_adding_text(chat_data, add=add), parse_mode=ParseMode.MARKDOWN)
    chat_data["mode"] = "get_file"


def handle_file(bot, update, chat_data):
    file_type = update.message.document.file_name.split(".")[-1]
    file_name = str(update.message.from_user.id) + "_" + update.message.document.file_name
    if file_type in ["json", "yaml"]:
        file_id = bot.getFile(update.message.document.file_id)
        file_id.download(custom_path=os.path.join(os.path.dirname(__file__), "downloads/") + file_name)
        msg = strings[chat_data['lang']]['add_receiv'].replace("@filename",
                                                               "`" + update.message.document.file_name + "`")
        message_id = update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
        read_string_file(file_name, msg, message_id, bot, chat_data, update.message.from_user.id)


def add_bot(update, lang):
    msg = strings[lang]['add_cmd']
    msg = msg.replace('@example', '`AgeCalculatorBot`')
    update.message.reply_text(msg, reply_markup=ForceReply(), parse_mode=ParseMode.MARKDOWN)


def set_bot_name(update, lang, chat_data, db):
    bot_name = update.message.text[1:] if update.message.text[:1] == '@' else update.message.text
    if re.match('^[a-zA-Z0-9_-]{5,64}$', bot_name):
        status = db.insert_bot(bot_name, update.message.from_user.id)
        if not status:
            link = 'https://t.me/' + cfg['bot']['name'] + '?start=' + bot_name
            msg = strings[chat_data['lang']]['add_name_err2']
            msg = msg.replace('@name', '@' + bot_name).replace('@link', link).replace('@owner',
                                                                                      '@' + cfg['bot']['owner_name'])
            update.message.reply_text(msg)
            return
        chat_data['bot_name'] = bot_name
        update.message.reply_text(
            get_adding_text(chat_data, strings[lang]['add_answ'] + '\n' + strings[chat_data['lang']]['add_hint']),
            reply_markup=get_lang_keyboard(chat_data),
            parse_mode=ParseMode.MARKDOWN)
    else:
        update.message.reply_text(
            strings[chat_data['lang']]['add_name_err'] + '\n' + strings[chat_data['lang']]['add_again'] + ' 😬',
            reply_markup=ForceReply())


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
        read_string_file(file_name, msg, message_id, bot, chat_data, update.message.from_user.id)
    else:
        msg = strings[chat_data['lang']]['add_err'] + ' 😅' + '\n\n' + strings[chat_data['lang']]['add_again']
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ ' + strings[chat_data['lang']]['cancel'], callback_data='exitadding')]])
        update.message.reply_text(msg, reply_markup=keyboard)


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


def read_string_file(file_name, msg, message_id, bot, chat_data, user_id):
    state = True
    data = None
    file_type = file_name.split(".")[-1]
    if file_type == "json":
        data, state = read_json("downloads/" + file_name)
    elif file_type == "yaml":
        data, state = ReadYaml.get_yml("downloads/" + file_name)
        state = re.sub('\"[^"]*\"', 'file', state) if not state is True else state
    if not state is True:
        msg = msg + "\n\n" + strings[chat_data['lang']]['error'] + " ☹️\n`" + state + "` " + '\n\n' + \
              strings[chat_data['lang']]['add_again']
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ ' + strings[chat_data['lang']]['cancel'], callback_data='exitadding')]])
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        return
    else:
        msg = msg + "\n\n" + file_type.upper() + strings[chat_data['lang']]['add_file'] + " ✅"
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              parse_mode=ParseMode.MARKDOWN)
    bot_lang = 0 if not 'lang_read' in chat_data else chat_data['lang_read']
    if not chat_data["format"] == "mono":
        str_list = list(data.keys())
        db = Database(cfg)
        if bot_lang == 0:
            db.insert_strings(chat_data["bot_name"], str_list)
            msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_strings'] + " ✅"
            bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                                  parse_mode=ParseMode.MARKDOWN)
        db.insert_words(data, chat_data["bot_lang"][bot_lang], chat_data["bot_name"], user_id)
        language = chat_data['bot_languages'][chat_data['bot_lang'][bot_lang]][1] + ' (' + \
                   chat_data['bot_languages'][chat_data['bot_lang'][bot_lang]][0] + ')'
        msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_words'].replace("@lang",
                                                                                                        language) + " ✅"
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              parse_mode=ParseMode.MARKDOWN)
        if chat_data['format'] == "poli":
            if len(chat_data['bot_lang']) > bot_lang + 1:
                chat_data['lang_read'] = chat_data['lang_read'] + 1
                lango = chat_data['bot_languages'][chat_data['bot_lang'][chat_data['lang_read']]][1] + ' (' + \
                        chat_data['bot_languages'][chat_data['bot_lang'][chat_data['lang_read']]][0] + ')'
                add = '\n\n' + strings[chat_data['lang']]['add_lango'].replace('@language', lango) + ' ⬇️'
                bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg + add,
                                      parse_mode=ParseMode.MARKDOWN)
                return
    else:
        str_list = list(next(iter(data.values())))
        db = Database(cfg)
        db.insert_strings(chat_data["bot_name"], str_list)
        msg = msg + '\n\n' + str(len(str_list)) + " " + strings[chat_data['lang']]['add_strings'] + " ✅"
        bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                              parse_mode=ParseMode.MARKDOWN)
        for key, value in data.items():
            try:
                language = chat_data['bot_languages'][key][1] + ' (' + chat_data['bot_languages'][key][0] + ')'
            except KeyError:
                msg = msg + '\n\n' + strings[chat_data['lang']]['add_val_err'].replace('@lang', '*' + key + '*') + ' ❌'
                msg = msg + '\n\n' + strings[chat_data['lang']]['add_again']
                bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                                      parse_mode=ParseMode.MARKDOWN)
                return
            db.insert_words(value, key, chat_data["bot_name"], user_id)
            msg = msg + '\n\n' + str(len(list(value.keys()))) + " " + strings[chat_data['lang']][
                'add_words'].replace("@lang",
                                     language) + " ✅"
            bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                                  parse_mode=ParseMode.MARKDOWN)
    link = 'https://t.me/' + cfg['bot']['name'] + '?start=' + chat_data['bot_name']
    msg = msg + '\n\n' + strings[chat_data['lang']]['add_success'].replace("@botname", '@' + chat_data['bot_name']) \
          + " 😃🎉\n\n" + strings[chat_data['lang']]['link'] + '\n' + link + '\n' + strings[chat_data['lang']][
              'link_desc'] + ' ☺️'
    bot.edit_message_text(chat_id=message_id.chat.id, message_id=message_id.message_id, text=msg,
                          parse_mode=ParseMode.MARKDOWN)
    delete_adding_values(chat_data)


def delete_adding_values(chat_data):
    chat_data.pop("letter_one", None)
    chat_data.pop("letter_two", None)
    chat_data.pop("bot_lang", None)
    chat_data.pop("bot_name", None)
    chat_data.pop("bot_languages", None)
    chat_data.pop("mode", None)
    chat_data.pop("lang_read", None)


def reply_button(bot, update, chat_data, arg_one, arg_two):
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
        db = Database(cfg)
        db.insert_bot_language(chat_data['bot_name'], chat_data['bot_lang'])
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
    if arg_one == 'format':
        ask_for_strings(arg_two, update, chat_data)
    if arg_one == 'exitadding':
        update.callback_query.message.edit_text(strings[chat_data['lang']]['cancel_msg'] + ' ❌')
        cancel_adding(chat_data)
    if arg_one == 'langdelete':
        chat_data.pop("letter_one", None)
        chat_data.pop("letter_two", None)
        chat_data['bot_lang'] = chat_data['bot_lang'][:-1]
        update.callback_query.message.edit_text(
            get_adding_text(chat_data, add=strings[chat_data['lang']]['add_answ']),
            reply_markup=get_lang_keyboard(chat_data))


def cancel_adding(chat_data):
    db = Database(cfg)
    db.delete_bot(chat_data['bot_name'])
    delete_adding_values(chat_data)


def set_gloabl(config, all_strings):
    global cfg
    cfg = config
    global strings
    strings = all_strings
