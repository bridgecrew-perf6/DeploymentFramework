#!/usr/bin/env python3
from core.app import Application
import yaml
import sys

if __name__ == "__main__":
    plugins = []
    with open('./plugins.yaml') as file:
        # The FullLoader parameter handles the conversion from YAML
        # scalar values to Python the dictionary format
        pluginConfig = yaml.load(file, Loader=yaml.FullLoader)

    for plugin in pluginConfig:
        if pluginConfig[plugin]['enabled']:
            plugins.append(plugin)

    # Initialising our application
    app = Application(plugins, pluginConfig)

    # Running our application
    app.run(sys.argv[1:])  