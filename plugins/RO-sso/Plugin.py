from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Module import Module
from core.models.Settings import Settings
import requests

from . import functions as ROSSOFunctions

class Plugin(BasePlugin):

    listenForEvents = {
        'RO.sso.createOauthApplication': 'createOauthApplication',
        'RO.sso.createSAMLApplication': 'createSAMLApplication',
        'RO.sso.createProxyApplication': 'createProxyApplication',
        'RO.sso.createSAMLPropertyMapping': 'createSAMLPropertyMapping'
    }

    availableCommands = {
        'RO.sso.createOauthApplication': 'Create a new OAuth based Application',
        'RO.sso.createSAMLApplication': 'Create a new SAML based Application',
        'RO.sso.createProxyApplication': 'Create a new Proxy Based Application',
        'RO.sso.createSAMLPropertyMapping': 'Create a New SAML Property Mapping'
    }

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
                'message': '[SSO] New Password for SSO-BIND LDAP account',
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
        if self.promptRequired('db-created'):
            self.events.emit('RO.postgresql.createDatabase', self.getSetting('db_name'), self.getSetting('db_user'), self.getSetting('db_pass'))
            Settings.create(plugin = self.module, key = 'db-created', value='True')
        
        if self.promptRequired('ldap-created'):
            self.events.emit('RO.ldap.createServiceAccount', 'SSO-BIND', self.getSetting('ldap_password'))
            Settings.create(plugin = self.module, key = 'ldap-created', value='True')

        contents = ROSSOFunctions.envFile(self.getSetting('secret_key'), self.getSetting('admin_pass'), 
            self.getSetting('admin_token'), self.getSetting('db_user'), self.getSetting('db_name'), self.getSetting('db_pass')
        )
        self.writeContentsToFile(contents, './envs/sso.env', install_dir)

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return
        
        self.events.emit('RO.proxy.createHost', 'sso', 'sso-server', '9443')

        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

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

        ROSSOFunctions.makeGroupAdmins(domain, self.getSetting('admin_token'), 'Administrators')
        ROSSOFunctions.makeGroupAdmins(domain, self.getSetting('admin_token'), 'SSO Admins')

        Settings.create(plugin = self.module, key = 'post-launch', value='True')


    def getDefaultFlowID(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        
        r = requests.get('https://sso.%s/api/v3/flows/instances/default-provider-authorization-implicit-consent/'% domain, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        return r.json()['pk']

    def getOauthPropertyMappings(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        
        r = requests.get('https://sso.%s/api/v3/propertymappings/all/?search=oauth'% domain, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        response = r.json()['results']
        keys = []
        for mapping in response:
            if "Proxy" not in mapping['name']:
                keys.append(mapping['pk'])
        return keys

    def createOauthProvider(self, name, client_id, client_secret, redirect_uri= None):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        data = {
            'name': '%s OAuth Provider' % name,
            'authorization_flow': self.getDefaultFlowID(),
            'property_mappings': self.getOauthPropertyMappings(),
            'client_type': 'confidential',
            'client_id': client_id,
            'client_secret': client_secret, 
            'issuer_mode': 'per_provider',
            'sub_mode': 'user_email',
            'include_claims_in_id_token': True,
            'token_validity': 'minutes=299'
        }
        if redirect_uri is not None:
                data['redirect_uris'] = redirect_uri
        r = requests.post('https://sso.%s/api/v3/providers/oauth2/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print(r.json())
            exit()
        else:
            provider_id = r.json()['pk']
            r = requests.get('https://sso.%s/api/v3/providers/oauth2/%s' % (domain, provider_id), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            r = requests.put('https://sso.%s/api/v3/providers/oauth2/%s' % (domain, provider_id), json=r.json(), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            return provider_id

    def getSAMLPropertyMappings(self, app_name):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        
        r = requests.get('https://sso.%s/api/v3/propertymappings/all/?search=SAML'% domain, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        response = r.json()['results']
        keys = []
        # Do not map these groups for these apps
        MappingExceptions = {
            'Cloud': ['authentik default SAML Mapping: Groups']
        }
        for mapping in response:
            if app_name in MappingExceptions.keys() and mapping['name'] not in MappingExceptions[app_name]:
                keys.append(mapping['pk'])
            elif app_name not in MappingExceptions.keys():
                keys.append(mapping['pk'])
        return keys

    def createSAMLPropertyMapping(self, name, expression, saml_name, friendly_name=None):
        data = {
            "name": name,
            "expression": expression,
            "saml_name": saml_name,
        }
        if friendly_name is not None:
            data["friendly_name"] = friendly_name

        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        r = requests.post('https://sso.%s/api/v3/propertymappings/saml/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print(r.json())
            exit()

    def createSAMLProvider(self, name, acs_url, audience, sp_binding):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        data = {
            'name': '%s SAML Provider' % name,
            'authorization_flow': self.getDefaultFlowID(),
            'property_mappings': self.getSAMLPropertyMappings(name),
            'acs_url': acs_url,
            'issuer': 'https://sso.%s' % domain,
            'sp_binding': sp_binding,
            'audience': audience,
            'signing_kp': self.getDefaultCertID()
        }

        r = requests.post('https://sso.%s/api/v3/providers/saml/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print(r.json())
            exit()
        else:
            provider_id = r.json()['pk']
            r = requests.get('https://sso.%s/api/v3/providers/saml/%s' % (domain, provider_id), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            r = requests.put('https://sso.%s/api/v3/providers/saml/%s' % (domain, provider_id), json=r.json(), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            return provider_id

    def getDefaultCertID(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        r = requests.get('https://sso.%s/api/v3/crypto/certificatekeypairs/' % domain, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        response = r.json()

        r = requests.get("https://sso.%s/%s" % (domain, response['results'][0]['certificate_download_url']), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        cert = r.text.replace('\r','').replace('\n','')
        Settings.create(plugin = self.module, key = 'default-cert', value=cert)

        return response['results'][0]['pk']

    def createProxyProvider(self, name, external_host):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        data = {
            'name': '%s Proxy Provider' % name,
            'authorization_flow': self.getDefaultFlowID(),
            'external_host': external_host,
            'basic_auth_enabled': True,
            'mode': 'forward_single',
            'token_validity': 'hours=1'
        }

        r = requests.post('https://sso.%s/api/v3/providers/proxy/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print(r.json())
            exit()
        else:
            provider_id = r.json()['pk']
            self.addProxyProviderToOutpost(provider_id)
            r = requests.get('https://sso.%s/api/v3/providers/proxy/%s' % (domain, provider_id), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            r = requests.put('https://sso.%s/api/v3/providers/proxy/%s' % (domain, provider_id), json=r.json(), headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
            return provider_id
    
    def addProxyProviderToOutpost(self, provider_id):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value

        outposts = requests.get('https://sso.%s/api/v3/outposts/instances/' % domain, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if outposts.status_code != 200:
            print("Unable To Get Proxy Outposts")
            exit()
        outpost = outposts.json()['results'][0];

        providers = [provider_id]
        if outpost['providers'] is not None:
            for p in outpost['providers']:
                providers.append(p)

        data = {
            'name': outpost['name'],
            'type': outpost['type'],
            'service_connection': outpost['service_connection'],
            'providers': providers,
            'config': outpost['config'],
            'managed': outpost['managed']
        }
        
        response = requests.put('https://sso.%s/api/v3/outposts/instances/%s/' % (domain, outpost['pk']), json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if response.status_code != 200:
            print("Unable To add Proxy to Outposts")
            print('https://sso.%s/api/v3/outposts/instances/%s/' % (domain, outpost['pk']))
            print(data)
            print(response.status_code)
            print(response.text)
            exit()

        pass
    def createOauthApplication(self, name, slug, launch_url, launch_description, client_id, client_secret, redirection_uri = None, launch_provider = None):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        data = {
            'name': name,
            'slug': slug,
            'provider': self.createOauthProvider(name, client_id, client_secret, redirection_uri),
            "meta_launch_url": launch_url,
            "meta_description": launch_description,
            "policy_engine_mode": "all"
        }
        if launch_provider is not None:
            data['launch_provider'] = launch_provider

        r = requests.post('https://sso.%s/api/v3/core/applications/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print()
            exit()
        
    def createSAMLApplication(self, name, slug, launch_url, launch_description, acs_url, audience, sp_binding='post', launch_provider = None):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        data = {
            'name': name,
            'slug': slug,
            'provider': self.createSAMLProvider(name, acs_url, audience, sp_binding),
            "meta_launch_url": launch_url,
            "meta_description": launch_description,
            "policy_engine_mode": "all"
        }
        if launch_provider is not None:
            data['launch_provider'] = launch_provider

        r = requests.post('https://sso.%s/api/v3/core/applications/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print()
            exit()

    def createProxyApplication(self, name, slug, launch_url, launch_description):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        data = {
            'name': name,
            'slug': slug,
            'provider': self.createProxyProvider(name, launch_url),
            "meta_launch_url": launch_url,
            "meta_description": launch_description,
            "policy_engine_mode": "all"
        }

        r = requests.post('https://sso.%s/api/v3/core/applications/' % domain, json=data, headers={'Authorization': "Bearer %s" % self.getSetting('admin_token')}, verify=False)
        if r.status_code != 201:
            print()
            exit()