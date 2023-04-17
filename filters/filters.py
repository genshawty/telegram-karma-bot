from typing import Union

from aiogram.filters import Filter
from aiogram.types import Message
from settings import CHANNEL_ID

class ChatTypeFilter(Filter):
    def __init__(self, chat_type: Union[str, list]) -> None:
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type

class AdminFilter(Filter):
    def __init__(self, admin_get_list) -> None:
        self.admin_get_list = admin_get_list
        self.admin_list = admin_get_list()

    async def __call__(self, message: Message) -> bool:
        self.admin_list = self.admin_get_list()
        if isinstance(self.admin_list, str):
            return str(message.from_user.id) == self.admin_list
        else:
            return str(message.from_user.id) in self.admin_list
    
class IsReplyFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.reply_to_message is not None
    
class IsForwardFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.forward_from is not None
    
class TargetChannel(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == CHANNEL_ID
    
class LogChannel(Filter):
    def __init__(self, func) -> None:
        self.get_log_channel = func
        self.log_channel = func()

    async def __call__(self, message: Message) -> bool:
        self.log_channel = self.get_log_channel()
        return str(message.chat.id) == self.log_channel