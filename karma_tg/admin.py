from karma_tg.create_db import User, Base, Log
from karma_tg.karma import get_role_by_points
import json, os
from logging import Logger
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session

def export_users(s: Session):
    users = s.query(User).all()
    columns = ",".join(["user_id", "username", "rolename", "points"])

    users_string = "\n".join(map(lambda x: x.to_csv(), users))
    ans = columns + "\n" + users_string

    with open("data/users.csv", "w", encoding="utf8") as f:
        f.write(ans)

def export_log(s: Session):
    logs = s.query(Log).all()
    columns = ",".join(["message_id", "log_message_id", "helper_id", "helper_name", "user_id", "user_name", "action_id", "action_input", "points_change", "new_points_balance",
                            "thank_back", "cancelled", "role_changed", "time"])

    logs_string = "\n".join(map(lambda x: x.to_csv(), logs))
    ans = columns + "\n" + logs_string

    with open("data/logs.csv", "w", encoding="utf8") as f:
        f.write(ans)

def get_log_channel():
    return json.load(open(os.path.join(os.path.dirname(__file__), "admins.json")))["log_channel"]

def if_admin(user_id: int):
    admins = admin_list()
    return str(user_id) in admins

def admin_list():
    return json.load(open(os.path.join(os.path.dirname(__file__), "admins.json")))["admins"]

def update_log_id(msg_id:int, log_id: int, s: Session):
    ans = s.query(Log).filter(Log.msg_id == msg_id).all()[-1]
    ans.log_message_id = log_id
    s.add(ans)
    s.commit()

def cancel_action(log_id: int, s: Session):
    ans = s.query(Log).filter(Log.log_message_id == log_id).all()[0]
    ans.cancelled = True

    helper_id = ans.helper_id
    change = ans.points_change

    helper = s.query(User).filter(User.user_id == helper_id).all()[0]
    helper.points -= change

    s.add(ans)
    s.add(helper)
    s.commit()

def leaderboard(s: Session):
    ans = s.query(User).order_by(User.points.desc())
    return ["{}: {}".format(user.username, user.points) for user in ans]

def admin_comand(action, name, num, s: Session) -> bool:
    user = s.query(User).filter(User.username == name).all()
    if num is not None:
        num = int(num)

    if len(user) == 0:
        return "User not found, forward some of his messages to this chat and then restart with /admin", False
    if len(user) > 1:
        return f"found {len(user)} users, check please", False
    user = user[0]
    ans = ""
    if action == "show":
        ans = user.make_string_user()
    elif action == "add":
        user.points += num
        ans = f"SUCCESFULLY ADDED POINTS user: {name}, balance: {user.points}"
    elif action == "sub":
        user.points -= num
        ans = f"SUCCESFULLY SUBSTRACTED POINTS user: {name}, balance: {user.points}"
    elif action == "set":
        user.points = num
        ans = f"SUCCESFULLY SET POINTS user: {name}, balance: {user.points}"

    user.rolename = get_role_by_points(user.points)[0]
    s.add(user)
    s.commit()
    return ans, True