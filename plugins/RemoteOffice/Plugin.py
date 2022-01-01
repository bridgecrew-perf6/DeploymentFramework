from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os
from core.models.Settings import Settings

class Plugin(BasePlugin):
    priority = 0

    version = 1.0

    listenForEvents = {
        'RO.settings': 'preformPrompts',
        'RO.install': 'preformInstall',
        'RO.launch': 'launchContainer',
        'RO.command': 'runCommand',
        'RO.CLEAN': 'resetOffice'
    }

    availableCommands = {
        'RO.settings': 'Prompt the User for Configuration Settings',
        'RO.install': 'After gathering required setting; preform the install',
        'RO.launch': 'Launch a specific container',
        'RO.command': 'Run a command on a specific container',
        'RO.CLEAN': 'Removes all directories and config files for the remote office'
    }

    pluginModels = []

    def help(self):
        print("-" * 50)
        print("Remote Office Install Plugin")
        super().help()
        print("-" * 50)

    def preformPrompts(self, args=[]):
        questions = []

        # Installation Directory
        if Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').count() == 0 or len(args) > 0:
            questions.append({
                'type': 'input',
                'name': 'install_dir',
                'message': 'Where should we install the office?',
                'default': './office'
            })

        if Settings.select().where(Settings.plugin == self.module, Settings.key == 'domain_name').count() == 0 or len(args) > 0:
            questions.append({
                'type': 'input',
                'name': 'domain_name',
                'message': 'What is the Domain Name the Virtual Office will be using?',
                'default': 'sniper7kills.com'
            })
        
        # If we had to prompt for any questions; save them into the config
        if len(questions) > 0:
            answers = prompt(questions)
            for answer in answers:
                Settings.create(plugin = self.module, key = answer, value=answers[answer])

        self.events.emit("RO.prompts")


    def preformInstall(self, args=[]):

        self.preformPrompts()

        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value

        if not os.path.exists("%s/storage/" % install_dir):
            os.makedirs("%s/storage/" % install_dir)

        if not os.path.exists("%s/init/" % install_dir):
            os.makedirs("%s/init/" % install_dir)

        if not os.path.exists("%s/envs/" % install_dir):
            os.makedirs("%s/envs/" % install_dir)

        self.events.emit("RO.folders", install_dir)
        self.cleanDockerCompose(install_dir, 'docker-compose.yml')
        self.events.emit("RO.docker", 'docker-compose.yml', install_dir)
        self.events.emit("RO.config", install_dir)

        for plugin in self.loadedPlugins:
            if plugin.getName().startswith("RO-"):
                plugin.preLaunchConfig(install_dir)
                plugin.launchDockerService()
                plugin.postLaunchConfig(install_dir)

    def cleanDockerCompose(self, install_dir, docker_file = 'docker-compose.yml'):
        contents = "version: '3.5'\nservices:\n"
        f = open(install_dir + '/' + docker_file, "w")
        f.write(contents)
        f.close()

    def launchContainer(self, container_name):
        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value
        self.events.emit("docker.start", install_dir, container_name)

    def runCommand(self, container_name, command):
        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value
        self.events.emit("docker.exec", install_dir, container_name, command)

    def resetOffice(self):
        import shutil
        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value
        self.events.emit("docker.down", install_dir)
        shutil.rmtree(install_dir)
        os.remove('config.db')