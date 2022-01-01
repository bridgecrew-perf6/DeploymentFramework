from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Module import Module
from core.models.Settings import Settings

from . import functions as ROSSOFunctions

class Plugin(BasePlugin):

    # listenForEvents = {
    #     'RO.mariadb.createDatabase': 'createDatabase',
    # }

    # availableCommands = {
    #     'RO.mariadb.createDatabase': 'Create a new Database'
    # }

    # Requires Redis + PostGresql + LDAP + Proxy
    priority = 20

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'image',
                'message': '[SSO] Image',
                'default': 'goauthentik.io/server'
            },
            {
                'type': 'input',
                'name': 'tag',
                'message': '[SSO] Tag',
                'default': '2021.12.4'
            },
            {
                'type': 'input',
                'name': 'db_name',
                'message': '[SSO] New POSTGRESQL Database for SSO Service',
                'default': 'authentik'
            },
            {
                'type': 'input',
                'name': 'db_user',
                'message': '[SSO] New POSTGRESQL User for SSO Service',
                'default': 'authentik'
            },
            {
                'type': 'password',
                'name': 'db_pass',
                'message': '[SSO] New Password for SSO Service POSTGRESQL User',
            },
                        {
                'type': 'password',
                'name': 'secret_key',
                'message': '[SSO] New Secret Key',
            },
            {
                'type': 'password',
                'name': 'admin_pass',
                'message': '[SSO] New Password for "akadmin"',
            },
            {
                'type': 'password',
                'name': 'admin_token',
                'message': '[SSO] New API Token for "akadmin"',
            },
            {
                'type': 'password',
                'name': 'ldap_password',
                'message': '[SSO] New Password for SSO-Bind LDAP account',
            }
            

        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question['name']):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)


    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        paths = [
            'storage/sso/media',
            'storage/sso/custom-templates',
            'storage/sso/backups'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROSSOFunctions.dockerFile(self.getSetting('image'), self.getSetting('tag'))
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        self.events.emit('RO.postgresql.createDatabase', self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))

        self.events.emit('RO.ldap.createServiceAccount', 'SSO-BIND', self.getSetting('ldap_password'))

        contents = ROSSOFunctions.envFile(self.getSetting('secret_key'), self.getSetting('admin_pass'), 
            self.getSetting('admin_token'), self.getSetting('db_user'), self.getSetting('db_name'), self.getSetting('db_pass')
        )
        self.writeContentsToFile(contents, './envs/sso.env', install_dir)

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        
        self.events.emit('RO.proxy.createHost', 'sso', 'sso-server', '9443')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "sso-server")
        self.events.emit("RO.launch", "sso-worker")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        ROldapModule = Module.select().where(Module.name == 'RO-ldap').get()
        base_dn = Settings.select().where(Settings.plugin == ROldapModule, Settings.key == 'base_dn').get().value

        ROSSOFunctions.configureLDAPSource(domain, self.getSetting('admin_token'), base_dn, self.getSetting('ldap_password'))

        Settings.create(plugin = self.module, key = 'post-launch', value='True')