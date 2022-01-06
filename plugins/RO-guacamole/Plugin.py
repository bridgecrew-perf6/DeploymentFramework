from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import requests, time, json

from . import functions as ROWordpressFunctions

class Plugin(BasePlugin):

    # listenForEvents = {
    #     'RO.mariadb.createDatabase': 'createDatabase',
    # }

    # availableCommands = {
    #     'RO.mariadb.createDatabase': 'Create a new Database'
    # }

    # 
    priority = 40

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        

        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'database_name',
                'message': '[%s] New MYSQL database name:' % str.upper(self.getName()),
                'default': 'guacamole'
            },
            {
                'type': 'input',
                'name': 'database_user',
                'message': '[%s] New MYSQL user name:' % str.upper(self.getName()),
                'default': 'guacamole'
            },
            {
                'type': 'password',
                'name': 'database_password',
                'message': '[%s] New MYSQL user\'s password:' % str.upper(self.getName())
            },
            {
                'type': 'password',
                'name': 'client_id',
                'message': '[%s] New OAUTH Provider ID:' % str.upper(self.getName()),
                'default': self.generateRandomString(150)
            },
            {
                'type': 'password',
                'name': 'client_secret',
                'message': '[%s] New OAUTH Provider SECRET:' % str.upper(self.getName()),
                'default': self.generateRandomString(150)
            }
            
        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question['name']):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)
        pass

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        # # The paths the plugin needs to ensure exist
        # paths = [
        #     'storage/wordpress/html',
        #     'storage/wordpress/themes',
        #     'storage/wordpress/plugins'
        # ]
        # self.createFolders(paths, install_dir)
        pass

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROWordpressFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        # ENV File
        contents = ROWordpressFunctions.envFile(self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'), domain, self.getSetting('client_id'))
        self.writeContentsToFile(contents, 'envs/guacamole.env', install_dir)
        
        if self.promptRequired('db-created'):
            self.events.emit("RO.mariadb.createDatabase", self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
            Settings.create(plugin = self.module, key = 'db-created', value='True')
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return

        self.events.emit('RO.proxy.createHost', 'desktop', 'guacamole', '8080', 'http')

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        self.events.emit('RO.sso.createOauthApplication', 'Guacamole', 'guacamole', 'https://desktop.%s/guacamole' % domain, 'Remote Desktops', self.getSetting('client_id'), self.getSetting('client_secret'), 'https://desktop.%s/guacamole' % domain)

        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "guacd")
        self.events.emit("RO.launch", "guacamole")
        
        self.waitForReady()

    def waitForReady(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://desktop.%s/guacamole' % domain, verify=False)
            status = r.status_code
            if status != 200:
                print(status)
                time.sleep(5)

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        Settings.create(plugin = self.module, key = 'post-launch', value='True')

        

