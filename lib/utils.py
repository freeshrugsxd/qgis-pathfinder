from pathlib import Path

from qgis.PyQt.QtCore import QSettings

from pathfinder.lib.i18n import tr


class PathfinderMaps:
    def __init__(self):
        # platform specific commands to open the system's *most likely* file explorer
        self.COMMANDS = {
            'Windows': 'explorer',
            'Linux': 'xdg-open',
            'Darwin': 'open'
        }

        # map combobox label to actual character
        self.MAPPINGS = {
            'quote_char': {
                '\"': '\"',
                '\'': '\'',
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
        self.DEFAULTS = {
            'quote_char': '"',
            'separ_char': tr('Space'),
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


def exists(loc: Path) -> bool:
    """Return ``Path.exists()`` but do not raise OSError if loc is not a
    valid OS path (e.g. starting with 'https:///').

    :param loc: A pathlib.Path object.
    :return: Whether loc is a file or folder.

    Note
    ----
    This is pathlibs default behaviour from Python 3.8 and onwards.
    So this helper will probably be deprecated once QGIS LTR on Windows ships with Python>=3.8.
    """
    try:
        return loc.exists()
    except OSError:
        return False


def get_char(s: str) -> str:
    """Return the character equivalent to ``s`` or its respective custom character.

    :param s: either 'quote_char' or 'separ_char'
    :return: representation of s or its respective custom character
    """

    settings = QSettings()
    settings.beginGroup('pathfinder')

    defs = PathfinderMaps().DEFAULTS
    maps = PathfinderMaps().MAPPINGS

    if settings.value(s) == tr('Other'):
        return settings.value(f'{s}_custom', defs[f'{s}_custom'])
    else:
        try:
            return maps[s][settings.value(s, defs[s])]
        except KeyError:
            # after switching languages, the values of some named characters can't be retrieved.
            # For now, we will reset these values to their default.
            # TODO: find way to make these settings persistent across languages
            settings.setValue(s, defs[s])
            return maps[s][settings.value(s)]


def escape_string(s):
    """Return a unicode escaped copy of ``s``.

    :param s:
    :return:
    """
    return bytes(s, 'utf-8').decode('unicode_escape')
