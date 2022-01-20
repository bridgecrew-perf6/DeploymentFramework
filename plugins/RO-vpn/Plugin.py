from core.models.Module import Module
from plugins.RemoteOffice.Template import Template as BasePlugin
from core.models.Settings import Settings

from . import functions as ROVPNFunctions

class Plugin(BasePlugin):

    # listenForEvents = {
    #     'RO.mariadb.createDatabase': 'createDatabase',
    # }

    # availableCommands = {
    #     'RO.mariadb.createDatabase': 'Create a new Database'
    # }

    # The RO Base is 0; We need to be above that...
    priority = 40

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        pass

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        paths = [
            'storage/vpn/certs',
            'docker/vpn',
            'init/vpn'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):

        contents = ROVPNFunctions.dockerBuildFile()
        self.writeContentsToFile(contents, 'Dockerfile', "%s/docker/vpn" % install_dir)

        contents = ROVPNFunctions.startupFile()
        self.writeContentsToFile(contents, 'startup.sh', "%s/docker/vpn" % install_dir)

        contents = ROVPNFunctions.dockerFile()
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        ROldapModule = Module.select().where(Module.name == 'RO-ldap').get()
        base_dn = Settings.select().where(Settings.plugin == ROldapModule, Settings.key == 'base_dn').get().value

        contents = ROVPNFunctions.ldapFile(base_dn)
        self.writeContentsToFile(contents, 'ldap.conf', "%s/init/vpn" % install_dir)

        contents = ROVPNFunctions.serverFile()
        self.writeContentsToFile(contents, 'server.conf', "%s/init/vpn" % install_dir)

    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('pre-launch'):
            return
        Settings.create(plugin = self.module, key = 'pre-launch', value='True')

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        self.events.emit("RO.launch", "vpn")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        if not self.promptRequired('post-launch'):
            return
        Settings.create(plugin = self.module, key = 'post-launch', value='True')