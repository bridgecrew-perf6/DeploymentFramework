from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as ROProxyFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        #'RO.postgresql.createDatabase': 'createDatabase',
    }

    availableCommands = {
        #'RO.postgresql.createDatabase': 'Create a new Database'
    }

    # The RO mariadb is 10; We need to be above that...
    priority = 20

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'new_email',
                'message': '[%s] New email for login:' % str.upper(self.getName()),
                'default': 'admin@%s' % domain
            },
            {
                'type': 'password',
                'name': 'database_user',
                'message': '[%s] New password for login:' % str.upper(self.getName()),
            },
            {
                'type': 'input',
                'name': 'database_name',
                'message': '[%s] New database name:' % str.upper(self.getName()),
                'default': 'proxy'
            },
            {
                'type': 'input',
                'name': 'database_user',
                'message': '[%s] New user name:' % str.upper(self.getName()),
                'default': 'proxy'
            },
            {
                'type': 'password',
                'name': 'database_password',
                'message': '[%s] New user\'s password:' % str.upper(self.getName())
            },

        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question['name']):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        # The paths the plugin needs to ensure exist
        paths = [
            'storage/proxy/data',
            'storage/proxy/letsencrypt'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROProxyFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        contents = ROProxyFunctions.envFile(self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
        self.writeContentsToFile(contents, 'envs/proxy.env', install_dir)

        self.events.emit("RO.mariadb.createDatabase", self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "proxy")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if self.promptRequired('post-launch'):
            Settings.create(plugin = self.module, key = 'post-launch', value='True')