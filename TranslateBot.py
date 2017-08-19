#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from telegram.ext.dispatcher import run_async
from telegram import ReplyKeyboardMarkup, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from Naked.toolshed.shell import muterun_js
from Database import Database


def get_std_keyboard(chat_data):
    keyboard = ReplyKeyboardMarkup(
        [['➕ ' + strings[chat_data['lang']]['add_bot'], '👤 ' + strings[chat_data['lang']]['my_profile']]],
        resize_keyboard=True)
    return keyboard


@run_async
def add_google_translation(chat_data, word, msg, msg_data, number, bot, transl_words, confirm, owner, db):
    result = "DEBUG\n"
    if not cfg["debug"]["windows"]:
        response = muterun_js(
            os.path.join(os.path.dirname(__file__), "google_translate.js") + ' ' + chat_data['flang'] + ' ' + chat_data[
                'tlang'] + ' "' + word + '"')
        if response.exitcode == 0:
            result = response.stdout.decode('utf-8')
            db.insert_word(result, chat_data['strings'][int(number)], chat_data['tlangid'], 0)
        else:
            result = response.stderr.decode('utf-8')
    msg = msg.replace("Übersetzen" + "...\n", result)
    bot.edit_message_text(chat_id=msg_data.chat.id, message_id=msg_data.message_id, text=msg,
                          parse_mode=ParseMode.MARKDOWN,
                          reply_markup=get_tr_keyboard(number, chat_data, transl_words, confirm, owner, active=True))


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
    msg = strings[chat_data['lang']]['tr_to'] + ' 😊\n' + strings[chat_data['lang']]['add_hint']
    update.callback_query.message.edit_text(get_start_text(chat_data, add=msg), reply_markup=get_search_keyboard(),
                                            parse_mode=ParseMode.MARKDOWN)


def start_translate_new(update, chat_data, edit=False):
    # chat_data['orginal_lang'] = 'uk'
    db = Database(cfg)
    user = update.callback_query.message.chat.first_name if edit else update.message.from_user.first_name
    language, flag, x = db.get_language(chat_data['orginal_lang'] if 'orginal_lang' in chat_data else chat_data['lang'])
    msg = strings[chat_data['lang']]['tr_greeting'].replace('@name', user + ' ✌️')
    msg = msg.replace('@bot_name', '@' + chat_data['bot'] if 'bot' in chat_data else 'Bots')
    lang_str = 'tr_lang_c' if edit else 'tr_lang'
    msg = msg + ' 🌏\n\n' + strings[chat_data['lang']][lang_str].replace('@lang', language) + ' ☺️\n'
    yes = '✔️ ' + strings[chat_data['lang']]['agree'] + ' ' + (flag if flag else '')
    no = '❌ ' + strings[chat_data['lang']]['tr_lang_no'] + ' 🗺'
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(yes, callback_data='langyes'), InlineKeyboardButton(no, callback_data='langno')]])
    if 'orginal_lang' in chat_data and not edit:
        msg = msg + '\nUnfortunately nobody has translated me into ' + language + \
              ' 😕\nIs it okay when I speak to you in English?'
    elif not edit:
        msg = msg + strings[chat_data['lang']]['tr_lang_fnd'].replace('@lang', language)
    if edit:
        update.callback_query.message.edit_text(msg)
    else:
        update.message.reply_text(msg, reply_markup=keyboard)


def get_search_keyboard():
    keyboard = [['qw', 'e', 'r', 't', 'y', 'u', 'i', 'op'], ['a', 's', 'd', 'f', 'g', 'h', 'j', 'kl'],
                ['z', 'x', 'c', 'v', 'b', 'n', 'm']]
    keyboard = [[InlineKeyboardButton(col, callback_data='searchkb_' + col) for col in row] for row in keyboard]
    return InlineKeyboardMarkup(keyboard)


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


def get_progress_bar(value, total):
    result = '█' * round(value / total * 16)
    result = result + round(16 - len(result)) * '▒'
    return result


