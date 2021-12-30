from abc import abstractmethod
from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os
from core.models.Settings import Settings

class Template(BasePlugin):

    def __init__(self, events, config=...):
        # Add Remote Office Listeners and functions
        self.Events = {
            **self.Events, 
            **{
                'RO.prompts': 'preformOfficePrompts',
                'RO.folders': 'createFolderStructure',
                'RO.docker': 'appendDockerService',
                'RO.config': 'createInitialConfig',
            }
        }
        # Preform Parent Actions
        super().__init__(events, config=config)

    @abstractmethod
    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        pass

    # Check if the prompt is needed for the provided key
    # Or if we already have a saved value.
    def promptRequired(self, setting_key, module = None):
        if module == None:
            module = self.module
        # Return true if we have 0 records for the key
        return Settings.select().where(Settings.plugin == module, Settings.key == setting_key).count() == 0

    # Preform the Prompts; and Update the settings
    def preformPrompts(self, questions = []):
        # Preform the prompts and get answers
        answers = prompt(questions)
        # Loop though each answer
        for answer in answers:
            tmp = answers[answer]
            # Check if its empty
            if len(tmp) == 0:
                # Create a random string if empty....
                tmp = self.generateRandomString()
            # Save the answer as a setting
            Settings.create(plugin = self.module, key = answer, value=tmp)

    # Get a specific setting
    def getSetting(self, setting_key, module = None):
        # Check if we need to prompt for this setting....
        if self.promptRequired(setting_key, module):
            # Return None if we do....
            return None
        # Otherwise Return the Setting
        return Settings.select().where(Settings.plugin == module, Settings.key == 'setting_key').get().value

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        pass

    # Ensures the paths provided exist as folders
    def createFolders(self, paths = [], install_dir = './office'):
        # Iterate though each path
        for path in paths:
            # Check if doesn't exist
            if not os.path.exists(install_dir+ '/' + path):
                # If it doesn't create it.
                os.makedirs(install_dir+ '/' + path)

    @abstractmethod
    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = './office/docker-compose.yml'):
        pass

    # Writes contents to file
    def writeContentsToFile(self, contents, file_name, install_dir = './office'):
        f = open(install_dir + '/' + file_name, "w")
        f.write(contents)
        f.close()

    # Appends content to file
    def appendContentsToFile(self, contents, file_name, install_dir = './office'):
        f = open(install_dir + '/' + file_name, "a")
        f.write(contents)
        f.close()

    @abstractmethod
    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        pass

    @abstractmethod
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        pass

    @abstractmethod
    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self, install_dir = './office'):
        pass

    @abstractmethod
    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        pass