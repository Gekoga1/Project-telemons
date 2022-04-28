from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from configure.configuraion import database_manager, MONSTER_NUM, NOTHING, ABILITY_NUM, TEAM_NUM, COLLECTION_NUM, COLLECTION_TEAM
from main import main_menu


def team_or_collection(update: Update, context: CallbackContext):  # выбор, что смотреть: коллекция или команда
    query = update.callback_query
    ques = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Просмотр коллекции', callback_data='collection'),
            InlineKeyboardButton('Просмотр команды', callback_data='team')
        ]
    ])
    query.edit_message_text('Что Вы хотите сделать?', reply_markup=ques)


def collection_info(update: Update, context: CallbackContext):  # вывод всей коллекции монстров
    collection = get_collection_info(update, context)
    msg = 'Ваши монстры:\n\n'
    if len(collection) == 0:
        update.effective_user.send_message('У Вас ещё нет монстров в коллекции, сыграйте в PVE бой, '
                                           'чтобы получить нового монстра')
        main_menu(update, context)
    else:
        for i in range(len(collection)):
            msg += f'{i + 1}) {collection[i][1]}\n'
        update.effective_user.send_message(text=msg)
        monster_choice(update, context)


def get_collection_info(update: Update, context: CallbackContext):  # получение информации о монстрах из коллекции
    user_id = update.effective_user.id
    monsters_id = database_manager.get_collection(user_id).split(';')
    collection = [database_manager.get_monster_info(int(i)) for i in monsters_id if i != '']
    return collection


def monster_choice(update: Update, context: CallbackContext):  # спрашивает номер монстра
    context.chat_data['waiting_for'] = MONSTER_NUM
    update.effective_user.send_message(text='Введите номер монстра')
    get_monster_num(update, context)


def get_monster_num(update: Update, context: CallbackContext):  # получает номер монстра
    try:
        user_id = update.effective_user.id
        monster_num = int(update.message.text)
        context.chat_data['collection_num'] = database_manager.get_collection(user_id).split(';')[monster_num - 1]
        print(database_manager.get_collection(user_id).split(';')[monster_num - 1])
        ques = InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Заменить монстра', callback_data='change monster'),
                InlineKeyboardButton('Посмотреть характеристики', callback_data='monster info')
            ],
            [
                InlineKeyboardButton('Вернуться в главное меню', callback_data='main menu')
            ]
        ])
        update.message.reply_text(f'Вы выбрали монстра под номером {str(monster_num)} \n'
                                  f'Что Вы хотите сделать?', reply_markup=ques)
    except Exception as ex:
        print(ex)
        update.message.reply_text('Вы ввели не число, попробуйте ещё раз.')


def monster_info(update: Update, context: CallbackContext):  # информация о монстре
    collection = get_collection_info(update, context)
    monster_num = context.chat_data['monster_num']
    text = f'Монстр: {collection[monster_num - 1][1]}\nУровень: {collection[monster_num - 1][2]}\n' \
           f'Опыт: {collection[monster_num - 1][3]}'
    update.effective_user.send_message(text=text)
    monster_activity(update, context)


def monster_activity(update: Update, context: CallbackContext):  # предлагает действия с монстром
    ques = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Вернуться в главное меню', callback_data='main menu'),
            InlineKeyboardButton('Заменить способность', callback_data='change ability')
        ],
        [
            InlineKeyboardButton('Эволюционировать', callback_data='evolution'),
            InlineKeyboardButton('Заменить монстра', callback_data='change monster')
        ]
    ])
    update.effective_user.send_message(text='Что вы хотите сделать?', reply_markup=ques)


def show_team_for_change(update: Update, context: CallbackContext):
    context.chat_data['waiting_for'] = COLLECTION_TEAM
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('1', callback_data='1'),
            InlineKeyboardButton('2', callback_data='2'),
            InlineKeyboardButton('3', callback_data='3'),
            InlineKeyboardButton('4', callback_data='4')
        ]
    ])
    team_info(update, context, only_show=True, reply_markup=keyboard)


def select_monster_in_team(update: Update, context: CallbackContext):
    num = update.callback_query.data
    context.chat_data['team_num'] = num
    context.chat_data['waiting for'] = NOTHING
    change_monster(update, context)


def print_ability_num(update: Update, context: CallbackContext):  # спрашивает номер способности
    update.effective_user.send_message(text='Введите номер способности, которую хотите заменить')
    context.chat_data['waiting_for'] = ABILITY_NUM
    get_ability_num(update, context)


def get_ability_num(update: Update, context: CallbackContext):  # получает номер способности от пользователя
    try:
        ability_num = int(update.message.text)
        show_ability_list(update, context, ability_num)
    except Exception as ex:
        print(ex)
        update.message.reply_text('Вы ввели не число, попробуйте ещё раз')


def show_ability_list(update: Update, context: CallbackContext,
                      ability_num):  # показывает список доступных способностей
    print(ability_num)
    update.message.reply_text('Здесь выводится список доступных способностей')


