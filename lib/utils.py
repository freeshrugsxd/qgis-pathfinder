from qgis.PyQt.QtCore import QSettings

from pathfinder.lib.i18n import tr


class PathfinderMaps:
    # platform specific commands to open the system's *most likely* file explorer
    COMMANDS = {
        'Windows': 'explorer',
        'Linux': 'xdg-open',
        'Darwin': 'open'
    }

    # map combobox label to actual character
    MAPPINGS = {
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
    DEFAULTS = {
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
        'paths_on_new_line': 0,
        'original_vrt_ds': 0,
        'notify_duration': 5
    }


def get_chars(quote='quote_char', sep='separ_char') -> str:
    """Return the character equivalent to s or its respective custom character.

    Args:
        quote: Quotation character
        sep: Separation character

    Yields:
        Generator[str, None, None]: generator containing representation of quote and sep
            or their respective custom characters.
    """
    settings = QSettings()
    settings.beginGroup('pathfinder')

    defs = PathfinderMaps.DEFAULTS
    maps = PathfinderMaps.MAPPINGS

    for s in (quote, sep):
        if settings.value(s) == tr('Other'):
            yield settings.value(f'{s}_custom', defs[f'{s}_custom'])
        else:
            try:
                yield maps[s][settings.value(s, defs[s])]
            except KeyError:
                # after switching languages, the values of some named characters can't be retrieved.
                # For now, we will reset these values to their default.
                # TODO: find way to make these settings persistent across languages
                settings.setValue(s, defs[s])
                yield maps[s][settings.value(s)]
