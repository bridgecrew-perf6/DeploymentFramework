from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os

class Plugin(BasePlugin):
    priority = -100

    version = 1.0

    listenForEvents = {
        'default': 'defaultCommandFunction',
    }

    availableCommands = {
        'default': 'Runs a Sample Default Command',
    }

    pluginModels = []

    def help(self):
        print("Sample Help Information In Addition to the displaying of commands....")
        super().help()

    def defaultCommandFunction(self):
        print("Example Function For 'default' Command.")