def team_info(update: Update, context: CallbackContext, only_show=False, reply_markup=None):
    user_id = update.effective_user.id
    monsters_id = database_manager.get_team(user_id).split(';')
    team = [database_manager.get_monster_info(int(i)) for i in monsters_id if i != '']
    text = 'Ваша команда:\n\n'
    for i in range(len(team)):
        text += f'{i + 1}) {team[i][1]}, уровень: {team[i][2]}, опыт: {team[i][3]}\n'
    if len(team) < 4:
        text += f'\nВы можете добавить в команду ещё {4 - len(team)} монстра'
    update.effective_user.send_message(text=text, reply_markup=reply_markup)
    if only_show:
        return
    else:
        team_activity(update, context)


def team_activity(update: Update, context: CallbackContext):  # информация о команде
    change_ques = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Да', callback_data='change team'),
            InlineKeyboardButton('Нет', callback_data='main menu')
        ]
    ])
    update.callback_query.edit_message_text('Вы хотите изменить команду?', reply_markup=change_ques)


def change_team(update: Update, context: CallbackContext, team):  # изменение команды
    user_id = update.effective_user.id
    database_manager.change_user_team(user_id, team)
    update.effective_message.reply_text('Команда успешно изменена')


def change_collection(update: Update, context: CallbackContext, new_collection):  # добавление монстра в коллекцию игрока
    user_id = update.effective_user.id
    database_manager.change_user_collection(user_id, new_collection)


def check_add_monster(update: Update, context: CallbackContext, uid):  # проверка, есть ли новый монстр уже у игрока
    collection = database_manager.get_collection(update.effective_user.id).split(';')
    uid_in_coll = [database_manager.get_monster_uid(int(i)) for i in collection if i != '']
    if uid in uid_in_coll:
        return False
    else:
        return True


def write_team_num(update: Update, context: CallbackContext):
    context.chat_data['waiting_for'] = TEAM_NUM
    update.effective_user.send_message('Введите номер монстра в команде')
    get_team_num(update, context)


def get_team_num(update: Update, context: CallbackContext):
    try:
        team_num = int(update.message.text)
        if team_num > 4 or team_num <= 0:
            raise Exception
        else:
            context.chat_data['team_num'] = team_num
            show_collection(update, context)
    except Exception as ex:
        print(ex)
        update.message.reply_text('Вы ввели не число или ввели номер, которого нет, попробуйте ещё раз')


def show_collection(update: Update, context: CallbackContext):
    context.chat_data['waiting_for'] = COLLECTION_NUM
    context.chat_data['collection_num'] = 0
    collection = get_collection_info(update, context)

    btns = []
    temp = []
    keyboard = []
    for i in range(len(collection) + 1):
        if i == len(collection):
            btns.append(temp)
        elif len(temp) <= 8:
            temp.append(i + 1)
        else:
            btns.append(temp)
            temp = []
    for group in btns:
        btns_in_row = []
        for num in group:
            btns_in_row.append(InlineKeyboardButton(str(num), callback_data=str(collection[num - 1][0])))
        keyboard.append(btns_in_row)

    text = 'Ваши монстры:\n\n'
    if len(collection) == 0:
        update.effective_user.send_message('У вас больше нет монстров, сыграйте в бой PvE,'
                                           ' чтобы получить нового монстра')
    else:
        for i in range(len(collection)):
            text += f'{i + 1}. {collection[i][1]}\n'
        update.effective_user.send_message(text=text, reply_markup=InlineKeyboardMarkup(keyboard))


def select_monster(update: Update, context: CallbackContext):
    num = update.callback_query.data
    context.chat_data['collection_num'] = num
    context.chat_data['waiting for'] = NOTHING
    change_monster(update, context)


def change_monster(update: Update, context: CallbackContext):
    team = database_manager.get_team(update.effective_user.id).split(';')
    collection = database_manager.get_collection(update.effective_user.id).split(';')
    team_num = context.chat_data['team_num']
    coll_num = context.chat_data['collection_num']
    new_team = ''
    new_collection = ''
    try:
        for i in range(len(team) + 1):
            print(i)
            if i == int(team_num) - 1:
                print(coll_num)
                new_team += f'{str(coll_num)};'
                new_collection += f'{team[i]}'
            elif team[i] != '':
                new_team += f'{team[i]};'
            else:
                new_team += f'{str(coll_num)}'
    except Exception as ex:
        print(ex)
    print(new_team, 'new team')
    for i in range(len(collection)):
        if collection[i] == str(coll_num):
            new_collection += ''
        else:
            new_collection += f'{collection[i]};'
    change_team(update, context, new_team[:-1])
    change_collection(update, context, new_collection[:-1])
    text = f'Новая команда:\n\n'
    monsters_id = database_manager.get_team(update.effective_user.id).split(';')
    new_team = [database_manager.get_monster_info(int(i)) for i in monsters_id if i != '']
    for i in range(len(new_team)):
        text += f'{i + 1}) {new_team[i][1]}, уровень: {new_team[i][2]}, опыт: {new_team[i][3]}\n'
    update.effective_user.send_message(text)
    next_activity(update, context)


def next_activity(update: Update, context: CallbackContext):
    ques = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('Изменить команду ещё раз', callback_data='team'),
            InlineKeyboardButton('Вернуться в главное меню', callback_data='main menu')
        ]
    ])
    update.effective_user.send_message(text='Что Вы хотите сделать?', reply_markup=ques)
