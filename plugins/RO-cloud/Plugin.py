import requests, time
from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as ROCloudFunctions

class Plugin(BasePlugin):

    # listenForEvents = {
    #     'RO.mariadb.createDatabase': 'createDatabase',
    # }

    # availableCommands = {
    #     'RO.mariadb.createDatabase': 'Create a new Database'
    # }

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
                'message': '[%s] New Admin User' % domain,
                'default': 'cloud'
            },
            {
                'type': 'input',
                'name': 'admin_pass',
                'message': '[%s] New Admin Password' % domain,
                'default': 'cloud'
            },
            {
                'type': 'input',
                'name': 'db_name',
                'message': '[%s] New POSTGRESQL Database for Cloud' % domain,
                'default': 'cloud'
            },
            {
                'type': 'input',
                'name': 'db_user',
                'message': '[%s] New POSTGRESQL User for Cloud' % domain,
                'default': 'cloud'
            },
            {
                'type': 'password',
                'name': 'db_pass',
                'message': '[%s] New Password for User' % domain,
            },
            {
                'type': 'password',
                'name': 'ldap_pass',
                'message': '[%s] New Password For CLOUD-BIND ldap account' % domain
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

        self.events.emit('RO.postgresql.createDatabase', self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))

        self.events.emit('RO.ldap.createServiceAccount', 'CLOUD-BIND', self.getSetting('ldap_pass'))

        # ENV File
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        
        contents = ROCloudFunctions.envFile(self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'), self.getSetting('admin_user'), self.getSetting('admin_pass'), domain)
        self.writeContentsToFile(contents, 'envs/cloud.env', install_dir)
        



    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return

        self.events.emit('RO.proxy.createHost', 'cloud', 'cloud', '80', 'http')
        pass

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

        # SAML
        self.events.emit("RO.command.user", "cloud", "www-data", "php occ app:enable user_saml -f")
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