#!/bin/env python3
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

import traceback
import threading
import sys
import time
import re

token = open('token').read().replace('\n', '')
longpoll = open('longpoll').read().replace('\n', '')
print('Подключаемся к токену', token, '\b...')
vk_session = vk_api.VkApi(token = token)
vk = vk_session.get_api()
print('Лонгполлируем группу номер', longpoll, '\b...')
vk_longpoll = VkBotLongPoll(vk_session, longpoll)
timeout = 30

peer = None

def make_table(tabname):
    """Reads a table
    Arguments:
    tabname -- table name : str"""
    print('Читаем таблицу', tabname, '\b...')
    with open(tabname) as tabf:
        tabfile = tabf.read().splitlines()
        tabf.close()
    tabout = dict()
    for line in tabfile:
        line.replace("\n", "")
        key, response = line.split(':', 1)
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
mfloc = './diplo/moves.txt'
permissions = open('./diplo/permissions.txt').read()

def read_msg():
    """Reads a message from longpoll and processes it"""
    try:
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
    except:
        print('Нет связи с сервером. Повторное соединение через %d секунд.', timeout)
        connect()

def check_msg():
    try:
        for event in vk_longpoll.check():
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
    except: 
        print('Нет связи с сервером. Повторное соединение через %d секунд.', timeout)
        connect()

def connect():
    global timeout
    timer = time.time()
    while (time.time() - timer) < timeout:
        pass
    check_msg()

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
            print('Выполняем', uin[1] + '...')
            user_command(uin[1])
        #Force reconnect
        elif com == 'fr':
            print('Переподключаемся...')
            connect()
        #Unknown command
        else:
            print('Неизвестная команда')

    except SystemExit:
        sys.exit()
    except:
        print('АА СТОП ОШИБКА 00000')
        print(traceback.format_exc())
        
def receive_moves(user, moves):
    print(moves)
    illegal = []
    illegalmsg = "Не распознаны аргументы:", illegal
    final = []
    finalmsg = "Посланы ходы:", final
    for move in moves:
        print(move)
        m1, m2 = move.split('-')
        move = move.lower()
        if re.match(r'([a-z]\d{1,2})-([a-z]\d{1,2})', move) and (m1 != m2):
            final.append(move)
        else:
            illegal.append(move)
    if illegal:
        write_msg(illegalmsg, user)
    if final:
        write_msg(finalmsg, user)
    
    if (str(user)+'\n') in permissions:
        print(user, 'запросил ходы:', final)
        dumpMoves(user, moves)
    else:
        print(user, 'нелегально запросил ходы:', final)
        
def dumpMoves(user, moves):
    usermoves = []
    print('Сбрасываем ходы в файл moves.txt')
    with open(mfloc, 'r') as movesfile:
        usermoves = movesfile.read().splitlines()
        userstr = str(user)
        linum = 0
        for i, line in enumerate(usermoves):
            ltok = line.split(',')
            if ltok[0] == userstr:
                print('В файле moves.txt найден пользователь %s, добавляем ходы...' % user)
                linum = i
                for move in moves:
                    if move in ltok: 
                        continue
                    else:
                        line += move + ','
                line+='\n'
                usermoves[i] = line
                break
        else:
            print('Пользователь %s не найден в файле moves.txt, добавляем в файл...'%userstr)
            usermoves.append(userstr + ',')
            line = usermoves[-1]
            for move in moves:
                if move in line:
                    continue
                else:
                    usermoves[-1] = line+move+','+'\n'
            linum = -1 
    movesfile.close()        
    with open (mfloc, 'w') as movesfile:
        pass
        movesfile.writelines( usermoves )
    print('Записали ходы:', moves, 'в файл moves.txt')            

def getInput():
    """Reads console input"""
    uin = input().split()
    console_command(uin)

print('Начинаем работу...')
inp = threading.Thread(target = read_msg, daemon = True)
inp.start()
print('Работаем, братья')
while 1:
    getInput()
