from __future__ import unicode_literals
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from peewee import *
import hashlib

__author__ = 'Constantin Roganov'

class EncryptedField(Field):
    """Encrypted field."""

    PASSPHRASE = ''
    db_field = 'binary'

    def db_value(self, value):
        if EncryptedField.PASSPHRASE == '':
            print("INVALID PASSPHRASE!")
            exit()
        # Encrypt
        obj = AES.new(hashlib.md5(EncryptedField.PASSPHRASE.encode()).hexdigest().encode(), AES.MODE_CFB, ("*" * 16).encode())
        newVal = obj.encrypt(value.encode())

        return newVal

    def python_value(self, value):
        if EncryptedField.PASSPHRASE == '':
            print("INVALID PASSPHRASE!")
            exit()
        # Decrypt
        obj = AES.new(hashlib.md5(EncryptedField.PASSPHRASE.encode()).hexdigest().encode(), AES.MODE_CFB, ("*" * 16).encode())
        newVal = obj.decrypt(value).decode()

        return super(EncryptedField, self).python_value(newVal)
