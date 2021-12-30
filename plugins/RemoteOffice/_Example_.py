from plugins.RemoteOffice.Template import Template as BasePlugin

class Plugin(BasePlugin):
    # The RO Base is 0; We need to be above that...
    priority = 10

    # Prompts User for Configuration Options
    def preformOfficePrompts(self):
        questions = [
            # REF: https://github.com/CITGuru/PyInquirer/
            {
                'type': 'password',
                'name': 'plugin_setting',
                'message': '[%s] Message Prompt:' % str.upper(self.getName()),
            }
        ]
        
        questionsToAsk = []
        for question in questions:
            if self.promptRequired(question.name):
                questionsToAsk.append(question)

        self.preformPrompts(questionsToAsk)

    # Used to create any storage and initizalation directories needed
    def createFolderStructure(self, install_dir = './office'):
        # The paths the plugin needs to ensure exist
        paths = [
            'storage/plugin/certs',
            'init/plugin/startup'
        ]
        self.createFolders(paths, install_dir)

    # Used to append the plugin's docker service if it exists.
    def appendDockerService(self, docker_compose_file = 'docker-compose.yml', install_dir = './office'):
        contents = "TODO.... %s in w/ your %s container settings. Ensure Proper Spacing...."  % ("Fill", "docker-compose plugin")
        self.appendContentsToFile(contents, docker_compose_file, install_dir)


    # Used to initialize any any configuration settings that need to be deployed
    def createInitialConfig(self, install_dir = './office'):
        # File 1
        contents = "setting_name = %s" % self.getSetting('setting_name')
        self.writeContentsToFile(contents, 'init/plugins/startup/startup.ini', install_dir)
        # Copy/Paste Repeat...

    
    # Preform any additional config before the container is launched.
    # This is useful if you need to preform API calls to finalize the config
    #   for this plugin; but need to wait for another plugin to launch first
    def preLaunchConfig(self, install_dir = './office'):
        # Example Emitting to another Plugin to have it do work....
        # self.events.emit(
        #     "RO.plugin.Event-Name", 
        #     "Function_Var_1",
        #     "Function_Var_2",
        #     # ...
        # )
        pass

    # Preform the actual launching of docker container for this plugin
    def launchDockerService(self):
        # Use the Docker Plugin to Launch a specific Container
        self.events.emit("docker.launch", "plugin-Container-Name")
        pass

    # Preform any post launch for this container.
    # Ensure API's are up
    # Change default passwords, Etc...
    def postLaunchConfig(self, install_dir = './office'):
        # See preLaunchConfig

        # Use the Docker Plugin to Launch a specific Container
        self.events.emit("docker.command", "plugin-Container-Name", "command to run on the container")
        pass

    # Functions Provided by Parent...

    # Check if the prompt is needed for the provided key
    # Or if we already have a saved value.
    #def promptRequired(self, setting_key, module = None):

    # Preform the Prompts; and Update the settings
    #def preformPrompts(self, questions = []):

    # Get a specific setting
    #def getSetting(self, setting_key, module = None):
    # Ensures the paths provided exist as folders
    #def createFolders(self, paths = [], install_dir = './office'):

    # Writes contents to file
    #def writeContentsToFile(self, contents, file_name, install_dir = './office'):

    # Appends content to file
    #def appendContentsToFile(self, contents, file_name, install_dir = './office'):