from abc import ABC, abstractmethod
import passgen
from pymitter import EventEmitter
import os, sys
from core.models.Module import Module
from core.models.Settings import Settings

class BasePlugin(ABC):

    priority = 100

    version = 1.0

    listenForEvents = {}

    db = None

    module = None

    loadedPlugins = None

    # Core Events we always want to run.
    Events = {
        'registerPlugin': 'register',
        'displayHelp': 'help',
    }

    # List any commands that this plugin provides
    availableCommands = {
        'help': 'Displays this page; which lists available commands.'
    }

    # List any models that this Plugin Provides
    pluginModels = []
    
    def __init__(self, events, config = {}):
        self.config = config
        self.events = events
        self.__registerEvents__()

    def __registerEvents__(self):
        # Go though each of the events we need to listen to
        allEvents = {**self.listenForEvents, **self.Events}
        for event in allEvents:
            # If we are recieving a boolean take default actions
            if type(allEvents[event]) == type(True):
                # If True; Function == Event Name
                if allEvents[event]:
                    self.events.on(event, func=getattr(self, event))
                # If False; Don't listen for the event
            # If we recieve anything else; that should be the name of the function to call
            else:
                self.events.on(event, func=getattr(self, allEvents[event]))

    def getName(self):
        full_path = os.path.realpath(sys.modules[self.__class__.__module__].__file__)
        path, filename = os.path.split(full_path)
        return path.split('/')[-1]

    def generateRandomString(self, length=25):
        return passgen.passgen(length=length, puncuation=True, digits=True, letters=True, case='both')

    def register(self, db, loadedPlugins):
        self.db = db
        self.loadedPlugins = loadedPlugins
        if Module.select().where(Module.name == self.getName()).count() == 0:
            db.create_tables(self.pluginModels)
            self.module = Module.create(name = self.getName(), version = self.version)
        else:
            self.module = Module.select().where(Module.name == self.getName()).get()
            if self.module.version < self.version:
                print("Update to Module Needed....")
        
        self.__registerConfigSettings__()

    def __registerConfigSettings__(self):
        for key in self.config:
            if Settings.select().where(Settings.plugin == self.module, Settings.key == key).count() == 0:
                Settings.create(plugin = self.module, key = key, value=str(self.config[key]))
                print("Added [%s] (%s) Setting With Value: %s From Plugin Config YML" % (self.getName(), key, self.config[key]))
        
    def help(self):
        for command in self.availableCommands:
            print("%s   -> %s" % (command,self.availableCommands[command]))
