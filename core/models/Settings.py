import base64
from peewee import *
from .BaseModel import BaseModel
from .Module import Module
from .EncryptedField import EncryptedField

class Settings(BaseModel):
    key = CharField()
    # All Settings are now encrypted :)
    value = EncryptedField()
    plugin = ForeignKeyField(Module, null=True)