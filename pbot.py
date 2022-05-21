#!/bin/env python3
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import traceback
import threading
import sys


token = open('token').read().replace('\n', '')
longpoll = open('longpoll').read().replace('\n', '')
print('Подключаемся к токену', token, '\b...')
vk_session = vk_api.VkApi(token = token)
vk = vk_session.get_api()
print('Лонгполлируем группу номер', longpoll, '\b...')
vk_longpoll = VkBotLongPoll(vk_session, longpoll)

peer = None

def make_table(tabname):
    """Reads a table
    Arguments:
    tabname -- table name : str"""
    print('Читаем таблицу', tabname, '\b...')
    with open(tabname) as tabfile:
        tabfile = tabfile.read().splitlines()
    tabout = dict()
    for line in tabfile:
        line.replace("\n", "")
        key, response = line.split(':')
        try:
            key = int(key)
        except ValueError:
            pass
        if response != None or key != None:
            tabout[key] = response
        elif response == None:
            tabout[key] = ''
        elif key == None:
            pass
    print('Прочтена')
    return tabout

localization = make_table('localization.txt')
commands = make_table('commands.txt')

permissions = open('./diplo/permissions.txt')
moves = open('./diplo/moves.txt', 'rw')


def read_msg():
    """Reads a message from longpoll and processes it"""
    for event in vk_longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj['message']
            user = msg['peer_id']
            print('Получено от:', user, '\b:', msg['text']) 
            if not msg['text']:
                print('Пустое сообщение от:', user)
                write_msg('Хватит присылать этот кал', user)
            else:
                if (msg['text'][0] == '/'):
                    user_command(msg['text'][1::], user)

def send_localized(locnum, user = -1):
    """Sends a message specified in the localization.txt file.
    locnum -- localization id : int
    user -- user vk id : int"""
    global peer
    if user == -1:
        user = peer
    msg = open(localization[locnum], 'r').read()
    write_msg(msg, user)

def write_msg(msg, user = -1):
    """Sends message to a user. If no user specified, then sends it to the peer.
    Arguments:
    msg -- Message : str
    user -- Optional user vk id : int"""
    global peer
    if user == -1:
        user = peer
    print('Отправлено к:', user, '\b:', msg)
    vk.messages.send(
            message = msg,
            random_id = get_random_id(),
            peer_id = user)

def user_command(uin, user = -1): 
    """Reads a user command, processes it in accordance with the commands table
    Arguments:
    uin -- Input string (command with arguments) : str
    user -- User vk id : int"""
    if user == -1:
        user = peer
    uin = uin.split()
    comkey = uin[0].lower()
    try:
        command = commands[comkey]
        exec(command)
        print('Выполнена команда', command, 'vk id:', user)
    except:
        print('Не удалось выполнить команду', comkey, 'vk id:', user)
        write_msg("Дедушка тебя не понимает", user)
        print(traceback.format_exc())

def console_command(uin):
    """ Processes console commands
    Arguments:
    uin -- Input string (command with arguments) : str"""
    global peer
    try:
        com = uin[0]
        #Send message to peer
        if com == 'w':
            try:
                write_msg(' '.join(uin[1:]))
            except IndexError:
                print('Неверное число аргументов')
        #Exit command
        elif com == 'q':
            print('Останавливаем')
            sys.exit()
        #Set a new peer
        elif com == 's':
            peer = uin[1]
            print('Собеседник задан:', peer)
        #Execute user command
        elif com == 'e':
            print('Executing', uin[1] + '...')
            user_command(uin[1])
        #Unknown command
        else:
            print('Неизвестная команда')

    except SystemExit:
        sys.exit()
    except:
        print('АА СТОП ОШИБКА 00000')
        print(traceback.format_exc())
        
def commitMoves(user, *moves):
    if user in permissions:
        print(user, 'запросил ходы:', moves)
        dumpMoves(user, moves)
    else:
        print(user, 'нелегально запросил ходы:', moves)
        
def dumpMoves(user, moves):
    print('Сбрасываем ходы в файл moves.txt')
    users = moves.readlines()
    for line in users:
        if line.contains(user):
            for move in moves:
                if line.contains(move):
                    pass
                    moves.replace(move, '')
            line += moves
            break
         else: 
            line += user+':'+moves
    else:
        print('Все ходы повторяются. Ни один не записан.')
    print('Записали ходы:', moves, 'в файл moves.txt')
    moves.writelines(users)
                    
def getInput():
    """Reads console input"""
    uin = input().split()
    console_command(uin)

print('Начинаем работу')
inp = threading.Thread(target = read_msg, daemon = True)
inp.start()
print('Работаем, братья')
 
while 1:
    getInput()
