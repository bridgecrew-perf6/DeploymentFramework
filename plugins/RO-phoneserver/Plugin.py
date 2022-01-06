from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import requests, time

from . import functions as ROPhoneserverFunctions

class Plugin(BasePlugin):

    # could be 30; but 40
    priority = 40

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'db_name',
                'message': '[%s] New MYSQL database name:' % str.upper(self.getName()),
                'default': 'asterisk'
            },
            {
                'type': 'input',
                'name': 'db_user',
                'message': '[%s] New MYSQL user name:' % str.upper(self.getName()),
                'default': 'asterisk'
            },
            {
                'type': 'password',
                'name': 'db_pass',
                'message': '[%s] New MYSQL user\'s password:' % str.upper(self.getName())
            },

        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question['name']):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        paths = [
            'storage/phoneserver/certs',
            'storage/phoneserver/data',
            'storage/phoneserver/logs',
            'storage/phoneserver/data',
            'storage/phoneserver/assets',
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROPhoneserverFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):

        contents = ROPhoneserverFunctions.envFile(self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))
        self.writeContentsToFile(contents, 'envs/phoneserver.env', install_dir)

        if self.promptRequired('db-created'):
            self.events.emit("RO.mariadb.createDatabase", self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))
            Settings.create(plugin = self.module, key = 'db-created', value='True')

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return

        self.events.emit('RO.proxy.createHost', 'phone', 'phoneserver', '80', 'http')
        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "phoneserver")

        self.waitForReady()

    def waitForReady(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://phone.%s' % domain, verify=False)
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