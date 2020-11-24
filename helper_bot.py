
import logging
# from systemd.journal import JournaldLogHandler

import time

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import re
import requests
import json


api_url = "http://fork.uz:4444/"
token = "1416576907:AAFlPluGEQTcCJtAVAx2o00GvGiqEMuxIpo"


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# optionally set the logging level
logger.setLevel(logging.DEBUG)

START, END, PHOTO, OPEN_BOOK, ACTION, JALOBA, PREDLOJ, OTZYV, SEND_ID, CANCEL = range(
    10)

message_from_user = {}

order_type = {
    'Жалоба': 1,
    'Предложение': 2,
    'Отзыв': 3
}


def start(update, context):

    user = update.effective_user

    update.message.reply_text(f'Здраствуйте уважавемый {user.username} 👋')

    reply_keyboard = [['Книжка жалоб и предложений 📖']]

    update.message.reply_text('Хотите написать владельцу предприятия?',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),)

    return OPEN_BOOK


def openBook(update, context):

    # print(update)
    # logger.info(update)

    update.message.reply_text('Введите ID предприятия 🏤 ?',
                              reply_markup=ReplyKeyboardRemove())

    res = requests.post(f'{api_url}/visitors/{update.message.from_user.username}', data={
        "username": update.message.from_user.username,
        "phone": None,
        "chat_id": update.message.chat.id
    })

    # print(res.text)

    return SEND_ID


def sendID(update, context):

    try:
        message_from_user['ID'] = int(update.message.text)
    except:
        return openBook(update, context)

    # update.message.reply_text('Ждраствуйте уважаемый ', update.effective_user)
    reply_keyboard = [['Жалоба 😡', 'Отзыв 😊'], ['Предложение 😎']]

    update.message.reply_text('Выберите действие ☝️',
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True),)

    return ACTION


def action(update, context):

    message = update.message.text

    if re.search('^Жалоба*', message):
        message_from_user['type'] = "Жалоба"
        update.message.reply_text(
            '🤧 Введите причину Вашего недовольствия:', reply_markup=ReplyKeyboardRemove())
        return JALOBA
    elif re.search('^Отзыв*', message):
        message_from_user['type'] = "Отзыв"
        update.message.reply_text(
            '🤩 Напишите нам Ваши впечатления:', reply_markup=ReplyKeyboardRemove())
        return OTZYV
    elif re.search('^Предложение*', message):
        message_from_user['type'] = "Предложение"
        update.message.reply_text(
            '🧐 Напишите нам Ваши предложения:', reply_markup=ReplyKeyboardRemove())
        return OTZYV

    return CANCEL


def jaloba(update, context):
    message = update.message.text
    message_from_user['text'] = message
    update.message.reply_text('Отправьте фото если имеется 🏞', reply_markup=ReplyKeyboardMarkup(
        [['Нет фото']], resize_keyboard=True))
    return PHOTO


def otzyv(update, context):
    message = update.message.text
    message_from_user['text'] = message
    update.message.reply_text(
        'Спасибо за вклад для внесенный для продвижения сервиса! 👍')
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
    gq = """
            query{
                visitors(where: {username: "%s"}){
                    username
                    id
                }
            }
        """ % (update.message.from_user.username)

    res = requests.post(f'{api_url}/graphql', data={
        "query": gq
    })

    resJson = res.json()

    # print(resJson)

    id = resJson["data"]["visitors"][0]["id"]
    data = {
        "text": message_from_user["text"],
        "visitor": id,
        "type": order_type[message_from_user["type"]]
    }

    res = requests.post(f'{api_url}/orders', data=data)

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
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    updater = Updater(
        f'{token}', use_context=True)

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(
            Filters.regex("Книжка жалоб и предложений"), start)],
        states={
            OPEN_BOOK: [MessageHandler(Filters.text, openBook)],
            SEND_ID: [MessageHandler(Filters.text, sendID)],
            ACTION: [MessageHandler(Filters.text, action)],
            JALOBA: [MessageHandler(Filters.text, jaloba)],
            PREDLOJ: [MessageHandler(Filters.text, action)],
            OTZYV: [MessageHandler(Filters.text, otzyv)],
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
