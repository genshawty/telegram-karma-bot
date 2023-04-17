from aiogram import Router
from aiogram.filters import Command, Text
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from aiogram.utils.markdown import text
from filters.filters import AdminFilter, ChatTypeFilter, IsForwardFilter
from aiogram.types import FSInputFile

from karma_tg.karma import get_user_by_user_id, get_role_by_points, update_helper
from karma_tg.admin import leaderboard, admin_list, admin_comand, get_log_channel, export_log, export_users
from karma_tg.create_db import User
from client.client import get_user_info_from_link

from settings import API_TOKEN
from requests import get
import urllib.parse
router = Router()

engine = create_engine("sqlite:///users.db")
session = sessionmaker(bind=engine)
s = session()

def send_message(text: str):
    text = urllib.parse.quote(text)
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage?chat_id={get_log_channel()}&text={text}"
    get(url)

@router.message(ChatTypeFilter(chat_type="private"), AdminFilter(admin_list), Command(commands='karma'))
async def private_admin_test_cmd_karma(message: types.Message):
    if message.from_user.is_bot:
        return
    user_id = message.from_user.id
    user = get_user_by_user_id(user_id, s)
    if user is None:
        return await message.answer("Unfortunately, you don't have any Sage role yet. Keep moving forward. CheeChee!")
    points, rolename = user.points, user.rolename

    new_role = get_role_by_points(points)[0]
    if new_role != rolename:
        user.rolename = new_role
        s.add(user)
        s.commit()
        
    rolename = new_role
    if rolename == "no-role":
        return await message.answer("Unfortunately, you don't have any Sage role yet. Keep moving forward. CheeChee!")
    else:
        return await message.answer("You have {} points in your pocket. Keep building 💪".format(points))

@router.message(ChatTypeFilter(chat_type="private"), AdminFilter(admin_list), Command(commands='admin'))
async def private_admin_panel(message: types.Message):
    markup = InlineKeyboardBuilder()
    markup.add(
        types.InlineKeyboardButton(text="Leaderboard", callback_data="leaderboard"),
        types.InlineKeyboardButton(text="Points manipulation", callback_data="edit_points"),
        types.InlineKeyboardButton(text="Add user", callback_data="add_user"),
        types.InlineKeyboardButton(text="Export files", callback_data="export_files")
    )
    return await message.answer(
        "Admin Panel",
        reply_markup=markup.as_markup()
    )

# @router.message(ChatTypeFilter(chat_type="private"), AdminFilter(admin_list), IsForwardFilter())
# async def private_admin_free(message: types.Message):
#     user_id = message.forward_from.id
#     first_name = message.forward_from.first_name
#     last_name = message.forward_from.last_name

#     user_name = message.forward_from.username
#     if user_name is None:
#         uname_row = "username: hidden by user"
#     else:
#         uname_row = "username: {}".format(user_name)
    
#     first_reply = text(
#         "id: {}".format(user_id),
#         "first name: {}".format(first_name),
#         "last name: {}".format(last_name),
#         uname_row,
#         sep="\n"
#     )
#     await message.reply(first_reply)
    
#     user = get_user_by_user_id(user_id=user_id, s=s)

#     if user is None:
#         second_reply = "user is not found, adding in database"
#         user = User(user_id=user_id, username=user_name, is_hidden=user_name is None, rolename=get_role_by_points(0)[0], points=0)
#         await message.reply(second_reply)
#         update_helper(user, s)
#         return await message.reply("Succesfull adding the info!")
#     else:
#         second_reply = "found: {}".format(user.make_string_user())
#         if user_name != user.username:
#             second_reply = second_reply + "\nWARN: username changed from: {}, to: {}".format(user.username, user_name)
#             user.username = user_name

#             await message.reply(second_reply)
#             update_helper(user, s)
#             return await message.reply("Succesfull updating the info!")
        
#         return await message.reply("Nothing to update")            

@router.callback_query(Text(text="export_files"))
async def admin_export_files(callback: types.CallbackQuery):
    engine = create_engine("sqlite:///users.db")
    session = sessionmaker(bind=engine)
    s = session()
    export_users(s)
    export_log(s)
    users_file = FSInputFile("data/users.csv")
    logs_file = FSInputFile("data/logs.csv")
    
    await callback.message.answer_document(users_file)
    await callback.message.answer_document(logs_file)
    await callback.answer()

