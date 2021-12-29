from peewee import *
from .BaseModel import BaseModel
from .Module import Module

class Settings(BaseModel):
    key = CharField()
    value = CharField()
    plugin = ForeignKeyField(Module, backref='pets', null=True)
    encrypt = BooleanField(default=False)

    #TODO: Extend this model to ensure we can encrypt + decrypt sensitve values