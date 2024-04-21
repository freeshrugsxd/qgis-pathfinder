from html import escape
from pathlib import Path
from platform import system
from subprocess import run
from xml.etree import ElementTree

from qgis.core import QgsProviderRegistry
from qgis.PyQt.QtCore import QObject, QSettings
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface

from pathfinder.lib.i18n import tr
from pathfinder.lib.utils import PathfinderMaps

DEFAULTS = PathfinderMaps.DEFAULTS
COMMANDS = PathfinderMaps.COMMANDS


class Pathfinder(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
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

    def notify(self, message):
        """Show QGIS notification, if desired.

        Args:
            message (str): Message to be displayed in the notification.

        """
        if (settings := QSettings()).value('show_notification', type=bool):
            iface.messageBar().pushMessage(
                tr('Copied to clipboard'),
                escape(message),
                level=0,
                duration=settings.value('notify_duration', DEFAULTS['notify_duration'], int)
            )


    def open_in_explorer(self):
        """Open unique parent directories in a file explorer."""
        # TODO: select files in file explorer
        for p in self.unique_parent_dirs:
            run([self.command, str(p)])  # noqa: S603, PLW1510

    def parse_selected(self):
        """Parse selected layers and populate self.locs."""
        self.locs = [p for p in (self.parse(lyr) for lyr in self.selected_layers) if p is not None]

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
        if n > 1 and settings.value('paths_on_new_line', type=bool):
            s += '\n'

        qpr = QgsProviderRegistry.instance()
        out = s.join([f'{q}{qpr.encodeUri(d.pop("provider"), d)}{q}' for d in paths])
        return f'{pre}{out}{post}'

    @staticmethod
    def parse(layer, must_exist=True):
        """Parse data_source and return path and query elements.

        Args:
            layer (QgsMapLayer): Layer data source string
            must_exist (bool): Whether data_source must exist in the file system

        Returns:
            dict: dictionary containing the parts needed to reencode the uri

        """
        settings = QSettings()
        settings.beginGroup('pathfinder')
        pr_name = layer.dataProvider().name()
        parts = QgsProviderRegistry.instance().decodeUri(pr_name, layer.source())

        if 'path' not in parts or parts['path'] is None:
            return None

        out = {}
        path = Path(parts['path'])

        if must_exist and not path.exists():
            return None

        out['provider'] = pr_name

        if settings.value('incl_layer_name', type=bool):
            out['layerId'] = parts.pop('layerId', None)
            out['layerName'] = parts.pop('layerName', None)

        if settings.value('incl_subset_str', type=bool):
            out['subset'] = parts.pop('subset', None)

        if path.suffix == '.vrt' and settings.value('original_vrt_ds', type=bool):
            # return path to data source instead of virtual file
            ds = ElementTree.fromstring(path.read_text()).find('OGRVRTLayer').find('SrcDataSource')  # noqa: S314
            try:
                if ds.attrib['relativeToVRT'] == '1' and (path.parent / ds.text).is_file():
                    path = path.parent / ds.text
                elif ds.attrib['relativeToVRT'] == '0':
                    ds_path = Path(ds.text)
                    if ds_path.is_file():
                        path = ds_path

            except KeyError:
                ds_path = Path(ds.text)
                if ds_path.is_file():
                    path = ds_path

        out['path'] = str(path)
        return out


    @staticmethod
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
