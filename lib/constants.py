from pathlib import Path
from platform import system

from pathfinder.lib.i18n import tr

class Constants:
    def __init__(self):
        # platform specific commands to open file explorer
        self.commands = {
            'Windows': 'explorer',
            'Linux': 'xdg-open',
            'Darwin': 'open'
        }

        # map combobox label to actual character
        self.mappings = {
            'quote_char': {
                '"': '"',
                "'": "'",
                '´': '´',
                '`': '`',
                tr('Space'): ' ',
                tr('None'): '',
            },
            'separ_char': {
                tr('Space'): ' ',
                tr('Tab'): '\t',
                tr('New Line'): '\n',
                ',': ',',
                ';': ';',
            }
        }

        self.system = system()
        self.system_is_windows = self.system == 'Windows'
        self.command = self.commands[self.system]
        self.plugin_dir = Path(__file__).parent.parent


constants = Constants()
COMMAND = constants.command
MAPPINGS = constants.mappings
PLUGIN_DIR = constants.plugin_dir
SYSTEM_IS_WINDOWS = constants.system_is_windows
