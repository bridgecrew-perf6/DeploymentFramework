from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os
from core.models.Settings import Settings

class Plugin(BasePlugin):
    priority = 0

    version = 1.0

    listenForEvents = {
        'RO.settings': 'preformPrompts',
        'RO.install': 'preformInstall'
    }

    availableCommands = {
        'RO.settings': 'Prompt the User for Configuration Settings',
        'RO.install': 'After gathering required setting; preform the install'
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


        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value
        self.events.emit("RO.prompts")


    def preformInstall(self, args=[]):

        install_dir = Settings.select().where(Settings.plugin == self.module, Settings.key == 'install_dir').get().value

        if not os.path.exists("%s/storage/" % install_dir):
            os.makedirs("%s/storage/" % install_dir)

        if not os.path.exists("%s/init/" % install_dir):
            os.makedirs("%s/init/" % install_dir)

        self.events.emit("RO.folders", install_dir)
        self.events.emit("RO.docker", 'docker-compose.yml', install_dir)
        self.events.emit("RO.config", install_dir)
        pass