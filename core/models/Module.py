from peewee import *
from .BaseModel import BaseModel

class Module(BaseModel):
    name = CharField()
    version = DoubleField()