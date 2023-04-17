from aiogram import Router
from aiogram import types
from filters.filters import ChatTypeFilter

router = Router()  

@router.message(ChatTypeFilter(chat_type="private"))
async def private_main_user(message: types.Message):
    # adv_message = "Here could be your ad"
    # return await message.answer(adv_message)
    return