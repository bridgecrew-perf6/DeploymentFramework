layout: page
title: "Deployment Framework"
permalink: /

# Deployment Framework

This project is an internally developed tool used to perform complex actions. It is licensed as such.

This framework's focus is being modular and event-driven, allowing anyone to jump in and develop CLI commands quickly.

# Creating a Plugin
To create a plugin, create a new directory with your plugin's name within the plugin folder. Then, within that new folder, create a new file titled `Plugin.py` using the following sample.

```python
# ./plugins/PLUGINNAME/Plugin.py
from core.BasePlugin import BasePlugin
from PyInquirer import prompt
import os

class Plugin(BasePlugin):

    priority = -100

    version = 1.0

    # Register functions to run when an Event is fired
    listenForEvents = {
        # Event to "catch" : Function to Run
        'default': 'defaultCommandFunction',
    }

    # Register Commands and Descriptions for the Help Menu
    # NOTE: The "command" is CASE SENSITIVE!
    availableCommands = {
        # Command : # Description
        'default': 'Runs a Sample Default Command',
    }

    pluginModels = []

    def help(self):
        print("Help Menu From [%s] Plugin" % self.getName())
        # Provides a print out of the `availableCommands`
        super().help()

     def defaultCommandFunction(self, arguments = []):
        print("Default command from [%s] Plugin provided %s arguments: %s" % 
            (self.getName(), len(arguments), arguments)
        )

        print("Dispatching the 'Help' event for the help menu to display")
        self.events.emit('help')

        print("Dispatching the event 'foo' with 3 function variables all 'bar'")
        self.events.emit('foo', 'bar', 'bar', 'bar')

        arguments.append('loop')
        print("The next line would run into a loop of doom....")
        # self.events.emit('default', arguments)

```

Finally, register it & enable it in the `plugins.yaml` file.

Additional values (settings) you provide will be set as the value for any settings in the database if they do not already exit upon being loaded.

```
RemoteOffice:
  enabled: true
  email: admin@localhost
```

# Additional Examples
While not all plugins we develop and used will be published here, you can see some more complex examples as this project develops.