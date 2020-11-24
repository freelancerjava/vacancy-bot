
import logging
# from systemd.journal import JournaldLogHandler

import time

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import re
import requests
import json


api_url = "http://localhost:4444/"
token = "1271620572:AAFRTniz3nT3_pHtaX-rP4Im1V3aG_GTf_I"


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# optionally set the logging level
logger.setLevel(logging.DEBUG)

START, END, PHOTO, OPEN_BOOK, ACTION, RABOTA, PREDLOJ, VOPROS, SEND_ID, CANCEL = range(
    10)

message_from_user = {}

order_type = {
    'Работа': 1,
    'Вопрос': 2,
    'Предложение': 3
}


def start(update, context):

    user = update.effective_user

    update.message.reply_text(f'Здраствуйте уважавемый {user.username} 👋')

    reply_keyboard = [['Книжка вопросов и предложений 📖']]

    update.message.reply_text('Хотите написать владельцу предприятия?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),)

    return OPEN_BOOK


def openBook(update, context):

    update.message.reply_text('Введите ID предприятия 🏤 ?',
                              reply_markup=ReplyKeyboardRemove())

    data={
        "username": update.message.from_user.username,
        "phone": None,
        "chat_id": update.message.chat.id
    }

    print(data)

    return SEND_ID


def sendID(update, context):

    try:
        message_from_user['ID'] = int(update.message.text)
    except:
        return openBook(update, context)

    # update.message.reply_text('Ждраствуйте уважаемый ', update.effective_user)
    reply_keyboard = [['Работа 😡', 'Вопрос 😊'], ['Предложение 😎']]

    update.message.reply_text('Выберите действие ☝️',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),)

    return ACTION


def action(update, context):

    message = update.message.text

    if re.search('^Работа*', message):
        message_from_user['type'] = "Работа"
        update.message.reply_text(
            'Оставьте нам свои контакты и Отправьте резюме:', reply_markup=ReplyKeyboardRemove())
        return RABOTA
    elif re.search('^Вопрос*', message):
        message_from_user['type'] = "Вопрос"
        update.message.reply_text(
            '🤩 Можете оставить свой вопрос:', reply_markup=ReplyKeyboardRemove())
        return VOPROS
    elif re.search('^Предложение*', message):
        message_from_user['type'] = "Предложение"
        update.message.reply_text(
            '🧐 Напишите нам Ваши предложения:', reply_markup=ReplyKeyboardRemove())
        return VOPROS

    return CANCEL


def rabota(update, context):
    message = update.message.text
    message_from_user['text'] = message
    update.message.reply_text('Отправьте фото если имеется 🏞', reply_markup=ReplyKeyboardMarkup(
        [['Нет фото']], resize_keyboard=True))
    return PHOTO


def vopros(update, context):
    message = update.message.text
    message_from_user['text'] = message
    update.message.reply_text(
        'Спасибо за Ваш запрос! 👍')
    return end(update, context)


def photo(update, context):
    user = update.message.from_user
    photo_file = update.message.photo[-1].get_file()
    if photo_file != None:
        photo_file.download('user_photo-{}.jpg'.format(time.time()))
        logger.info("Photo of %s: %s", user.first_name, 'user_photo.jpg')
        message_from_user['photo'] = photo_file
    else:
        message_from_user['photo'] = ''
        return skip_photo(update, context)

    return end(update, context)


def skip_photo(update, context):
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)

    return end(update, context)


def end(update, context):
    
    data = {
        "text": message_from_user["text"],
        "visitor": update.message.from_user.id,
        "type": order_type[message_from_user["type"]]
    }

    print(data)

    update.message.reply_text(
        f'Вы оставили следуещее заявление:\n'
        f'🏤 ID предприятия: {message_from_user["ID"]}\n'
        f'📬 Тип запроса: {message_from_user["type"]}\n'
        f'💬 Текст запроса: {message_from_user["text"]}\n'
        f'Уважаемый {update.effective_user.username}, на Ваш запрос ответим в кратчайшие сроки 👌\n',
        reply_markup=ReplyKeyboardMarkup([['◀️ Назад']], resize_keyboard=True)
    )

    return START


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Пока!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    updater = Updater(
        f'{token}', use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(
            Filters.regex("Книжка вопросов и предложений"), start)],
        states={
            OPEN_BOOK: [MessageHandler(Filters.text, openBook)],
            SEND_ID: [MessageHandler(Filters.text, sendID)],
            ACTION: [MessageHandler(Filters.text, action)],
            RABOTA: [MessageHandler(Filters.text, rabota)],
            PREDLOJ: [MessageHandler(Filters.text, action)],
            VOPROS: [MessageHandler(Filters.text, vopros)],
            PHOTO: [
                MessageHandler(Filters.photo, photo),
                CommandHandler('skip', start),
                MessageHandler(Filters.regex("^(Нет фото)$"), end)],
            CANCEL: [CommandHandler('cancel', cancel)],
            START: [MessageHandler(Filters.text, start),
                    CommandHandler('start', start),
                    MessageHandler(Filters.regex("^(Назад)$"), end)],
            END: [MessageHandler(Filters.text, end), CommandHandler('end', end)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
