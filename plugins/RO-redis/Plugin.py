from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as RORedisFunctions

class Plugin(BasePlugin):

    # listenForEvents = {
    #     'RO.mariadb.createDatabase': 'createDatabase',
    # }

    # availableCommands = {
    #     'RO.mariadb.createDatabase': 'Create a new Database'
    # }

    # The RO Base is 0; We need to be above that...
    priority = 10

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        pass

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        pass

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = RORedisFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        pass

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "redis")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        Settings.create(plugin = self.module, key = 'post-launch', value='True')