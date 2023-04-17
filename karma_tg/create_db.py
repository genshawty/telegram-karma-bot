from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import  Column, Integer, String, Boolean, DateTime
  
# строка подключения
sqlite_database = "sqlite:///users.db"
  
# создаем движок SqlAlchemy
engine = create_engine(sqlite_database)
#создаем базовый класс для моделей
Base = declarative_base()
  
# создаем модель, объекты которой будут храниться в бд
class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String)
    is_hidden = Column(Boolean, default=False)
    rolename = Column(String)
    points = Column(Integer)
    
    def make_string_user(self):
        return "user_id: {}\nusername: {}\nhidden: {}\nrolename: {}\npoints: {}".format(self.user_id, self.username, self.is_hidden, self.rolename, self.points)
    
    def to_csv(self):
        out = ",".join(map(lambda x: str(x).replace(",", "`"), [self.user_id, self.username, self.rolename, self.points]))
        return out
        
class Log(Base):
    __tablename__ = "log"
    num_row = Column(Integer, primary_key=True, autoincrement=True)

    # store message ids
    msg_id = Column(Integer)
    log_message_id = Column(Integer, default=-1)

    # helper identity. Points to him
    helper_id = Column(Integer)
    helper_name = Column(String)
    # user, who made an action
    user_id = Column(Integer)
    user_name = Column(String)

    action_id = Column(String)
    action_input = Column(String)
    points_change = Column(Integer)
    new_points_balance = Column(Integer)

    # thank_back storage
    thank_back = Column(Boolean)
    cancelled = Column(Boolean, default=False)
    role_changed = Column(Boolean, default=False)
    time = Column(DateTime)

    def to_csv(self):
        out = ",".join(map(lambda x: str(x).replace(",", "`"), 
                        [self.msg_id, self.log_message_id, self.helper_id, self.helper_name, self.user_id, 
                            self.user_name, self.action_id, self.action_input, self.points_change, self.new_points_balance, self.thank_back, self.cancelled, self.role_changed, self.time]))
        return out

if __name__ == "__main__":
    # создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("База данных и таблица созданы")