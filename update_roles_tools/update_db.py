from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from karma_dc.create_db import User
from karma_dc.karma import get_role_by_points, get_role_id_dict
import requests, time
from settings import TOKEN

engine = create_engine("sqlite:///users.db")
session = sessionmaker(bind=engine)
s = session()

guild_id = 1052208146443145226

def update_db():
    print("role updating started")

    users = s.query(User).all()
    for user in users:
        points, role = user.points, user.rolename
        new_role = get_role_by_points(points)[0]
        if new_role != role:
            user.rolename = new_role
        s.add(user)
    s.commit()

    print("role updating finished")
    
def give_role(user_id: int, role_id: int):
    url = "https://discord.com/api/guilds/{}/members/{}/roles/{}".format(guild_id, user_id, role_id)
    r = requests.put(url, headers={"Authorization": f"Bot {TOKEN}"})
    if r.status_code != 204:
        print("error with", user_id)

def give_everybody_roles():
    print("started giving everybody roles")
    users = s.query(User).all()
    roles = get_role_id_dict()
    for user in users:
        user_id, role_id = user.user_id, roles[user.rolename]
        give_role(user_id, role_id)
        time.sleep(0.5)
    print("ended giving everybody roles")