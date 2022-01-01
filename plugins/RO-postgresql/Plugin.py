from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as ROPostgresqlFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.postgresql.createDatabase': 'createDatabase',
    }

    availableCommands = {
        'RO.postgresql.createDatabase': 'Create a new Database'
    }

    # The RO Base is 0; We need to be above that...
    priority = 10

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'default_database',
                'message': '[%s] New POSTGRESQL database name:' % str.upper(self.getName()),
                'default': 'itsupport'
            },
            {
                'type': 'input',
                'name': 'default_user',
                'message': '[%s] New POSTGRESQL user name:' % str.upper(self.getName()),
                'default': 'itsupport'
            },
            {
                'type': 'password',
                'name': 'default_password',
                'message': '[%s] New POSTGRESQL user\'s password:' % str.upper(self.getName())
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
            'init/postgresql',
            'storage/postgresql/data'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROPostgresqlFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        contents = ROPostgresqlFunctions.envFile(self.getSetting('default_database'), self.getSetting('default_user'), self.getSetting('default_password'))
        self.writeContentsToFile(contents, 'envs/postgresql.env', install_dir)
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "postgresql")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        Settings.create(plugin = self.module, key = 'post-launch', value='True')

    def createDatabase(self, db_name, db_user=None, db_password=None):
        if type(db_name) == type([]):
            db_user = db_name[1]
            db_password = db_name[2]
            db_name = db_name[0]

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        install_dir = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'install_dir').get().value
        content = ROPostgresqlFunctions.dbsql(db_name, db_user, db_password)

        # See if the postLaunchConfig has been run...
        if self.promptRequired('post-launch'):
            # It hasn't been run yet...
            self.writeContentsToFile(content, 'init/postgresql/%s.sh' % db_name, install_dir)
        else:
            print("TODO: preform docker command to create the database...")