def get_number_emoji(number):
    emoji_list = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    result = ''
    for x in str(number):
        result = result + emoji_list[int(x)]
    return result


def get_tr_keyboard(number, chat_data, transl_words, confirm, owner, active=False):
    keyboard = []
    for index, word_id in enumerate(transl_words):
        keyboard.append(InlineKeyboardButton((strings[chat_data['lang']]['sugg'] if owner != word_id[4] else
                                              '👨‍💻 ' + strings[chat_data['lang']]['original']) + ' ' + str(
            get_number_emoji(index + 1)), callback_data='confirm_' + str(word_id[1]) + ' ' + str(
            number + 1) if active else 'Wait'))
    keyboard.append(InlineKeyboardButton('Google 🗣', callback_data='google_' + str(number + 1) if active else 'Wait'))
    keyboard = [InlineKeyboardButton('✔️ ' + strings[chat_data['lang']]['sugg'] + ' ' + str(
        get_number_emoji(len(transl_words))), callback_data='confirm_' + str(transl_words[-1][1]) + ' ' + str(
        number + 1) if active else 'Wait')] if confirm else keyboard
    keyboard = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]
    keyboard.append([InlineKeyboardButton(('◀️ ' + strings[chat_data['lang']]['back']) if number > 0 else '',
                                          callback_data='translnav_' + str(number - 1) if active else 'Wait'),
                     InlineKeyboardButton(
                         (strings[chat_data['lang']]['skip'] + ' ▶️') if number < len(chat_data['strings']) - 1 else '',
                         callback_data='translnav_' + str(number + 1) if active else 'Wait')])
    keyboard.append([InlineKeyboardButton('✔️ ' + strings[chat_data['lang']]['done'],
                                          callback_data='transldone_' + str(number) if active else 'Wait')])
    return InlineKeyboardMarkup(keyboard)


def get_the_world(number):
    world = ['🌏', '🌍', '🌎']
    return world[number % 3]


def translate_text(update, chat_data, db, number, bot, first=False, confirm=False, add='', end=False):
    word = db.get_word(chat_data['strings'][number], chat_data['flangid'])[0]
    transl_words = db.get_words(chat_data['strings'][number], chat_data['tlangid'])
    owner = db.get_bot_owner(chat_data['bot'])
    if 'confirm_own' in chat_data and not confirm:
        chat_data.pop('confirm_own', None)
    # elif 'confirm_own' in chat_data:
    #    if transl_words[-1][0] in [transl_words[:][0] + google]
    google_exists = False
    google = "Übersetzen...\n"
    google_confirm = ''
    if len(transl_words) > 0 and transl_words[0][3] == 'google':
        google_exists = True
        google = transl_words[0][0]
        google_confirm = ' (' + str(transl_words[0][2]) + 'x👍)' if transl_words[0][2] > 0 else ''
        del transl_words[0]
    length = str(len(chat_data['strings']))
    msg = '@' + chat_data['bot'] + ' ' + strings[chat_data['lang']]['transl'] + ' ' + (
        str(number + 1) if (number + 1) > 9 else '0' + str(number + 1)) + '/' + (
              length if int(length) > 9 else '0' + length) + ' ' + get_the_world(number) + '\n' + get_progress_bar(
        number,
        len(
            chat_data[
                'strings'])) + '\n\n_' + word + '_' + '\n\n*Google Translate 🗣*' + google_confirm + '\n`' + google + '`'
    for index, string in enumerate(transl_words):
        msg = msg + '\n*' + (
            strings[chat_data['lang']]['sugg'] if owner != string[4] else '👨‍💻 ' + strings[chat_data['lang']][
                'original']) + '* ' + str(
            get_number_emoji(index + 1)) + (
                  ' (*' + str(string[2]) + '*x👍)' if string[2] > 1 else '') + '\n`' + string[0] + '`\n'
        # + ('\n\[' + strings[chat_data['lang']]['tr_by'] + ' @' + string[3] + ']' if string[3] else '')
    msg = msg + add
    keyboard = '' if end else get_tr_keyboard(number, chat_data, transl_words, confirm, owner, active=google)
    if first:
        msg_data = update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, action=ChatAction.TYPING,
                                             reply_markup=keyboard)
    else:
        msg_data = update.message.edit_text(msg, parse_mode=ParseMode.MARKDOWN, action=ChatAction.TYPING,
                                            reply_markup=keyboard)
    chat_data['mode'] = 'tr_' + str(number)
    if not google_exists:
        add_google_translation(chat_data, word, msg, msg_data, number, bot, transl_words, confirm, owner, db)


