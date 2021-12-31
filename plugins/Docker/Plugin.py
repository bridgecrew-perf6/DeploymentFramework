from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os
from core.models.Settings import Settings

class Plugin(BasePlugin):
    priority = 0

    version = 1.0

    listenForEvents = {
        'docker.start': 'startDockerContainer',
        'docker.stop': 'stopDockerContainer',
        'docker.rebuild': 'rebuildDockerContainer'
    }

    def todo(self, args):
        print("... Docker Todo ...")

    availableCommands = {
        'docker.start': 'Start a specific docker container',
        'docker.stop': 'Stop a specific docker container',
        'docker.rebuild': 'Stop; pull/build/update image; Start'
    }

    pluginModels = []

    def help(self):
        print("-" * 50)
        print("Docker Plugin")
        super().help()
        print("-" * 50)

    def startDockerContainer(self, launch_location, container_name):
        print("[TODO] Start Docker Container In %s Named %s" % (launch_location, container_name))
        pass

    def stopDockerContainer(self, launch_location, container_name):
        pass

    def rebuildDockerContainer(self, launch_location, container_name=None):
        pass