@router.callback_query(Text(text="leaderboard"))
async def admin_show_leaderboard(callback: types.CallbackQuery):
    engine = create_engine("sqlite:///users.db")
    session = sessionmaker(bind=engine)
    s = session()
    ans = leaderboard(s)
    if len(ans) > 20:
        ans = ans[:20]
    await callback.message.answer('\n'.join(ans))
    await callback.answer()

class AddUser(StatesGroup):
    link = State()

@router.callback_query(Text(text="add_user"))
async def admin_add_user(callback: types.CallbackQuery, state: FSMContext):
    instructions_text = text(
                            "Enter link to user message: "
                        )

    await callback.message.reply(instructions_text)
    await state.set_state(AddUser.link)
    await callback.answer()

@router.message(AddUser.link)
async def admin_edit_points(message: types.Message, state: FSMContext):
    await state.clear()
    link = message.text
    user_id, user_name = await get_user_info_from_link(link)

    user = get_user_by_user_id(user_id=user_id, s=s)

    if user_name is None:
        uname_row = "username: hidden by user"
    else:
        uname_row = "username: {}".format(user_name)

    first_reply = text(
        "id: {}".format(user_id),
        uname_row,
        sep="\n"
    )
    await message.reply(first_reply)
    
    if user is None:
        second_reply = "user is not found, adding in database"
        user = User(user_id=user_id, username=user_name, is_hidden=user_name is None, rolename=get_role_by_points(0)[0], points=0)
        await message.reply(second_reply)
        update_helper(user, s)
        return await message.reply("Succesfull added the info!")
    else:
        second_reply = "found: {}".format(user.make_string_user())
        if user_name != user.username:
            second_reply = second_reply + "\nWARN: username changed from: {}, to: {}".format(user.username, user_name)
            user.username = user_name

            await message.reply(second_reply)
            update_helper(user, s)
            return await message.reply("Succesfull updated the info!")
        return await message.reply("Nothing to update")

class ChangePoints(StatesGroup):
    edit_points = State()

@router.callback_query(Text(text="edit_points"))
async def admin_add_points(callback: types.CallbackQuery, state: FSMContext):
    instructions_text = text(
                            "Write command to add points like this:",
                            "[action] [username] [number]",
                            "Where: action - show, add, sub, show",
                            "username - username without at sign",
                            "number - amount of points to add/subsctract/set. Do not write it when use show command. Example:",
                            "add gen_0x 5",
                            "will add 5 points to a user with gen_0x username",
                            sep="\n"
                        )

    await callback.message.reply(instructions_text)
    await state.set_state(ChangePoints.edit_points)
    await callback.answer()

@router.message(ChangePoints.edit_points)
async def admin_edit_points(message: types.Message, state: FSMContext):
    text = message.text.split()
    action, name, num = [None]*3
    
    markup = InlineKeyboardBuilder()
    markup.add(
        types.InlineKeyboardButton(text="Leaderboard", callback_data="leaderboard"),
        types.InlineKeyboardButton(text="Points manipulation", callback_data="edit_points")
    )

    if len(text) == 3:
        action, name, num = text
        if (action not in ["show", "set", "add", "sub"]) or (not num.isnumeric()):
            return await message.reply("Wrong command", reply_markup=markup.as_markup())
    elif len(text) == 2:
        action, name = text
        if (action not in ["show", "set", "add", "sub"]):
            return await message.reply("Wrong command", reply_markup=markup.as_markup())
    else:
        return await message.reply("Wrong command", reply_markup=markup.as_markup())

    ans, ok = admin_comand(action, name, num, s)

    if not ok:
        await message.reply(ans, reply_markup=markup.as_markup())
        return await state.clear()

    await message.reply(ans, reply_markup=markup.as_markup())
    await state.clear()
    send_message("action: {}, name: {}, num: {}, admin name: {}, admin id: {}, #admin".format(action, name, num, message.from_user.username, message.from_user.id))

@router.message(ChatTypeFilter(chat_type="private"), AdminFilter(admin_list))
async def private_admin_free(message: types.Message):
    return await message.answer("Probably you forgot to forward message or or account is hidden by user or type /admin")