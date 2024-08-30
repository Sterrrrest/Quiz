import logging
import requests
import time
import telegram
import random
import redis

from environs import Env
from functools import partial

from telegram import Update, ForceReply, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, RegexHandler, ConversationHandler

from main import get_quiz

logger = logging.getLogger(__name__)

NEW_QUESTION, CHOOSING, ANSWER_ATTEMPT, GIVE_UP = range(4)


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    custom_keyboard = [['Да']]

    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)

    update.message.reply_markdown_v2(
        fr'Пссс {user.mention_markdown_v2()}\!, хочешь вопрос?',
        reply_markup=reply_markup,
    )
    return NEW_QUESTION


def handle_new_question_request(red, update, context):
    custom_keyboard = [['Сдаться'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    quiz = get_quiz()
    question = random.choice(list(quiz.keys()))

    context.bot.send_message(chat_id=update.effective_chat.id, text=question, reply_markup=reply_markup)
    red.set(update.effective_chat.id, question)

    return ANSWER_ATTEMPT


def handle_solution_attempt(red, update, context):
    custom_keyboard = [['Новый вопрос'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    custom_keyboard_loose = [['Новый вопрос', 'Сдаться'],
                             ['Мой счет']]
    reply_markup_loose = telegram.ReplyKeyboardMarkup(custom_keyboard_loose)
    full_answer = get_quiz().get(red.get(update.effective_chat.id))
    answer = full_answer.split('\n')[1].split('(')[0]

    if update.message.text == answer:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Siiiii Senor. Try again?', reply_markup=reply_markup)
        return NEW_QUESTION

    if update.message.text != answer and update.message.text != 'Новый вопрос' and update.message.text != 'Сдаться':
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='Неправильно… Попробуешь ещё раз?', reply_markup=reply_markup_loose)

        return ANSWER_ATTEMPT


def handle_give_up(red, update, context):
    custom_keyboard = [['Новый вопрос'],
                       ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    full_answer = get_quiz().get(red.get(update.effective_chat.id))
    context.bot.send_message(chat_id=update.effective_chat.id, text=full_answer, reply_markup=reply_markup)

    return NEW_QUESTION


def main():

    env = Env()
    env.read_env()

    tg_token = env.str('TG_TOKEN')
    db_host = env.str('DB_HOST')
    db_port = env.str('DB_PORT')
    db_password = env.str('DB_PASSWORD')

    updater = Updater(token=tg_token)
    dp = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    red = redis.Redis(host=db_host,
                      port=db_port,
                      password=db_password,
                      decode_responses=True,
                      )

    handle_new_question_request_bd = partial(handle_new_question_request, red)
    handle_solution_attempt_bd = partial(handle_solution_attempt, red)
    handle_give_up_bd = partial(handle_give_up, red)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            NEW_QUESTION: [RegexHandler('^(Новый вопрос|Да)$', handle_new_question_request_bd)],

            ANSWER_ATTEMPT: [RegexHandler('^(Сдаться)$', handle_give_up_bd, pass_user_data=True),
                             MessageHandler(Filters.text, handle_solution_attempt_bd, pass_user_data=True)],
        },
        fallbacks=[MessageHandler(Filters.text, handle_give_up_bd, pass_user_data=True)]
    )

    while True:
        try:
            dp.add_handler(conv_handler)

            updater.start_polling()
            updater.idle()

        except Exception as e:
            print('Error', e)
            time.sleep(60)
        except requests.ConnectionError:
            time.sleep(30)


if __name__ == '__main__':
    main()
