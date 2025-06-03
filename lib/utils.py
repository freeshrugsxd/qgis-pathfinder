from pathlib import Path
from platform import system

from pathfinder.lib.i18n import tr

# platform specific commands to open file explorer
COMMANDS = {
    'Windows': 'explorer',
    'Linux': 'xdg-open',
    'Darwin': 'open'
}

# map combobox label to actual character
MAPPINGS = {
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

SYSTEM = system()
SYSTEM_IS_WINDOWS = SYSTEM == 'Windows'
COMMAND = COMMANDS[SYSTEM]
PLUGIN_DIR = Path(__file__).parent.parent
