from html import escape
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree as ET

from qgis.core import QgsProviderRegistry
from qgis.PyQt.QtCore import QProcess
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface

from pathfinder.lib.i18n import tr
from pathfinder.lib.settings import Settings
from pathfinder.lib.utils import COMMAND, MAPPINGS, SYSTEM_IS_WINDOWS


class Pathfinder:
    def __init__(self):
        self.locs = []
        self.settings = Settings()

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
        for p in self.unique_file_paths:
            QProcess.startDetached(COMMAND, ['/select,', str(p)] if SYSTEM_IS_WINDOWS else [str(p)])

    def build_string(self, paths):
        """Construct a string using pathfinders current settings.

        Args:
            paths (list[dict]): A list of dicts with at least a 'path'
            and 'provider' key.

        Returns:
           str: Formatted string representing one or more file uris.

        """
        settings = Settings()
        qpr = QgsProviderRegistry.instance()
        n = len(paths)

        q, s = self.get_chars(quote='quote_char', sep='separ_char')

        pre = settings.prefix.value()
        post = settings.postfix.value()

        # should file name be included?
        if not settings.incl_file_name.value('incl_file_name'):
            for d in paths:
                d['path'] = str(Path(d['path']).parent)

        if n == 1:
            # should a single path be quoted?
            if not settings.single_path_quote.value():
                q = ''
            # should pre- and postfix be applied to single path?
            if not settings.single_path_affix.value():
                pre = ''
                post = ''

        # should paths go onto separate lines?
        elif n > 1 and settings.paths_on_new_line.value():
            s += '\n'

        enc = []
        for parts in paths:
            provider = parts.pop('provider')
            encoded = qpr.encodeUri(provider, parts)

            if 'file:///' in encoded:
                encoded = urlparse(encoded).path

                if SYSTEM_IS_WINDOWS:
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
        if self.settings.show_notification.value():
            iface.messageBar().pushMessage(
                tr('Copied to clipboard'),
                escape(message),
                level=0,
                duration=self.settings.notify_duration.value()
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
        settings = Settings()

        for s in (quote, sep):
            if getattr(settings, s).value() == tr('Other'):
                yield getattr(settings, f'{s}_custom').value()
            else:
                yield MAPPINGS[s][getattr(settings, s).value()]

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

        if must_exist and not path.exists():
            return None

        settings = Settings()
        out = {'provider': pr_name}

        if settings.incl_layer_name.value():
            out['layerId'] = parts.pop('layerId', None)
            out['layerName'] = parts.pop('layerName', None)

        if settings.incl_subset_str.value():
            out['subset'] = parts.pop('subset', None)

        if path.suffix == '.vrt' and settings.original_vrt_ds.value():
            # return path to data source instead of virtual file
            ds = ET.fromstring(path.read_text()).find('OGRVRTLayer').find('SrcDataSource')  # noqa: S314
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

        Returns:
            set[Path]: Set of unique parent directories from list of paths

        """
        return {Path(d['path']).parent for d in self.locs}

    @property
    def layers_selected(self):
        """Return whether there are any layers selected.

        Returns:
            bool: Whether there are any layers selected.

        """
        return len(self.selected_layers) > 0

    @property
    def selected_layers(self):
        """Return list of selected layers.

        Returns:
            list[QgsMapLayer]: List of selected layers.

        """
        return iface.layerTreeView().selectedLayers()
