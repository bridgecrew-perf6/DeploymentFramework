from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import requests
import time
import os

from . import functions as ROProxyFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.proxy.createHost': 'createHost',
    }

    availableCommands = {
        #'RO.postgresql.createDatabase': 'Create a new Database'
    }

    # The RO mariadb is 10; We need to be above that...
    priority = 20

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'input',
                'name': 'new_email',
                'message': '[%s] New email for login:' % str.upper(self.getName()),
                'default': 'admin@%s' % domain
            },
            {
                'type': 'password',
                'name': 'new_pass',
                'message': '[%s] New password for login:' % str.upper(self.getName()),
            },
            {
                'type': 'input',
                'name': 'database_name',
                'message': '[%s] New database name:' % str.upper(self.getName()),
                'default': 'proxy'
            },
            {
                'type': 'input',
                'name': 'database_user',
                'message': '[%s] New database user name:' % str.upper(self.getName()),
                'default': 'proxy'
            },
            {
                'type': 'password',
                'name': 'database_password',
                'message': '[%s] New database user password:' % str.upper(self.getName())
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
            'storage/proxy/data',
            'storage/proxy/letsencrypt'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROProxyFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # ENV File
        contents = ROProxyFunctions.envFile(self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
        self.writeContentsToFile(contents, 'envs/proxy.env', install_dir)

        self.events.emit("RO.mariadb.createDatabase", self.getSetting('database_name'), self.getSetting('database_user'), self.getSetting('database_password'))
        


    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "proxy")
        time.sleep(2)

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        self.updateDefaultUser()

        Settings.create(plugin = self.module, key = 'post-launch', value='True')

    def updateDefaultUser(self):
        token = None
        while token is None:
            token = ROProxyFunctions.getToken(user_name = 'admin@example.com', user_password = 'changeme')
        print()
        
        print("[%s] Updating Username"%self.getName())
        username_update_data={
            'name': 'IT Support',
            'nickname': 'Admin',
            'email': '%s' % self.getSetting('new_email'),
            'roles': ['admin'],
            'is_disabled': False
        }
        r = requests.put('http://127.0.0.1:81/api/users/1', json=username_update_data, headers={'Authorization': 'Bearer %s' % token} )

        print("[%s] Updating Password"%self.getName())
        password_update_data={
            'type': 'password',
            'current': 'changeme',
            'secret': '%s' % self.getSetting('new_pass')
        }
        r = requests.put('http://127.0.0.1:81/api/users/1/auth', json=password_update_data, headers={'Authorization': 'Bearer %s' % token} )

    def createHost(self, subdomain, host, port, scheme='https', cert=None):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        token = ROProxyFunctions.getToken(user_name = self.getSetting('new_email'), user_password = self.getSetting('new_pass'))

        if cert is None:
            if os.path.exists('./certs/%s' % subdomain + '.' + domain):
                cert = self.importCertificate(subdomain + '.' + domain)
            else:
                cert='new'

        payload = {
            "domain_names": ["%s.%s" % (subdomain, domain)],
            "forward_scheme": scheme,
            "forward_host": host,
            "forward_port": port,
            "allow_websocket_upgrade": True,
            "access_list_id": "0",
            "certificate_id": cert,
            "meta": {
                "letsencrypt_email": "itsupport@%s" % domain,
                "letsencrypt_agree": True,
                "dns_challenge": False
            },
            "advanced_config": "",
            "locations": [],
            "block_exploits": False,
            "caching_enabled": False,
            "http2_support": True,
            "hsts_enabled": True,
            "hsts_subdomains": False,
            "ssl_forced": True
        }

        r = requests.post("http://127.0.0.1:81/api/nginx/proxy-hosts", json=payload, headers={'Authorization': 'Bearer %s' % token})
        if r.status_code != 201:
            print("Error Creating Proxy Host %s.%s" % (subdomain, domain))
            print(r.json())
            exit()

    def importCertificate(self, certName):
        token = ROProxyFunctions.getToken(user_name = self.getSetting('new_email'), user_password = self.getSetting('new_pass'))
        payload = {
            "nice_name": certName,
            "provider": "other"
        }
        response = requests.post("http://127.0.0.1:81/api/nginx/certificates", json=payload, headers={"Authorization": "Bearer %s" % token})
        if response.status_code != 201:
            print("  [PROXY] Error Creating Cert Entry...")
            exit()
        certID = response.json()['id']

        url = "http://127.0.0.1:81/api/nginx/certificates/%s/upload" % certID

        headers = {
            "Authorization": "Bearer %s" % token
        }
        files = {
            'certificate': open('./certs/%s' % certName,'rb'),
            'certificate_key': open('./certs/%s.key' % certName,'rb'),
        }
        response = requests.request("POST", url, files=files, headers=headers)
        if response.status_code != 200:
            print("  [PROXY] Error Uploading to Cert Entry...")
            exit()

        return certID