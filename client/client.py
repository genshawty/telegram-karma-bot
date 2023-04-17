from telethon import TelegramClient
# Use your own values from my.telegram.org
from telethon.tl.types import PeerChannel
import requests
from settings import API_ID, API_HASH, CHANNEL_ID, API_TOKEN, USERNAME

client = TelegramClient(USERNAME, api_id=API_ID, api_hash=API_HASH)

async def get_user_info_from_link(link: str):
    link_arr = link.split("/")
    msg_id = int(link_arr[-1])
    return await get_user_info_from_id(msg_id)

async def get_user_info_from_id(id: int):
    await client.start()
    chat = await client.get_entity(PeerChannel(CHANNEL_ID))
    ans = await client.get_messages(chat, ids=id)
    user_id = ans.from_id.user_id
    
    username = get_username_by_id(user_id, chat.username)
    return user_id, username

def get_username_by_id(user_id: int, channel_name_id: str):
    r = requests.get(f"https://api.telegram.org/bot{API_TOKEN}/getChatMember?chat_id=@{channel_name_id}&user_id={user_id}")
    ans = r.json()
    if ans["ok"]:
        try:
            return ans["result"]["user"]["username"]
        except:
            return None
    return None