from pathlib import Path
from typing import List

from PyQt5.QtCore import QSettings


class PathfinderSettings:
    def __init__(self):
        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

    @property
    def defaults(self):
        # int values 0 and 2 correspond to Qts CheckStatus enum
        # https://doc.qt.io/qtforpython-5/PySide2/QtCore/Qt.html#PySide2.QtCore.PySide2.QtCore.Qt.CheckState
        # 0 = Qt.Unchecked, 2 = Qt.Checked
        return {
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
        }

    @property
    def mappings(self):
        return {
            'quote_char': {
                '\"': '\"',
                '\'': '\'',
                '´': '´',
                '`': '`',
                'Space': ' ',
                'None': '',
                'Other': self.settings.value('quote_char_custom', self.defaults['quote_char_custom'])
            },
            'separ_char': {
                'Space': ' ',
                'Tab': '    ',
                'New Line': '\n',
                ',': ',',
                ';': ';',
                'Other': self.settings.value('separ_char_custom', self.defaults['separ_char_custom'])
            },
        }


def build_string(paths: List[tuple]) -> str:
    """Construct a string using pathfinders current settings.

    :param paths: A list of tuples (path, info) where paths[0] contains the valid file path
    and paths[1] contains data provider information such as the layer name and
    subset string.
    :return: Formatted string representing one or more file paths.
    """
    settings = QSettings()
    settings.beginGroup('pathfinder')
    mappings = PathfinderSettings().mappings
    defaults = PathfinderSettings().defaults

    q = mappings['quote_char'][settings.value('quote_char', defaults['quote_char'])]
    s = mappings['separ_char'][settings.value('separ_char', defaults['separ_char'])]
    pre = settings.value('prefix', defaults['prefix'])
    post = settings.value('postfix', defaults['postfix'])

    # should file name be included?
    fn = settings.value('incl_file_name', type=bool)

    # should a single path be quoted?
    if len(paths) == 1 and settings.value('single_path_quote', type=bool):
        q = ''

    # should pre- and postfix be applied to single path?
    if len(paths) == 1 and settings.value('single_path_affix', type=bool):
        pre = ''
        post = ''

    out = s.join([f'{q}{p if fn else p.parent}{i}{q}' for p, i in paths])
    return f'{pre}{out}{post}'


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


def parse_path(path: str, must_be_file: bool = True) -> [tuple, None]:  # noqa
    """Strip common appendices from path string according to pathfinder settings.

    :param path: String that could be a file path.
    :return: Tuple containing a valid file path and the desired data provider information.
    """
    # TODO:
    #  - allow for non file layer to successfully pass through here
    #  - come up with a more clear return than a tuple
    settings = QSettings()
    settings.beginGroup('pathfinder')
    parts = path.replace('file:', '').split('?')[0].split('|')

    fp = Path(parts[0])
    # return tuple of Nones if s
    if must_be_file and not is_file(fp) :
        return None, None

    n = len(parts)
    has_layer_name = n > 1
    is_subset = n > 2

    info = ''

    if has_layer_name and settings.value('incl_layer_name', type=bool):
        info += f'|{parts[1]}'

    if is_subset and settings.value('incl_subset_str', type=bool):
        info += f'|{parts[2]}'

    return fp, info


def escape_string(s):
    """Return a unicode escaped copy of ``s``.

    :param s:
    :return:
    """
    return bytes(s, 'utf-8').decode('unicode_escape')
