import logging
import requests
import time
import random
import vk_api
import redis

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from main import get_quiz

from functools import partial
from vk_api.longpoll import VkLongPoll, VkEventType
from environs import Env

logger = logging.getLogger("Debug")


def new_request(red, event, vk_api):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)

    question = random.choice(list(get_quiz().keys()))

    vk_api.messages.send(user_id=event.user_id,
                         random_id=random.randint(1, 1000),
                         keyboard=keyboard.get_keyboard(),
                         message=question)

    red.set(event.user_id, question)


def get_response(red, event, vk_api):

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)

    full_answer = get_quiz().get(red.get(event.user_id)).split('\n')[1]
    answer = full_answer.split('(')[0]

    if event.text == "Новый вопрос":
        new_request(red, event, vk_api)

    if event.text == "Сдаться":
        vk_api.messages.send(user_id=event.user_id,
                             random_id=random.randint(1,1000),
                             keyboard=keyboard.get_keyboard(),
                             message=full_answer)

    if event.text != "Новый вопрос" and event.text != "Сдаться":
        if event.text == answer or event.text == full_answer:
            keyboard = VkKeyboard(one_time=True)
            keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
            vk_api.messages.send(user_id=event.user_id,
                                 random_id=random.randint(1, 1000),
                                 keyboard=keyboard.get_keyboard(),
                                 message='Siiiii Senor. One more?')
        else:
            vk_api.messages.send(user_id=event.user_id,
                                 random_id=random.randint(1, 1000),
                                 keyboard=keyboard.get_keyboard(),
                                 message='Неправильно… Попробуешь ещё раз?')


def main():

    env = Env()
    env.read_env()

    vk_token = env.str('VK_TOKEN')
    vk_session = vk_api.VkApi(token=vk_token)
    longpoll = VkLongPoll(vk_session)

    vk_api_session = vk_session.get_api()

    db_host = env.str('DB_HOST')
    db_port = env.str('DB_PORT')
    db_password = env.str('DB_PASSWORD')

    red_vk = redis.Redis(host=db_host, port=db_port, password=db_password, decode_responses=True)

    bot_talk = partial(get_response, red_vk)

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    bot_talk(event, vk_api_session)
        except Exception as e:
            print('Error', e)
            time.sleep(60)
        except requests.ConnectionError:
            time.sleep(30)


if __name__ == "__main__":
    main()
