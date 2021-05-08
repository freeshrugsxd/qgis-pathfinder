from pathlib import Path

from PyQt5.QtCore import QSettings

DEFAULTS = {
    'quote_char': '"',
    'separ_char': 'Space',
    'quote_char_custom': '',
    'separ_char_custom': '',
    'prefix': '',
    'postfix': '',
    'single_path_quote': 0,
    'single_path_affix': 0,
    'incl_file_name': 2,
    'incl_layer_name': 0,
    'incl_subset_str': 0,
    'show_notification': 0,
    'paths_on_new_line': 0
}

MAPPINGS = {
    'quote_char': {
        '\"': '\"',
        '\'': '\'',
        '´': '´',
        '`': '`',
        'Space': ' ',
        'None': '',

    },
    'separ_char': {
        'Space': ' ',
        'Tab': '\t',
        'New Line': '\n',
        ',': ',',
        ';': ';',
    },
}


def is_file(loc: Path) -> bool:
    """Return ``Path.is_file()`` but do not raise OSError if loc is not a
    valid OS path (e.g. starting with 'https:///').

    :param loc: A pathlib.Path object.
    :return: Whether loc is a file.

    Note
    ----
    This is pathlibs default behaviour from Python 3.8 and onwards.
    So this helper will probably be deprecated once QGIS LTR on Windows ships with Python>=3.8.
    """
    try:
        return loc.is_file()
    except OSError:
        return False


def get_char(s: str) -> str:
    """Return the character equivalent to ``s`` or its respective custom character.

    :param s: either 'quote_char' or 'separ_char'
    :return: representation of s or its respective custom character
    """
    settings = QSettings()
    settings.beginGroup('pathfinder')
    if settings.value(s) == 'Other':
        return settings.value(f'{s}_custom', DEFAULTS[f'{s}_custom'])
    else:
        return MAPPINGS[s][settings.value(s, DEFAULTS[s])]


def escape_string(s):
    """Return a unicode escaped copy of ``s``.

    :param s:
    :return:
    """
    return bytes(s, 'utf-8').decode('unicode_escape')
