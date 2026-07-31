from pathlib import Path
from platform import system

system = system()

COMMAND = {
    'Windows': 'explorer',
    'Linux': 'xdg-open',
    'Darwin': 'open',
}[system]

MAPPINGS = {
    'quote_char': {
        'double_quote': '"',
        'single_quote': "'",
        'acute_accent': '´',
        'backtick': '`',
        'space': ' ',
        'none': '',
    },
    'separ_char': {
        'space': ' ',
        'tab': '\t',
        'comma': ',',
        'semicolon': ';',
    }
}

PLUGIN_DIR = Path(__file__).parent.parent
SYSTEM_IS_WINDOWS = system == 'Windows'
