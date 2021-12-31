from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import subprocess
import os
from core.models.Settings import Settings

class Plugin(BasePlugin):
    priority = 0

    version = 1.0

    listenForEvents = {
        'docker.start': 'startDockerContainer',
        'docker.exec': 'executeDockerCommand',
        'docker.stop': 'stopDockerContainer',
        'docker.rebuild': 'rebuildDockerContainer'
    }

    availableCommands = {
        'docker.start': 'Start a specific docker container',
        'docker.stop': 'Stop a specific docker container',
        'docker.rebuild': 'Stop; pull/build/update image; Start'
    }

    pluginModels = []

    def __init__(self, events, config=...):
        super().__init__(events, config=config)

        # Check and ensure we have docker-compose installed.
        try:
            result = subprocess.Popen(["docker-compose", "version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            text = result.communicate()
            return_code = result.returncode
        except Exception as e:
            return_code=-1
        if return_code != 0:
            print("[%s] ERROR! Unable to run 'docker-compose version' Do you have docker-compose installed?" % self.getName())
            if 'startupByPass' not in config.keys()  or config['startupByPass'] != True:
                exit()

        # Check to ensure we have permission to run "docker ps" and that we don't fail.
        try:
            result = subprocess.Popen(["docker", "ps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL )
            text = result.communicate()
            return_code = result.returncode
        except Exception as e:
            return_code=-1
        if return_code != 0:
            print("[%s] ERROR! Unable to run 'docker ps' Do you have proper permissions?" % self.getName())
            if 'startupByPass' not in config.keys() or config['startupByPass'] != True:
                exit()

    def help(self):
        print("-" * 50)
        print("Docker Plugin")
        super().help()
        print("-" * 50)

    def startDockerContainer(self, launch_location, container_name):
        #print("[TODO] Start Docker Container In %s Named %s" % (launch_location, container_name))
        launchCommand = ["docker-compose","up","-d", container_name]
        try:
            result = subprocess.Popen(launchCommand, cwd=launch_location)
            text = result.communicate()[0]
            return_code = result.returncode
        except Exception as e:
            print(e)
            return_code=-1
            
        if return_code != 0:
            print("Error Starting Container...")
            exit()

    def executeDockerCommand(self, launch_location, container_name, command):
        command = command.split(" ")
        launchCommand = ["docker-compose","exec",container_name]
        for word in command:
            launchCommand.append(word)

        # print("[TODO] Run Command in [%s] Container [%s] [%s]" % (launch_location, container_name, launchCommand))
        try:
            result = subprocess.Popen(launchCommand, cwd=launch_location)
            text = result.communicate()[0]
            return_code = result.returncode
        except Exception as e:
            print(e)
            return_code=-1
            
        if return_code != 0:
            print("Error Executing Command...")
            exit()

    def stopDockerContainer(self, launch_location, container_name):
        pass

    def rebuildDockerContainer(self, launch_location, container_name=None):
        pass