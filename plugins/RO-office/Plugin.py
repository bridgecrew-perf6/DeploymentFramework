from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings
import requests, time

from . import functions as ROOfficeFunctions

class Plugin(BasePlugin):

    # could be 30; but 40
    priority = 40

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        pass

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        paths = [
            'storage/office/data',
            'storage/office/logs'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = ROOfficeFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        pass

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return

        self.events.emit('RO.proxy.createHost', 'office', 'office', '80', 'http')
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "office")

        self.waitForReady()

    def waitForReady(self):
        RemoteOfficeModule = Module.select().where(Module.name == 'RemoteOffice').get()
        domain = Settings.select().where(Settings.plugin == RemoteOfficeModule, Settings.key == 'domain_name').get().value
        status = 0
        #Wait For Ready
        while status != 200:
            r = requests.get('https://office.%s' % domain, verify=False)
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

        self.events.emit("RO.command.user", "cloud", "www-data", "php occ config:system:set allow_local_remote_servers --value true --type bool")

        self.events.emit("RO.cloud.enableApp", "onlyoffice")

        settings = {
            "enabled": "yes",  
            "DocumentServerUrl": "https://office.%s/" % domain,
            "verify_peer_off": "true",
            "DocumentServerInternalUrl": "http://office/",
            "StorageUrl": "http://cloud/",
            "settings_error": "",
            "defFormats": "{\"csv\":\"true\",\"doc\":\"true\",\"docm\":\"true\",\"docx\":\"true\",\"dotx\":\"true\",\"epub\":\"true\",\"html\":\"true\",\"odp\":\"true\",\"ods\":\"true\",\"odt\":\"true\",\"otp\":\"true\",\"ots\":\"true\",\"ott\":\"true\",\"pdf\":\"true\",\"potm\":\"true\",\"potx\":\"true\",\"ppsm\":\"true\",\"ppsx\":\"true\",\"ppt\":\"true\",\"pptm\":\"true\",\"pptx\":\"true\",\"rtf\":\"true\",\"txt\":\"true\",\"xls\":\"true\",\"xlsm\":\"true\",\"xlsx\":\"true\",\"xltm\":\"true\",\"xltx\":\"true\"}",
            "editFormats": "{\"csv\":\"true\",\"odp\":\"true\",\"ods\":\"true\",\"odt\":\"true\",\"rtf\":\"true\",\"txt\":\"true\"}",
            "sameTab": "true",
            "preview": "true",
            "versionHistory": "true",
            "groups": "[]",
            "customizationChat": "true",
            "customizationCompactHeader": "true",
            "customizationFeedback": "true",
            "customizationForcesave": "false",
            "customizationHelp": "true",
            "customizationToolbarNoTabs": "true",
            "customizationReviewDisplay": "original"
        }
        for setting in settings:
            self.events.emit("RO.cloud.setAppSetting", "onlyoffice", setting, settings[setting])

        Settings.create(plugin = self.module, key = 'post-launch', value='True')