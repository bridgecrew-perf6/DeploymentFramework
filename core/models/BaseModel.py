from peewee import *
import datetime

db = SqliteDatabase('config.db')

class BaseModel(Model):
    created_date = DateTimeField(default=datetime.datetime.now)
    class Meta:
        database = db