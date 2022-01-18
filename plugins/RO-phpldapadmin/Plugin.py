from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import time

from . import functions as ROPhpLDAPAdminFunctions

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
        # questions = [
        #     # REF: https://github.com/CITGuru/PyInquirer/
        #     {
        #         'type': 'password',
        #         'name': 'ldap_password',
        #         'message': '[%s] New LDAPADMIN-BIND user password:' % str.upper(self.getName())
        #     },
        # ]
        
        # questionsToAsk = []
        # for question in questions:
        #     if self.promptRequired(question['name']):
        #         questionsToAsk.append(question)

        # self.preformPrompts(questionsToAsk)
        pass

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        # The paths the plugin needs to ensure exist
        paths = [
            'storage/ldap-admin',
            'init/ldap-admin',
            'init/ldap-admin/templates'
        ]
        self.createFolders(paths, install_dir)
        pass

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROPhpLDAPAdminFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # Initial Config
        ROldapModule = Module.select().where(Module.name == 'RO-ldap').get()
        base_dn = Settings.select().where(Settings.plugin == ROldapModule, Settings.key == 'base_dn').get().value

        # bind_id = "cn=%s,ou=Service,ou=Accounts,%s" % ("LDAPADMIN-BIND", base_dn)
        bind_pass = Settings.select().where(Settings.plugin == ROldapModule, Settings.key == 'admin_pass').get().value
        contents = ROPhpLDAPAdminFunctions.configFile('cn=admin,%s'% base_dn, bind_pass)
        self.writeContentsToFile(contents, 'init/ldap-admin/config.php', install_dir)

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        contents = ROPhpLDAPAdminFunctions.UserTemplate(domain)
        self.writeContentsToFile(contents, 'init/ldap-admin/templates/custom_User.xml', install_dir)

        contents = ROPhpLDAPAdminFunctions.GroupTemplate()
        self.writeContentsToFile(contents, 'init/ldap-admin/templates/custom_Group.xml', install_dir)

        # if self.promptRequired('ldap-created'):
        #     self.events.emit('RO.ldap.createServiceAccount', 'LDAPADMIN-BIND', self.getSetting('ldap_password'))
        #     Settings.create(plugin = self.module, key = 'ldap-created', value='True')
        
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return

        
        

        advanceProxyConfig = ROPhpLDAPAdminFunctions.getAdvanceConfig()
        self.events.emit('RO.proxy.createHost', 'ldapadmin', 'phpldapadmin', '443', 'https', None, advanceProxyConfig)
        
        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "phpldapadmin")
        time.sleep(5)
        self.events.emit("RO.launch", "phpldapadmin")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        self.events.emit('RO.sso.createProxyApplication', 'LDAP Admin', 'ldapadmin', 'https://ldapadmin.%s' % domain, 'Manage Accounts')
        Settings.create(plugin = self.module, key = 'post-launch', value='True')