from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from configure.configuraion import rooms, teams
from creating_rooms.Room import Room, Stage
from game_logic.game_lib import *


def choose_type_fight(update: Update, context: CallbackContext):
    query = update.callback_query
    fights = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('PVP', callback_data='PVP'),
        ],
        [
            InlineKeyboardButton('PVE', callback_data='PVE')
        ],
        [
            InlineKeyboardButton('Вернуться в главное меню', callback_data='main menu')
        ]
    ])
    query.edit_message_text('Выберите тип сражения', reply_markup=fights)


def fight_PVP(update: Update, context: CallbackContext):
    if len(rooms):
        join_room(update=update, context=context)
    else:
        create_room(update=update, context=context)


def create_room(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    room = Room()
    room.author_id = user.id
    room.room_name = user.username
    context.chat_data['create_room'] = room

    room: Room = context.chat_data['create_room']

    rooms[room.room_name] = room
    del context.chat_data['create_room']
    context.bot_data[user.id]['stage'] = Stage.HOSTING_GAME
    room.count_players = 0
    room.player_list = []
    room.round_data = {}

    query.edit_message_text(
        text='Подходящих комнат не нашлось, поэтому комната была создана.\nВы уже находитесь в ней, ждите пользователей')

    context.chat_data['roomName'] = user.username
    room.player_list.append(update.effective_message.chat_id)
    room.count_players += 1
    context.bot_data[user.id]['stage'] = Stage.PLAY_GAME


def close_room(update: Update, context: CallbackContext, room_name) -> None:
    del rooms[room_name]


def join_room(update: Update, context: CallbackContext) -> None:
    for roomKey in rooms:
        if rooms[roomKey].count_players <= 2:
            context.chat_data['roomName'] = roomKey
            room_name = context.chat_data['roomName']
            room = rooms[room_name]
            show_room(update=update, context=context, room=room)
    # buttons = []
    # for roomKey in rooms:
    #     if rooms[roomKey].count_players <= 2:
    #         buttons.append(InlineKeyboardButton(rooms[roomKey].room_name, callback_data=rooms[roomKey].room_name))
    # keyboard = [buttons]
    # reply_markup = InlineKeyboardMarkup(keyboard)
    # query = update.callback_query
    # query.edit_message_text(text='Выберите комнату', reply_markup=reply_markup)


# def select_room(update: Update, context: CallbackContext) -> None:
#     context.chat_data['roomName'] = update.callback_query.data
#     room_name = context.chat_data['roomName']
#     room = rooms[room_name]
#     show_room(update=update, context=context, room=room)


def show_room(update: Update, context: CallbackContext, room) -> None:
    query = update.callback_query
    room.player_list.append(update.effective_user.id)
    room.count_players += 1
    context.bot_data[update.effective_user.id]['stage'] = Stage.PLAY_GAME
    query.edit_message_text(text=f'Проверка проверка, это комната {room.room_name}\n')
    if room.count_players == 2:
        room.count_round = 1
        room.blue_player = room.player_list[0]
        room.red_player = room.player_list[1]
        room.room_battle = Battle(None, teams[room.blue_player], None, teams[room.red_player])
        room.room_battle.start()
        test_game(update=update, context=context, room=room)


def test_game(update: Update, context: CallbackContext, room) -> None:
    # first_player = random.choice(room.player_list)
    for i in room.player_list:
        context.bot.send_message(chat_id=i, text='Игра началась')
        context.bot.send_message(chat_id=i,
                                 text=f'Раунд номер {room.count_round}\nДелайте свой ход и ждите противник')
    choose(update, context, room)

    # text = update.message.text
    # if text == 'hello':
    #     room_name = context.chat_data['roomName']
    #     context.bot_data[id]['stage'] = Stage.LOBBY
    #     update.message.reply_text('УРА! Вы угадали это слово')
    #     del rooms[room_name]
    #     main_menu(update, context)
    #     print(rooms)
    # else:
    #     update.message.reply_text(text='Вы не угадали слово')


def choose(update: Update, context: CallbackContext, room) -> None:
    for j, a in enumerate(room.player_list):
        if j == 0:
            skill = room.room_battle.blue_active.get_skills()
            skills = []
            for i in skill:
                if i != 'None':
                    skills.append([InlineKeyboardButton(i, callback_data=f'Атака {skill.index(i) + 1}')])
            skills.append([InlineKeyboardButton('Выход из боя', callback_data=f'exit_fight')])
            reply_markup = InlineKeyboardMarkup(skills)

            context.bot.send_message(chat_id=a, text=room.room_battle.print(reverse=True),
                                     reply_markup=reply_markup)
        else:
            skill = room.room_battle.red_active.get_skills()
            skills = []
            for i in skill:
                if i != 'None':
                    skills.append([InlineKeyboardButton(i, callback_data=f'Атака {skill.index(i) + 1}')])
            skills.append([InlineKeyboardButton('Выход из боя', callback_data=f'exit_fight')])
            reply_markup = InlineKeyboardMarkup(skills)

            context.bot.send_message(chat_id=a, text=room.room_battle.print(reverse=True),
                                     reply_markup=reply_markup)


def main_fight(update: Update, context: CallbackContext, text) -> None:
    room_name = context.chat_data['roomName']
    room = rooms[room_name]

    user_data = update.effective_user.id

    if user_data not in room.round_data:
        text_info = text.split()
        if text_info[0] == 'Атака':
            if room.player_list.index(user_data) == 0:
                if room.room_battle.blue_active.skills[int(text_info[1]) - 1] is not None:
                    room.round_data[user_data] = text
                    context.bot.send_message(chat_id=user_data, text='Ждите оппонента')
                else:
                    context.bot.send_message(chat_id=user_data, text='Ошибочный ввод')
            else:
                if room.room_battle.red_active.skills[int(text_info[1]) - 1] is not None:
                    room.round_data[user_data] = text
                    context.bot.send_message(chat_id=user_data, text='Ждите оппонента')
                else:
                    context.bot.send_message(chat_id=user_data, text='Ошибочный ввод')
        elif text_info[0] == 'Смена':
            if user_data == room.blue_player:
                if len(room.room_battle.blue_team) < 2:
                    context.bot.send_message(chat_id=user_data, text=f'У вас нету персонажей для смены')
                else:
                    context.bot.send_message(chat_id=user_data, text='Ждите оппонента')
            else:
                if len(room.room_battle.red_team) < 2:
                    context.bot.send_message(chat_id=user_data, text=f'У вас нету персонажей для смены')
                else:
                    context.bot.send_message(chat_id=user_data, text='Ждите оппонента')

    if len(room.round_data) == 2:
        change_happened = False
        for user_id in room.round_data:
            data = room.round_data[user_id]
            data = data.split()
            if data[0] == 'Смена':
                change_happened = True
                if user_id == room.blue_player:
                    propose_change_monster(update, context, room.room_battle.blue_active, player_move='blue',
                                           room=room)
                else:
                    propose_change_monster(update, context, room.room_battle.blue_active, player_move='red',
                                           room=room)
        if change_happened:
            if room.round_data[room.blue_player].split(' ')[0] == 'Атака':
                room.room_battle.blue_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
            elif room.round_data[room.red_player].split(' ')[0] == 'Атака':
                room.room_battle.red_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
        else:
            if room.room_battle.red_active.c_speed > room.room_battle.blue_active.c_speed:
                room.room_battle.red_turn(int(room.round_data[room.red_player].split(' ')[1]) - 1)
                room.room_battle.blue_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
            elif room.room_battle.red_active.c_speed < room.room_battle.blue_active.c_speed:
                room.room_battle.blue_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
                room.room_battle.red_turn(int(room.round_data[room.red_player].split(' ')[1]) - 1)
            else:
                if choice([True, False]):
                    room.room_battle.red_turn(int(room.round_data[room.red_player].split(' ')[1]) - 1)
                    room.room_battle.blue_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
                else:
                    room.room_battle.blue_turn(int(room.round_data[room.blue_player].split(' ')[1]) - 1)
                    room.room_battle.red_turn(int(room.round_data[room.red_player].split(' ')[1]) - 1)

        room.room_battle.update()

        for j, i in enumerate(room.player_list):
            if j == 0:
                your_name = database_manager.get_gamename(user_id=i)
                context.bot.send_message(chat_id=i,
                                         text=f'Команда {your_name} \n{room.room_battle.print(reverse=False)}')
            else:
                your_name = database_manager.get_gamename(user_id=i)
                context.bot.send_message(chat_id=i,
                                         text=f'Команда {your_name}\n{room.room_battle.print(reverse=False)}')

        if not room.room_battle.blue_active.alive:
            pass
        elif not room.room_battle.red_active.alive:
            pass

        if all(map(lambda x: not x.alive, room.room_battle.blue_team)):
            your_name = database_manager.get_gamename(user_id=room.red_player)
            context.bot.send_message(chat_id=room.red_player, text=f'Команда {your_name} выиграла!!!')
            room.winner = room.red_player
            return finishing_PvP(update, context, room)
        elif all(map(lambda x: not x.alive, room.room_battle.red_team)):
            your_name = database_manager.get_gamename(user_id=room.red_player)
            context.bot.send_message(chat_id=room.blue_player, text=f'Команда {your_name} выиграла!!!')
            room.winner = room.blue_player
            return finishing_PvP(update, context, room)
        #     context.bot.send_message(chat_id=user_id, text=f'ход совершён')
        # for user_id in room.round_data:
        #     context.bot.send_message(chat_id=user_id, text=room.round_data[user_id])
        # room.count_round += 1
        # for user_id in room.round_data:
        #     context.bot.send_message(chat_id=user_id,
        #                              text=f'Раунд номер {room.count_round}\nДелайте свой ход и ждите противника')
        room.round_data = {}

        choose(update, context, room)


def propose_change_monster(update: Update, context: CallbackContext, monster, player_move, room):
    buttons = []
    if player_move == 'blue':
        context.bot_data[room.blue_player]['stage'] = Stage.CHANGE_MONSTER
        for member in room.room_battle.blue_team:
            if member != monster:
                buttons.append(InlineKeyboardButton(member, callback_data=member))
    else:
        context.bot_data[room.red_player]['stage'] = Stage.CHANGE_MONSTER
        for member in room.room_battle.red_team:
            if member != monster:
                buttons.append(InlineKeyboardButton(member, callback_data=member))
    keyboard = [buttons]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(text='Выберите на кого будете менять', reply_markup=reply_markup)


def change_monster(update: Update, context: CallbackContext, monster, player_team):
    room_name = context.chat_data['roomName']
    room = rooms[room_name]
    if player_team == room.blue_player:
        room.room_battle.change(player=0, new=room.room_battle.blue_team.index(monster))
    else:
        room.room_battle.change(player=1, new=room.room_battle.blue_team.index(monster))
    context.bot.send_message(chat_id=player_team, text='Монстр изменен')


def finishing_PvP(update: Update, context: CallbackContext, room, is_extra=False) -> None:
    if is_extra is not True:
        for member in teams[room.winner]:
            member.get_exp(amount=100)
        for user_id in room.player_list:
            try:
                context.bot_data[user_id]['stage'] = Stage.LOBBY
                del context.chat_data['roomName']
                del rooms[room.room_name]
                context.bot.send_message(chat_id=user_id, text='Битва закончилась\n'
                                                               'Главное меню - /main_menu')

            except Exception as exception:
                context.bot.send_message(chat_id=user_id, text='Битва закончилась\n'
                                                               'Главное меню - /main_menu')
    else:
        room_name = context.chat_data['roomName']
        room = rooms[room_name]
        for user_id in room.player_list:
            try:
                context.bot_data[user_id]['stage'] = Stage.LOBBY
                del context.chat_data['roomName']
                del rooms[room.room_name]
                context.bot.send_message(chat_id=user_id,
                                         text='Битва закончилась досрочно, так как один из пользователей вышел\n'
                                              'Главное меню - /main_menu')
            except Exception as exception:
                context.bot.send_message(chat_id=user_id,
                                         text='Битва закончилась досрочно, так как один из пользователей вышел\n'
                                              'Главное меню - /main_menu')


def fighting_PVE(update: Update, context: CallbackContext):
    dummy = Spyland(lvl=5)
    dummy.generate_skills()

    id = update.effective_user.id
    team = teams[id]

    battle = Battle(None, team, None, [dummy])

    skill = battle.blue_active.get_skills()
    skills = []
    for i in skill:
        if i != 'None':
            skills.append([InlineKeyboardButton(i, callback_data=f'Атака {skill.index(i) + 1}')])
    skills.append([InlineKeyboardButton('Выход из боя', callback_data=f'exit_pve')])
    reply_markup = InlineKeyboardMarkup(skills)
    context.bot.send_message(chat_id=id, text=battle.print(reverse=False), reply_markup=reply_markup)
    context.bot_data[id]['stage'] = Stage.PLAY_PVE
    context.bot_data[id]['pve'] = battle


def continue_fighting_PVE(update: Update, context: CallbackContext, text, id):
    try:
        text_info = text.split()
        battle = context.bot_data[id]['pve']
        if text_info[0] == 'Атака':
            if battle.blue_active.skills[int(text_info[1]) - 1] is not None:
                context.bot.send_message(chat_id=id, text='Ход сделан')
            else:
                context.bot.send_message(chat_id=id, text='Ошибка ввода')

        red_choice = randint(0, 3 - battle.red_active.skills.count(None))
        if battle.red_active.c_speed > battle.blue_active.c_speed:
            battle.red_turn(int(red_choice))
            battle.blue_turn(int(text.split(' ')[1]) - 1)
        elif battle.red_active.c_speed < battle.blue_active.c_speed:
            battle.blue_turn(int(text.split(' ')[1]) - 1)
            battle.red_turn(int(red_choice))
        else:
            if choice([True, False]):
                battle.red_turn(int(red_choice))
                battle.blue_turn(int(text.split(' ')[1]) - 1)
            else:
                battle.blue_turn(int(text.split(' ')[1]) - 1)
                battle.red_turn(int(red_choice))
        battle.update()

        if all(map(lambda x: not x.alive, battle.blue_team)):
            context.bot.send_message(chat_id=id, text=f'Ты проиграл')
            return finishing_PVE(update, context, id)
        elif all(map(lambda x: not x.alive, battle.red_team)):
            context.bot.send_message(chat_id=id, text=f'Ты выиграл и получаешь опыт')
            return finishing_PVE(update, context, id)

        skill = battle.blue_active.get_skills()
        skills = []
        for i in skill:
            if i != 'None':
                skills.append([InlineKeyboardButton(i, callback_data=f'Атака {skill.index(i) + 1}')])
        skills.append([InlineKeyboardButton('Выход из боя', callback_data=f'exit_pve')])
        reply_markup = InlineKeyboardMarkup(skills)

        context.bot.send_message(chat_id=id, text=battle.print(), reply_markup=reply_markup)
    except Exception as exception:
        print(exception)


def finishing_PVE(update, context, id, extra=False):
    if not extra:
        context.bot_data[id]['stage'] = Stage.LOBBY
        del context.bot_data[id]['pve']
        context.bot.send_message(chat_id=id,
                                 text='Битва закончилась, вы получаете опыт\n'
                                      'Главное меню - /main_menu')
    else:
        context.bot_data[id]['stage'] = Stage.LOBBY
        del context.bot_data[id]['pve']
        context.bot.send_message(chat_id=id,
                                 text='Битва закончилась досрочно, вы не получаете опыт\n'
                                      'Главное меню - /main_menu')