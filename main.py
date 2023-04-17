from aiogram.utils.markdown import text as md_text
from aiogram.utils.markdown import link, bold
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder

from settings import API_TOKEN

from karma_tg.karma import get_action_info, thank_back_check, add_points, get_user_by_user_id, get_role_by_points
from karma_tg.admin import get_log_channel, cancel_action, update_log_id
from filters.filters import ChatTypeFilter, IsReplyFilter, TargetChannel, LogChannel

import logging, os, asyncio
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from handlers import private_admins, private_users

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=storage)

engine = create_engine("sqlite:///users.db")
session = sessionmaker(bind=engine)
s = session()

logger = logging.getLogger()

# dd/mm/YY H:M:S
dt_string = "bot_log"
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", dt_string + ".log")

with open(log_file, mode='a+'): pass

logging.basicConfig(level=logging.INFO, 
                    filename = log_file,
                    format = "%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                    datefmt='%H:%M:%S',
                    force=True,
                )
                
logger.warning("RERUNNING")

# @dp.message()
# async def main_get_chat_id(message: types.Message):
#     print(message.chat.id)
#     print(message.chat)
#     await message.reply(message.chat.id)

@dp.message(LogChannel(get_log_channel), IsReplyFilter())
async def log_cancel(message: types.Message):
    if message.text != "-":
        return
    log_id = message.reply_to_message.message_id
    cancel_action(log_id, s=s)

    await message.reply("Cancelled!")

@dp.message(TargetChannel(), ChatTypeFilter(chat_type=["group", "supergroup"]), Command(commands='karma'))
async def karma_command(message: types.Message):
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
    

@dp.message(TargetChannel(), ChatTypeFilter(chat_type=["group", "supergroup"]), IsReplyFilter())
async def main_group(message: types.Message):
    if message.from_user.is_bot:
        return
    user_id = message.from_user.id
    helper_id = message.reply_to_message.from_user.id

    user_name = message.from_user.username
    helper_name = message.reply_to_message.from_user.username
    is_helper_hidden = helper_name is None

    time = datetime.now(tz=timezone.utc)
    
    # check if not reply to himself
    if user_id == helper_id:
        return   

    # get info about action
    action_id, action_input, points = get_action_info(message.text)
    if points == 0:
        return
    
    is_thank_back = thank_back_check(message.reply_to_message.message_id, user_id, s)
    
    log_msg_dict = add_points(
        logger=logger, 
        msg_id=message.message_id,
        helper_id=helper_id,
        helper_name=helper_name,
        is_helper_hidden=is_helper_hidden,
        user_id=user_id,
        user_name=user_name,
        points_change=points,
        action_id=action_id,
        action_input=action_input,
        is_thank_back=is_thank_back,
        time=time,
        s=s
    )
    
    log_msg = md_text(
        f"helper: {log_msg_dict['helper_name']}", 
        f"user: {log_msg_dict['user_name']}", 
        f"action id: {log_msg_dict['action_id']}", 
        f"action input: {log_msg_dict['action_input']}", 
        f"actual points balance: {log_msg_dict['actual_balance']}", sep="\n")
    if log_msg_dict["role_changed"]:
        log_msg = log_msg + f"\nNEW helper ROLE: {log_msg_dict['actual_role']} #bot"
    else:
        log_msg = log_msg + f"\nhelper role: {log_msg_dict['actual_role']} #bot"
    link = message.get_url()
    helper_text = message.reply_to_message.text
    user_text = message.text

    log_msg = log_msg + "\nlink: {}\nhelper message: {}\nuser message: {}".format(link, helper_text, user_text)

    log_message_sended = await bot.send_message(chat_id=int(get_log_channel()), text=log_msg)

    log_msg_id = log_message_sended.message_id
    update_log_id(message.message_id, log_msg_id, s)

# log_msg = {
#         "helper_name": helper_name,
#         "user_name": user_name,
#         "action": action_name,
#         "points_change": points_change,
#         "role_changed": role_changed,
#         "actual_role": helper.rolename,
#         "actual_balance": helper.points
#     }

async def main():
    logging.getLogger("aiogram.event").setLevel(logging.WARN)
    dp.include_router(private_admins.router)
    dp.include_router(private_users.router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())