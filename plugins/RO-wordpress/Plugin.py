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
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'database_name',
                'message': '[%s] New MYSQL database name:' % str.upper(self.getName()),
                'default': 'wordpress'
            },
            {
                'type': 'input',
                'name': 'database_user',
                'message': '[%s] New MYSQL user name:' % str.upper(self.getName()),
                'default': 'wordpress'
            },
            {
                'type': 'password',
                'name': 'database_password',
                'message': '[%s] New MYSQL user\'s password:' % str.upper(self.getName())
            },
            {
                'type': 'input',
                'name': 'title',
                'message': '[%s] Site Title:' % str.upper(self.getName()),
                'default': '%s LLC' % domain
            },
            {
                'type': 'input',
                'name': 'admin_user',
                'message': '[%s] Default Admin Username:' % str.upper(self.getName()),
                'default': 'admin'
            },
            {
                'type': 'input',
                'name': 'admin_email',
                'message': '[%s] Default Admin Email:' % str.upper(self.getName()),
                'default': 'itsupport@%s' % domain
            },
            {
                'type': 'password',
                'name': 'admin_password',
                'message': '[%s] Default Admin Password:' % str.upper(self.getName()),
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
        paths = [
            'storage/wordpress/html',
            'storage/wordpress/themes',
            'storage/wordpress/plugins'
        ]
        self.createFolders(paths, install_dir)
        pass

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROWordpressFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        contents = ROWordpressFunctions.envFile(self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
        self.writeContentsToFile(contents, 'envs/wordpress.env', install_dir)

        if self.promptRequired('db-created'):
            self.events.emit("RO.mariadb.createDatabase", self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
            Settings.create(plugin = self.module, key = 'db-created', value='True')
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return

        self.events.emit('RO.proxy.createHost', 'www', 'wordpress', '80', 'http')
        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "wordpress")
        
        self.waitForReady()

    def waitForReady(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://www.%s' % domain, verify=False)
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

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value


        self.events.emit('RO.sso.createOauthApplication', 'Wordpress', 'wordpress', 'https://www.%s' % domain, 'Public Website', self.getSetting('client_id'), self.getSetting('client_secret'), 'https://www.%s/wp-admin/admin-ajax.php?action=openid-connect-authorize' % domain)

        SSOSettings = {
            'login_type': 'auto',
            'client_id': self.getSetting('client_id'),
            'client_secret': self.getSetting('client_secret'),
            'scope': 'email profile openid',
            'endpoint_login': 'https://sso.%s/application/o/authorize/' % domain,
            'endpoint_userinfo': 'https://sso.%s/application/o/userinfo/' % domain,
            'endpoint_token': 'https://sso.%s/application/o/token/' % domain,
            'endpoint_end_session': 'https://sso.%s/application/o/wordpress/end-session/' % domain,
            'identity_key': 'preferred_username',
            'no_sslverify': '1',
            'http_request_timeout': '5',
            'enforce_privacy': '0',
            'alternate_redirect_uri': '0',
            'nickname_key': 'preferred_username',
            'email_format': '{email}',
            'displayname_format': '',
            'identify_with_username': '0',
            'state_time_limit': '',
            'token_refresh_enable': '1',
            'link_existing_users': '1',
            'create_if_does_not_exist': '1',
            'redirect_user_back': '1',
            'redirect_on_logout': '1',
            'enable_logging': '0',
            'log_limit': '1000'
        }

        commands = [
            "curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar",
            "chmod +x ./wp-cli.phar",
            "./wp-cli.phar core install --url=https://www.%s --title=%s --admin_user=%s --admin_email=%s --admin_password=%s" % (
                domain, self.getSetting('title').replace(' ','%%SPACE%'), self.getSetting('admin_user'), self.getSetting('admin_email'), self.getSetting('admin_password')
            ),
            "./wp-cli.phar plugin install daggerhart-openid-connect-generic",
            "./wp-cli.phar plugin activate daggerhart-openid-connect-generic",
            "./wp-cli.phar option set openid_connect_generic_settings %s --format=json --autoload=yes" % json.dumps(SSOSettings).replace(' ','%%SPACE%')

        ]
        for command in commands:
            self.events.emit("RO.command.user", "wordpress", "www-data", command)

            

        Settings.create(plugin = self.module, key = 'post-launch', value='True')

        

