import requests, time
from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as ROCloudFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.cloud.enableApp': 'enableApp',
        'RO.cloud.setAppSetting': 'setAppSetting'
    }

    availableCommands = {
        'RO.cloud.enableApp': 'Enable an app in the Cloud',
        'RO.cloud.setAppSetting': 'Configures a specific setting for an app'
    }

    # The RO Base is 0; We need to be above that...
    priority = 30

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'admin_user',
                'message': '[%s] New Admin User' % self.getName(),
                'default': 'cloud'
            },
            {
                'type': 'password',
                'name': 'admin_pass',
                'message': '[%s] New Admin Password' % self.getName(),
            },
            {
                'type': 'input',
                'name': 'db_name',
                'message': '[%s] New POSTGRESQL Database for Cloud' % self.getName(),
                'default': 'cloud'
            },
            {
                'type': 'input',
                'name': 'db_user',
                'message': '[%s] New POSTGRESQL User for Cloud' % self.getName(),
                'default': 'cloud'
            },
            {
                'type': 'password',
                'name': 'db_pass',
                'message': '[%s] New Password for POSTGRESQL User' % self.getName(),
            },
            {
                'type': 'password',
                'name': 'ldap_pass',
                'message': '[%s] New Password For CLOUD-BIND ldap account' % self.getName()
            }

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
            'storage/cloud'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROCloudFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):

        if self.promptRequired('ldap-created'):
            self.events.emit('RO.postgresql.createDatabase', self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))
            Settings.create(plugin = self.module, key = 'ldap-created', value='True')
        


        if self.promptRequired('db-created'):
            self.events.emit('RO.ldap.createServiceAccount', 'CLOUD-BIND', self.getSetting('ldap_pass'))
            Settings.create(plugin = self.module, key = 'db-created', value='True')
        

        # ENV File
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        
        contents = ROCloudFunctions.envFile(self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'), self.getSetting('admin_user'), self.getSetting('admin_pass'), domain)
        self.writeContentsToFile(contents, 'envs/cloud.env', install_dir)
        



    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return
        

        self.events.emit('RO.proxy.createHost', 'cloud', 'cloud', '80', 'http')
        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "cloud")
        
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://cloud.%s' % domain, verify=False)
            status = r.status_code
            if status != 200:
                print(status)
                time.sleep(5)

    def waitForReady(self):
        print("Waiting for Cloud...", end="")
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://cloud.%s' % domain, verify=False)
            status = r.status_code
            if status != 200:
                print(".", end="")
                time.sleep(5)
        print("")

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        # TALK Server
        self.enableApp('spreed')

        # Group Folders
        self.enableApp('groupfolders')

        # Tasks
        self.enableApp('tasks')

        # calendar
        self.enableApp('calendar')

        # SAML
        self.enableApp('user_saml')

        self.events.emit("RO.sso.createSAMLPropertyMapping",
            'Nextcloud SAML Group Mapping',
            """for group in user.ak_groups.all():
    yield group.name
if ak_is_group_member(request.user, name="Administrators"):
    yield "admin"
if ak_is_group_member(request.user, name="Cloud Admins"):
    yield "admin"
""",
            'http://schemas.xmlsoap.org/claims/Group'
        )

        self.events.emit("RO.sso.createSAMLApplication", 
                "Cloud",
                "cloud",
                "https://cloud.%s" % domain, 
                "Document Cloud",
                "https://cloud.%s/apps/user_saml/saml/acs" % domain,
                'https://cloud.%s/apps/user_saml/saml/metadata' % domain,
                "post"
        )


        ROssoModule = Module.select().where(Module.name == 'RO-sso').get()
        cert = Settings.select().where(Settings.plugin == ROssoModule, Settings.key == 'default-cert').get().value
        settings = {
            "providerIds": "1",
            "general-use_saml_auth_for_desktop": "1",
            "general-allow_multiple_user_back_ends": "0",
            "general-uid_mapping": "http://schemas.goauthentik.io/2021/02/saml/username",
            "general-idp0_display_name": "SSO",
            "idp-entityId": "https://sso.%s" % domain,
            "idp-singleSignOnService.url": "https://sso.%s/application/saml/cloud/sso/binding/redirect/" % domain,
            "idp-singleLogoutService.url": "https://sso.%s/if/session-end/cloud/" % domain,
            "idp-singleLogoutService.responseUrl": "https://sso.%s/if/session-end/cloud/" % domain,
            "idp-x509cert": "%s" % cert.replace('\n','').replace('\r','').replace(" ","%%SPACE%"),
            "saml-attribute-mapping-displayName_mapping": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
            "saml-attribute-mapping-email_mapping": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "saml-attribute-mapping-group_mapping": "http://schemas.xmlsoap.org/claims/Group",
            "enabled": "yes",
            "type": "saml"
        }
        for setting in settings:
            self.events.emit("RO.command.user", "cloud", "www-data", "php occ config:app:set --value=%s user_saml %s" % (settings[setting], setting))


        Settings.create(plugin = self.module, key = 'post-launch', value='True')

    def enableApp(self, app_name):
        self.events.emit("RO.command.user", "cloud", "www-data", "php occ app:enable %s -f" % app_name)

    def setAppSetting(self, app_name, setting, value):
        self.events.emit("RO.command.user", "cloud", "www-data", "php occ config:app:set --value=%s %s %s" % (value, app_name, setting))