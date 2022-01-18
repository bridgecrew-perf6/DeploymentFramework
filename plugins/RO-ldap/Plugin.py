import os
from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import time

from . import functions as ROLdapFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.ldap.createServiceAccount': 'createServiceAccount',
        'RO.ldap.waitForReady': 'waitToBeReady'
    }

    availableCommands = {
        'RO.ldap.createServiceAccount': 'Create a new service account',
        'RO.ldap.waitForReady' : 'Wait and ensure LDAP is ready'
    }

    # The RO Base is 0; We need to be above that...
    priority = 10

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        domainSplit = domain.split('.')
        basedn=""
        for part in domainSplit:
            basedn = basedn + "dc=" + part +","

        basedn=basedn[:-1]

        Settings.create(plugin = self.module, key = 'base_dn', value = basedn)

        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'organization_name',
                'message': '[%s] Name of the Organization:' % str.upper(self.getName()),
                'default': 'Sniper7Kills LLC'
            },
            {
                'type': 'password',
                'name': 'admin_pass',
                'message': '[%s] Default Admin User Password:' % str.upper(self.getName()),
            },
            {
                'type': 'password',
                'name': 'config_pass',
                'message': '[%s] Default Config User Password:' % str.upper(self.getName())
            },
            {
                'type': 'password',
                'name': 'it_password',
                'message': '[%s] Default itsupport@%s Password:' % (str.upper(self.getName()), domain)
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
            'storage/ldap/data',
            'storage/ldap/config',
            'init/ldap/ldifs',
            'storage/ldap/certs',
            'storage/ldap/backup'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        contents = ROLdapFunctions.dockerFile(domain)
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        contents = ROLdapFunctions.envFile(domain, self.getSetting('organization_name'), self.getSetting('admin_pass'),self.getSetting('config_pass'),)
        self.writeContentsToFile(contents, 'envs/ldap.env', install_dir)
    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return
        # Get Domain
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        # postfix schema
        contents = ROLdapFunctions.postfixSchema()
        self.writeContentsToFile(contents, 'init/ldap/ldifs/postfix.schema', install_dir)

        # permissions schema
        contents = ROLdapFunctions.permissionsSchema(self.getSetting('base_dn'))
        self.writeContentsToFile(contents, 'init/ldap/ldifs/permissions.schema', install_dir)

        # Initial ldif population
        contents = ROLdapFunctions.initialLDIF(self.getSetting('base_dn'), domain, self.getSetting('it_password'))
        self.writeContentsToFile(contents, 'init/ldap/ldifs/initial.load', install_dir)

        Settings.create(plugin = self.module, key = 'pre-launch', value='True')
        

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "ldap")
        time.sleep(5)
        self.waitToBeReady()
        pass

    def waitToBeReady(self):
        command = "ldapsearch -b %s -H ldapi://" % self.getSetting('base_dn')
        print("[%s] Waiting for LDAP to be Ready..." % self.getName(), end="", flush=True)
        ready = False
        while not ready:
            try:
                self.events.emit("RO.command", "ldap", command)
                ready=True
            except:
                print(".", end='', flush=True)
                time.sleep(2)
        print()

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        

        # Ensure we can connect

        # Inject postfix Schema w/ Config Account (Its already converted)
        self.waitToBeReady()
        print("postfix.schema")
        self.events.emit(
            'RO.command', 
            'ldap', 
            'ldapadd -H ldapi:/// -D cn=config -w %s -f /assets/S7K-LDIF/postfix.schema' % self.getSetting('config_pass')
        )

        self.waitToBeReady()
        print("initial.load")
        self.events.emit(
            'RO.command', 
            'ldap', 
            'ldapadd -H ldapi:/// -D cn=admin,%s -w %s -f /assets/S7K-LDIF/initial.load' % (self.getSetting('base_dn'), self.getSetting('admin_pass'))
        )

        # Inject remaining LDIFS in folder
        for x in os.listdir(install_dir + '/init/ldap/ldifs'):
            if x.endswith(".ldif"):
            # Prints only text file present in My Folder
                try:
                    print(x)
                    self.waitToBeReady()
                    self.events.emit(
                        'RO.command', 
                        'ldap', 
                        'ldapadd -H ldapi:/// -D cn=admin,%s -w %s -f /assets/S7K-LDIF/%s' % (self.getSetting('base_dn'), self.getSetting('admin_pass'), x)
                    )
                except:
                    print("ERROR LOADING LDIF %s" % x)
                    exit()

        self.waitToBeReady()
        print("permissions.schema")
        self.events.emit(
            'RO.command', 
            'ldap', 
            'ldapadd -H ldapi:/// -D cn=config -w %s -f /assets/S7K-LDIF/permissions.schema' % self.getSetting('config_pass')
        )
        
        Settings.create(plugin = self.module, key = 'post-launch', value='True')

    def createServiceAccount(self, user_name, user_password=None):
        if type(user_name) == type([]):
            user_password = user_name[1]
            user_name = user_name[0]

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        install_dir = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'install_dir').get().value
        content = ROLdapFunctions.serviceAccountLDIF(self.getSetting('base_dn'), user_name, user_password)

        self.writeContentsToFile(content, 'init/ldap/ldifs/%s.ldif' % user_name, install_dir)

        # See if the postLaunchConfig has been run...
        if not self.promptRequired('post-launch'):
            # It has... So we need to connect to the docker container to run it.
            print("TODO: preform docker command to create the database...")