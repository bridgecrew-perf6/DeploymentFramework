import os
from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import time

from . import functions as ROMailFunctions

class Plugin(BasePlugin):
    # Depends on SSO and LDAP
    priority = 30

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'password',
                'name': 'ldap_password',
                'message': '[%s] New Password for MAIL-BIND LDAP account:' % str.upper(self.getName()),
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
                'message': '[%s] New Password for MAIL-BIND LDAP account:' % str.upper(self.getName()),
                'default': self.generateRandomString(150)
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
            'storage/mailserver/mail',
            'storage/mailserver/state',
            'storage/mailserver/logs',
            'init/mailserver/config',
            'init/webmail/config'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        contents = ROMailFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        self.events.emit('RO.ldap.createServiceAccount', 'MAIL-BIND', self.getSetting('ldap_password'))

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        ROLdapModule = Module.select().where(Module.name == 'RO-ldap').get()
        base_dn = Settings.select().where(Settings.plugin == ROLdapModule, Settings.key == 'base_dn').get().value
        
        contents = ROMailFunctions.envFile(base_dn, self.getSetting('ldap_password'), domain)
        self.writeContentsToFile(contents, 'envs/mailserver.env', install_dir)

        contents = ROMailFunctions.authConf()
        self.writeContentsToFile(contents, 'init/mailserver/10-auth.conf', install_dir)

        contents = ROMailFunctions.postfixMain()
        self.writeContentsToFile(contents, 'init/mailserver/config/postfix-main.cf', install_dir)

    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        self.events.emit('RO.proxy.createHost', 'webmail', 'webmail', '80', 'http')
        self.events.emit('RO.sso.createOauthApplication', 'Email', 'email', 'https://webmail.%s' % domain, 'Roundcube Webmail Access to Email', self.getSetting('client_id'), self.getSetting('client_secret'), 'http://webmail.%s/index.php/login/oauth' % domain)

        
        contents = ROMailFunctions.webmailOAuth(domain, self.getSetting('client_id'), self.getSetting('client_secret'))
        self.writeContentsToFile(contents, 'init/webmail/config/oauth.php', install_dir)

        contents = ROMailFunctions.dovecotOAuth(domain, self.getSetting('client_id'), self.getSetting('client_secret'))
        self.writeContentsToFile(contents, 'init/mailserver/dovecot-oauth2.conf.ext', install_dir)

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        # Use the Docker Plugin to Launch a specific Container
        self.events.emit("RO.launch", "mailserver")
        self.events.emit("RO.launch", "webmail")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        # See preLaunchConfig
        pass