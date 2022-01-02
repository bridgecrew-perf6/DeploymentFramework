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
        'docker.exec.user': 'executeDockerCommandAsUser',
        'docker.stop': 'stopDockerContainer',
        'docker.rebuild': 'rebuildDockerContainer',
        'docker.down':  'downDockerEnvironment'
    }

    availableCommands = {
        'docker.start': 'Start a specific docker container',
        'docker.stop': 'Stop a specific docker container',
        'docker.rebuild': 'Stop; pull/build/update image; Start',
        'docker.down': 'Stop all containers in an environment'
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
            return_code = -1
            
        if return_code != 0:
            print("Error Starting Container...")
            exit()

    def executeDockerCommand(self, launch_location, container_name, command):
        command = command.split(" ")
        launchCommand = ["docker-compose","exec", container_name]
        for word in command:
            launchCommand.append(word)

        try:
            result = subprocess.Popen(launchCommand, cwd=launch_location, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            text = result.communicate()[0]
            return_code = result.returncode
        except Exception as e:
            raise e

        if return_code != 0:
            raise Exception("Non 0 Return")

    def executeDockerCommandAsUser(self, launch_location, container_name, user, command):
        command = command.split(" ")
        launchCommand = ["docker-compose","exec", "--user", user, container_name]
        for word in command:
            launchCommand.append(word.replace("%%SPACE%", " "))
        try:
            print(launchCommand)
            result = subprocess.Popen(launchCommand, cwd=launch_location, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            text = result.communicate()[0]
            return_code = result.returncode
        except Exception as e:
            raise e

        if return_code != 0:
            print("Error Executing Docker Command")
            print("Result: [%s] %s" % (return_code, text))
            #exit()

    def stopDockerContainer(self, launch_location, container_name):
        pass

    def rebuildDockerContainer(self, launch_location, container_name=None):
        pass

    def downDockerEnvironment(self, launch_location):
        try:
            result = subprocess.Popen(["docker-compose", "down"], cwd=launch_location)
            text = result.communicate()[0]
            return_code = result.returncode
        except Exception as e:
            raise e
            
        if return_code != 0:
            print("Error Executing Docker Command")
            print("Result: [%s] %s" % (return_code, text))
            exit()