def have_translate_data(update, chat_data, bot):
    db = Database(cfg)
    language = db.get_language(chat_data['tlang'])
    chat_data['lang_to'] = language[0] + ' ' + language[1] if language[1] else language[0]
    msg = strings[chat_data['lang']]['tr_start'] + '\n' + strings[chat_data['lang']]['tr_instr'] + ' 😁'
    update.callback_query.message.edit_text(get_start_text(chat_data, add=msg))
    chat_data['strings'] = db.get_strings(chat_data['bot'])
    chat_data['flangid'] = db.get_translation(chat_data['bot'], chat_data['flang'])
    to_lang = db.get_translation(chat_data['bot'], chat_data['tlang'])
    if to_lang:
        chat_data['tlangid'] = to_lang
    else:
        db.insert_bot_language(chat_data['bot'], [chat_data['tlang']], 1)
        chat_data['tlangid'] = db.get_translation(chat_data['bot'], chat_data['tlang'])
    chat_data.pop('lang_from', None)
    chat_data.pop('lang_to', None)
    translate_text(update.callback_query, chat_data, db, 0, bot, first=True)


def manage_search_kb(update, chat_data, bot):
    lang_list = dict()
    db = Database(cfg)
    for first in chat_data['lone']:
        for second in chat_data['ltwo']:
            lang_list = dict(list(lang_list.items()) + list(db.search_language(first + second).items()))
    chat_data.pop('lone', None)
    chat_data.pop('ltwo', None)
    if len(list(lang_list)) > 1:
        keyboard = []
        for key, value in lang_list.items():
            keyboard = keyboard + [[InlineKeyboardButton(value[0], callback_data='tlang_' + key)]]
        msg = strings[chat_data['lang']]['tr_to_ask'] + ' 😅'
        keyboard = InlineKeyboardMarkup(keyboard)
        update.callback_query.message.edit_text(get_start_text(chat_data, add=msg), reply_markup=keyboard)
    elif len(list(lang_list)) == 1:
        chat_data['tlang'] = list(lang_list)[0]
        have_translate_data(update, chat_data, bot)
    else:
        msg = strings[chat_data['lang']]['tr_to_f'] + ' 😬\n' + strings[chat_data['lang']]['again']
        update.callback_query.message.edit_text(get_start_text(chat_data, add=msg),
                                                reply_markup=get_search_keyboard())


def get_tworow_keyboard(str_list, callback):
    keyboard = [InlineKeyboardButton(lang[0], callback_data=callback + lang[1]) for lang in str_list]
    keyboard = [keyboard[i:i + 2] for i in range(0, len(keyboard), 2)]
    return InlineKeyboardMarkup(keyboard)


