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

# reasonable defaults for pathfinder settings
DEFAULTS = {
    'quote_char': '"',
    'separ_char': tr('Space'),
    'quote_char_custom': '',
    'separ_char_custom': '',
    'prefix': '',
    'postfix': '',
    'single_path_quote': False,
    'single_path_affix': False,
    'incl_file_name': True,
    'incl_layer_name': False,
    'incl_subset_str': False,
    'show_notification': False,
    'paths_on_new_line': False,
    'original_vrt_ds': False,
    'notify_duration': 5
}

SYSTEM = system()
SYSTEM_IS_WINDOWS = SYSTEM == 'Windows'
COMMAND = COMMANDS[SYSTEM]
PLUGIN_DIR = Path(__file__).parent.parent
