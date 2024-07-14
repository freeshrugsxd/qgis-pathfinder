from html import escape
from pathlib import Path
from platform import system
from subprocess import run
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

from qgis.core import QgsProviderRegistry
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface

from pathfinder.lib.i18n import tr
from pathfinder.lib.utils import PathfinderMaps

DEFAULTS = PathfinderMaps.DEFAULTS
COMMANDS = PathfinderMaps.COMMANDS


class Pathfinder:
    def __init__(self):
        self.command = COMMANDS[system()]
        self.locs = []
        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

    def copy(self):
        """Copy paths to clipboard."""
        text = self.build_string(self.locs)
        QApplication.clipboard().setText(text)
        self.notify(message=text)

    def copy_double_backslash(self):
        """Copy paths to clipboard with double backslashes."""
        text = self.build_string(self.locs).replace('\\', '\\\\')
        QApplication.clipboard().setText(text)
        self.notify(message=text)

    def open_in_explorer(self):
        """Open unique parent directories in a file explorer."""
        if system() == 'Windows':
            for p in self.unique_file_paths:
                run([self.command, '/select,', p])  # noqa: S603, PLW1510
        else:
            for p in self.unique_parent_dirs:
                run([self.command, p])  # noqa: S603, PLW1510

    def build_string(self, paths):
        """Construct a string using pathfinders current settings.

        Args:
            paths (list[dict]): A list of dicts with at least a 'path'
            and 'provider' key.

        Returns:
           str: Formatted string representing one or more file uris.

        """
        settings = QSettings()
        settings.beginGroup('pathfinder')
        qpr = QgsProviderRegistry.instance()
        n = len(paths)

        q, s = self.get_chars(quote='quote_char', sep='separ_char')

        pre = settings.value('prefix', DEFAULTS['prefix'])
        post = settings.value('postfix', DEFAULTS['postfix'])

        # should file name be included?
        if not settings.value('incl_file_name', type=bool):
            for d in paths:
                d['path'] = str(Path(d['path']).parent)

        if n == 1:
            # should a single path be quoted?
            if not settings.value('single_path_quote', type=bool):
                q = ''
            # should pre- and postfix be applied to single path?
            if not settings.value('single_path_affix', type=bool):
                pre = ''
                post = ''

        # should paths go onto separate lines?
        elif n > 1 and settings.value('paths_on_new_line', type=bool):
            s += '\n'

        enc = []
        for parts in paths:
            provider = parts.pop('provider')
            encoded = qpr.encodeUri(provider, parts)

            if 'file:///' in encoded:
                encoded = urlparse(encoded).path

                if system() == 'Windows':
                    encoded = encoded.strip('/')

            if provider == 'delimitedtext' and '%' in encoded:
                encoded = unquote(encoded)

            enc.append(encoded)

        inner = s.join(f'{q}{path}{q}' for path in enc)
        return f'{pre}{inner}{post}'

    def notify(self, message):
        """Show QGIS notification, if setting is enabled.

        Args:
            message (str): Message to be displayed in the notification.

        """
        if self.settings.value('show_notification', type=bool):
            iface.messageBar().pushMessage(
                tr('Copied to clipboard'),
                escape(message),
                level=0,
                duration=self.settings.value('notify_duration', DEFAULTS['notify_duration'], int)
            )

    def parse_selected(self):
        """Parse selected layers and populate self.locs."""
        self.locs = [p for p in (self.parse(lyr) for lyr in self.selected_layers) if p is not None]


    @staticmethod
    def get_chars(quote='quote_char', sep='separ_char'):
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


    @staticmethod
    def parse(layer, must_exist=True):
        """Parse layer and return dictionary from which to encode an uri again.

        Args:
            layer (QgsMapLayer): A QGIS layer.
            must_exist (bool): Whether layer's data source must exist in the file system

        Returns:
            dict: dictionary containing the parts needed to reencode the uri

        """
        pr_name = layer.dataProvider().name()
        parts = QgsProviderRegistry.instance().decodeUri(pr_name, layer.source())

        if (path_str := parts.pop('path', None)) is None:
            return None

        path = Path(path_str)

        if not path.exists() and must_exist:
            return None

        settings = QSettings()
        settings.beginGroup('pathfinder')
        out = {'provider': pr_name}

        if settings.value('incl_layer_name', type=bool):
            out['layerId'] = parts.pop('layerId', None)
            out['layerName'] = parts.pop('layerName', None)

        if settings.value('incl_subset_str', type=bool):
            out['subset'] = parts.pop('subset', None)

        if path.suffix == '.vrt' and settings.value('original_vrt_ds', type=bool):
            # return path to data source instead of virtual file
            ds = ElementTree.fromstring(path.read_text()).find('OGRVRTLayer').find('SrcDataSource')  # noqa: S314
            if 'relativeToVRT' in ds.attrib:
                path = path.parent / ds.text if ds.attrib['relativeToVRT'] == '1' else Path(ds.text)

        # in case a shapefile was loaded from a directory
        elif path.is_dir() and 'layerName' in parts and (shp := (path / parts['layerName']).with_suffix('.shp')).is_file():
            path = shp

        out['path'] = str(path)

        return {k: v for k, v in out.items() if v is not None}

    @property
    def unique_file_paths(self):
        """Return set of unique file paths.

        Returns:
            set[Path]: Set of unique file paths
        """
        return {Path(d['path']) for d in self.locs}

    @property
    def unique_parent_dirs(self):
        """Return set of unique parent directories from list of paths.

        Returns
            set[Path]: Set of unique parent directories from list of paths

        """
        return {Path(d['path']).parent for d in self.locs}

    @property
    def layers_selected(self):
        """Return whether there are any layers selected.

        Returns
            bool: Whether there are any layers selected.

        """
        return len(self.selected_layers) > 0

    @property
    def selected_layers(self):
        """Return list of selected layers.

        Returns
            list[QgsMapLayer]: List of selected layers.

        """
        return iface.layerTreeView().selectedLayers()
