import importlib
from pymitter import EventEmitter
from PyInquirer import prompt
import os
from peewee import *
from core.models.Settings import Settings
from core.models.Module import Module
from core.models.EncryptedField import EncryptedField
from datetime import datetime

class Application:
    # We are going to receive a list of plugins as parameter

    events = EventEmitter()

    db = SqliteDatabase('config.db')

    def __init__(self, plugins:list=[], pluginConfig={}):
        question = [
            {
                'type': 'password',
                'name': 'password',
                'message': 'Encryption Password'
            }
        ]

        EncryptedField.PASSPHRASE = prompt(question)['password'];
    
        if not os.path.isfile("config.db"):
            print("New Install Detected!")

            # Register Framework Models in the database
            self.db.connect()
            self.db.create_tables([Settings, Module])
            # Create a default entry so we have a known update key
            # You could also use this to populate values such as Vendor Deploying; Contact Info Etc....
            Settings.create(key='install_date', value=datetime.now().strftime("%d-%b-%Y (%H:%M:%S.%f)"))
            Settings.create(key='install_test', encrypt=True, value="Working")
        else:
            try:
                # You can use this section to pull values from the database to display when launching....
                print("Install Date: %s"  % Settings.select().where(Settings.key == 'install_date').get().value)
            except:
                print("Error Launching... Config Database may be corrupt?")
                exit()

        if Settings.select().where(Settings.key == 'install_test').get().value != "Working":
            print(Settings.select().where(Settings.key == 'install_test').get().value)
            print("Error! Encryption Key Appears To Be Invalid!")
            exit()

        # Checking if plugin were sent
        if plugins != []:
            # create a list of plugins
            self._plugins = [
                importlib.import_module("plugins." + plugin + ".Plugin",".").Plugin(self.events, {**pluginConfig[plugin], **{'install_dir': './office'}}) for plugin in plugins
            ]
        else:
            # If no plugin were set we use our default
            self._plugins = [importlib.import_module('plugins.default.Plugin',".").Plugin(self.events)]

        self.events.emit("registerPlugin", self.db)

        
    def run(self, arguments):

        if len(arguments) == 0:
            self.events.emit("displayHelp")
            exit()
        else:
            if arguments[0] == "help":
                arguments[0] = "displayHelp"
        
        if len(arguments) == 1:
            self.events.emit(arguments[0])
        else:
            self.events.emit(arguments[0], arguments[1:])