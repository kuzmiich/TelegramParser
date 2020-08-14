import time
import configparser
from datetime import date, datetime
import asyncio

from telethon.sync import TelegramClient
from telethon import connection
# прокси
import socks
# классы для работы с каналами
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, PeerChannel
# класс для работы с сообщениями
from telethon.tl.functions.messages import GetHistoryRequest


async def dump_all_participants(chat_id, client):
    URL = chat_id
    try:
        channel = await client.get_entity(URL)
    except (ValueError, UnboundLocalError) as err:
        print(err)
        return
    else:
        offset_user = 0  # номер участника, с которого начинается считывание
        limit_user = 100  # максимальное число записей, передаваемых за один раз

        all_participants = []  # список всех участников канала
        filter_user = ChannelParticipantsSearch('')

        while True:
            try:
                participants = await client(GetParticipantsRequest(channel, filter_user, offset_user,
                                                                   limit_user, hash=0))
            except BaseException as e:
                print(e)
                return
            if not participants.users:
                break
            all_participants.extend(participants.users)
            offset_user += len(participants.users)

        all_users_details = {}

        for participant in all_participants:
            all_users_details["id"] = participant.id
            all_users_details["first_name"] = participant.first_name
            all_users_details["last_name"] = participant.last_name
            all_users_details["user"] = participant.username
            all_users_details["phone"] = participant.phone
            all_users_details["is_bot"] = participant.bot
            
        return all_users_details
    

def check_post_type(message, gif, photo, video, voice):
    if message:
        return "text"
    elif gif:
        return "Gif"
    elif photo:
        return "Photo"
    elif video:
        return "Video"
    elif voice:
        return "Voice"


async def dump_messages(chat_id, time_period, client):
    URL = chat_id
    try:
        channel = await client.get_entity(URL)
        print("ID - ", channel.id)
    except (ValueError, UnboundLocalError) as err:
        print(err)
        return
    else:
        offset_msg = 0  # номер записи, с которой начинается считывание
        limit_msg = 1000  # максимальное число записей, передаваемых за один раз
        count_attr = 4  # количество атрибутов

        all_messages = {}  # список всех сообщений
        total_messages = 0
        total_count_limit = 0  # поменяйте это значение, если вам нужны не все сообщения

        while True:
            history = await client(GetHistoryRequest(
                peer=channel,
                offset_id=offset_msg,
                offset_date=None, add_offset=0,
                limit=limit_msg, max_id=0, min_id=0,
                hash=0))

            if not history.messages:
                break
            messages = history.messages

            i = 1
            time_now = time.time()
            for message in messages:
                unix_data = datetime.timestamp(message.date)
                if time_period <= time_now - unix_data:
                    break
                all_messages[str(i) + ".Id"] = message.id
                all_messages[str(i) + ".Time"] = unix_data
                all_messages[str(i) + ".Type"] = check_post_type(message.message, message.gif,
                                                                 message.photo, message.video, message.voice)
                all_messages[str(i) + ".Message"] = message.message
                i += 1

            offset_msg = messages[len(messages) - 1].id
            total_messages = len(all_messages)

            if total_count_limit != 0 and total_messages >= total_count_limit:
                break

            return all_messages


def clnt():
    # Считываем учетные данные
    # config = configparser.ConfigParser()
    # config.read("config.ini")
    # Присваиваем значения внутренним переменным
    # api_id   = config['Telegram']['api_id']
    # api_hash = config['Telegram']['api_hash']
    # username = config['Telegram']['username']

    # proxy_server = 'godaddy.com'
    # proxy_port = 18726
    # proxy_key = '166.62.80.198'
    # proxy = (proxy_server, proxy_port, proxy_key)
    # connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
    #                         proxy = proxy
    api_id = "1735329"
    api_hash = "86a59fa728d061e59e6f5dd68408a44f"
    username = "username"
    client = TelegramClient(username, api_id, api_hash)
    return client


def parse(chat_id, time_period):
    client = clnt()
    is_connect = False
    try:
        client.start()
    except ConnectionError as err:
        print("Ошибка, подключитесь к интернету!")
    else:
        is_connect = True
    
    if is_connect:
        with client:
            lst_result = []
            dict_messages = client.loop.run_until_complete(dump_messages(chat_id, time_period, client))
            lst_result.append(dict_messages)
            INPUT = input("Введите 0, если вам нужно получить данные о пользователях\nРаботает, если есть доступ к каналу или он публичный\n")
            if int(INPUT) == 0:
                dict_participants = client.loop.run_until_complete(dump_all_participants(chat_id, client))
                lst_result.append(dict_participants)

            return lst_result

if __name__ == "__main__":
    chat_id = input("Введите ссылку на канал или чат: ")
    time_period = int(input("Введите количество секунд: "))
    print(parse(chat_id, time_period))