def reply_button(bot, update, chat_data, arg_one, arg_two):
    if arg_one == 'langyes':
        if 'orginal_lang' in chat_data:
            db = Database(cfg)
            db.update_language(update.callback_query.message.chat.id, chat_data['lang'])
            chat_data.pop("orginal_lang", None)
        if 'bot' in chat_data:
            start_translation(update.callback_query, chat_data, edit=True)
        else:
            start_translate_new(update, chat_data, edit=True)
            update.callback_query.message.reply_text(
                strings[chat_data['lang']]['ask_action'] + ' ☺️',
                reply_markup=get_std_keyboard(chat_data))
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
            language, flag, x = db.get_language(lang)
            languages.append([language + ' ' + flag if flag else language, lang])
        keyboard = get_tworow_keyboard(languages, "langcho_")
        update.callback_query.message.edit_text(msg, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    elif arg_one == 'langcho':
        db = Database(cfg)
        db.update_language(update.callback_query.message.chat.id, arg_two)
        if 'bot' in chat_data:
            start(bot, update.callback_query, chat_data)
        else:
            start_translate_new(update, chat_data, edit=True)
            update.callback_query.message.reply_text(
                strings[chat_data['lang']]['ask_action'] + ' ☺️',
                reply_markup=get_std_keyboard(chat_data))
    elif arg_one == 'fromlang':
        chat_data['flang'] = arg_two
        choose_lang_to(update, chat_data)
    elif arg_one == 'searchkb':
        if 'lone' in chat_data:
            chat_data['ltwo'] = arg_two
            manage_search_kb(update, chat_data, bot)
        else:
            chat_data['lone'] = arg_two
    elif arg_one == 'tlang':
        chat_data['tlang'] = arg_two
        have_translate_data(update, chat_data, bot)
    elif arg_one == 'translnav':
        db = Database(cfg)
        if 'confirm_own' in chat_data:
            db.delete_word(chat_data['confirm_own'])
        translate_text(update.callback_query, chat_data, db, int(arg_two), bot)
    elif arg_one == 'confirm' or arg_one == 'google':
        db = Database(cfg)
        word_id = arg_two.split(' ')[0] if arg_one == 'confirm' else None
        number = int(arg_two.split(' ')[1]) if arg_one == 'confirm' else int(arg_two)
        string_id = chat_data['strings'][number - 1]
        db.insert_confirmation(word_id, string_id, update.callback_query.message.chat.id, chat_data['tlangid'])
        if number >= len(chat_data['strings']):
            translation_done(bot, update, chat_data, number - 1, add=strings[chat_data['lang']]['tr_end'] + ' 🎉\n\n')
        else:
            translate_text(update.callback_query, chat_data, db, number, bot)
    elif arg_one == 'transldone':
        translation_done(bot, update, chat_data, arg_two)


def calc_translation_stats(user_id, transl_id, total):
    db = Database(cfg)
    stats = db.get_conf_stats(user_id, transl_id)
    own_words = db.get_own_words(user_id, transl_id)
    google = str(round(stats[0] / total * 100, 2)) if 0 in stats else str(0.00)
    own = str(round(stats[user_id] / total * 100, 2)) if user_id in stats else str(0.00)
    msg = str(own_words) + " Strings vorgeschlagen\n"
    msg = msg + google + '% Google\n' + own + '% Eigene\n'
    skipped = sum(stats.values())
    stats.pop(user_id, None)
    stats.pop(0, None)
    others = sum(stats.values())
    msg = msg + str(round(others / total * 100, 2)) + '% Andere\n' if others > 0 else msg
    msg = msg + str(round((total - skipped) / total * 100, 2)) + '% Übersprungen\n' if skipped > 0 else msg
    return msg


def translation_done(bot, update, chat_data, arg_two, add=''):
    translate_text(update.callback_query, chat_data, Database(cfg), int(arg_two), bot, end=True)
    msg = calc_translation_stats(update.callback_query.message.chat.id, chat_data['tlangid'], len(chat_data['strings']))
    chat_data.pop('bot', None)
    chat_data.pop('flang', None)
    chat_data.pop('tlang', None)
    chat_data.pop('mode', None)
    chat_data.pop('strings', None)
    chat_data.pop('tlangid', None)
    chat_data.pop('flangid', None)
    msg = add + strings[chat_data['lang']]['tr_thanks'] + ' 💙\n\n' + msg
    update.callback_query.message.reply_text(msg, reply_markup=get_std_keyboard(chat_data))


def set_global(config, all_strings):
    global cfg
    cfg = config
    global strings
    strings = all_strings
