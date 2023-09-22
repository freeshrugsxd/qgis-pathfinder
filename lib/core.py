import xml.etree.ElementTree as ET
from html import escape as escape_html
from pathlib import Path
from platform import system as pf_system
from subprocess import run as run_subprocess
from urllib.parse import urlparse
from urllib.request import url2pathname

from qgis.PyQt.QtCore import QObject, QSettings
from qgis.PyQt.QtWidgets import QApplication
from qgis.utils import iface

from pathfinder.lib.i18n import tr
from pathfinder.lib.utils import PathfinderMaps, get_chars

DEFAULTS = PathfinderMaps.DEFAULTS
COMMANDS = PathfinderMaps.COMMANDS


class Pathfinder(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.command = COMMANDS[pf_system()]
        self.locs = []
        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

    def copy(self):
        """Copy paths to clipboard."""
        text = self.build_string(self.locs)
        QApplication.clipboard().setText(text)
        self.notify(text)

    def copy_double_backslash(self):
        """Copy paths to clipboard with double backslashes."""
        text = self.build_string(self.locs).replace('\\', '\\\\')
        QApplication.clipboard().setText(text)
        self.notify(msg=text)

    def notify(self, msg):
        """Show QGIS notification.

        Args:
            msg (str): Message to be displayed in QGIS notification.
        """
        if self.settings.value('show_notification', type=bool):
            iface.messageBar().pushMessage(
                tr('Copied to clipboard'),
                escape_html(msg),
                level=0,
                duration=self.settings.value('notify_duration', DEFAULTS['notify_duration'], int)
            )

    def open_in_explorer(self):
        """Open unique parent directories in a file explorer."""
        # TODO: select files in file explorer
        for p in self.unique_parent_dirs:
            run_subprocess([self.command, str(p)])  # noqa: S603, PLW1510

    def parse_selected(self):
        """Parse selected layers. Populate self.locs."""
        for lyr in self.selected_layers:
            path, query = self.parse_path(lyr.source())
            if path is not None:
                self.locs.append((path, query))

    @property
    def unique_parent_dirs(self):
        """Return set of unique parent directories from list of paths.

        Returns:
            set[Path]: Set of unique parent directories from list of paths
        """
        return {path.parent for path, query in self.locs}

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

    @staticmethod
    def build_string(paths):
        """Construct a string using pathfinders current settings.

        Args:
            paths (list[tuple]): A list of tuples (path, query) where the first item contains
                the valid file path and the second contains data provider information such
                as the layer name and subset string.

        Returns:
           str: Formatted string representing one or more file paths.
        """
        settings = QSettings()
        settings.beginGroup('pathfinder')
        n = len(paths)

        q, s = get_chars(q='quote_char', s='separ_char')

        pre = settings.value('prefix', DEFAULTS['prefix'])
        post = settings.value('postfix', DEFAULTS['postfix'])

        # should file name be included?
        fn = settings.value('incl_file_name', type=bool)

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

        out = s.join([f'{q}{p if fn else p.parent}{i}{q}' for p, i in paths])
        return f'{pre}{out}{post}'

    @staticmethod
    def parse_path(data_source, must_exist=True):
        """Parse data_source and return path and query elements.

        Args:
            data_source (str): Layer data source string
            must_exist (bool): Whether data_source must exist in the file system

        Returns:
            tuple: Tuple containing the path and query parts of the source
        """
        # TODO:
        #  - come up with a more clear return than a tuple
        settings = QSettings()
        settings.beginGroup('pathfinder')
        parts = data_source.split('?')[0].split('|')

        if not parts[0]:
            return None, None

        try:
            path = Path(url2pathname(urlparse(parts[0]).path) if parts[0].startswith('file:') else parts[0])

        except OSError:
            # return None for now
            return None, None

        if must_exist and not path.exists():
            return None, None

        has_layer_name_or_id = False
        layer_name_or_id = ''
        is_subset = False
        subset_string = ''

        if len(parts) > 1:
            for part in parts[1:]:
                if has_layer_name_or_id := 'layername=' in part or 'layerid=' in part:
                    layer_name_or_id = part

                elif is_subset := 'subset=' in part:
                    subset_string = part

        query = ''

        if has_layer_name_or_id and settings.value('incl_layer_name', type=bool):
            query += f'|{layer_name_or_id}'

        if is_subset and settings.value('incl_subset_str', type=bool):
            query += f'|{subset_string}'

        if path.suffix == '.vrt' and settings.value('original_vrt_ds', type=bool):
            # return path to data source instead of virtual file
            ds = ET.fromstring(path.read_text()).find('OGRVRTLayer').find('SrcDataSource')  # noqa: S314
            try:
                if ds.attrib['relativeToVRT'] == '1' and path.parent.joinpath(ds.text).is_file():
                    path = path.parent / ds.text
                elif ds.attrib['relativeToVRT'] == '0':
                    ds_path = Path(ds.text)
                    if ds_path.is_file():
                        path = ds_path

            except KeyError:
                ds_path = Path(ds.text)
                if ds_path.is_file():
                    path = ds_path

        # in case a shapefile was loaded from a directory
        elif path.is_dir():
            # we slice the layername instead of splitting to account for the
            # unlikely case that the shapefile name contains an equal sign (=)
            layername = parts[1][parts[1].index('=') + 1:]
            shp_path = path.joinpath(layername).with_suffix('.shp')
            if shp_path.is_file():
                path = shp_path

        return path, query
