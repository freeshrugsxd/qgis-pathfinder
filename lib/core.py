import subprocess
from pathlib import Path
from platform import system as pf_system
from typing import List
from urllib.parse import urlparse
from urllib.request import url2pathname

from PyQt5.QtCore import QObject, QSettings
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsLayerTree
from qgis.utils import iface

from pathfinder.lib.i18n import tr
from pathfinder.lib.utils import get_char, exists, PathfinderMaps

DEFAULTS = PathfinderMaps().DEFAULTS
COMMANDS = PathfinderMaps().COMMANDS


class Pathfinder(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.locs = []
        self.selected_layers = []
        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

        self.command = COMMANDS[pf_system()]

    def copy(self) -> None:
        """Copy paths to clipboard."""
        text = self.build_string(self.locs)
        QApplication.clipboard().setText(text)
        self.notify(text)

    def copy_double_backslash(self) -> None:
        """Copy paths to clipboard with double backslashes."""
        text = self.build_string(self.locs).replace('\\', '\\\\')
        QApplication.clipboard().setText(text)
        self.notify(text)

    def notify(self, text: str) -> None:
        """Show QGIS notification."""
        if self.settings.value('show_notification', type=bool):
            iface.messageBar().pushMessage(tr('Copied to clipboard'), text, level=0, duration=4)

    def open_in_explorer(self) -> None:
        """Open unique parent directories in a file explorer."""
        # TODO: select files in file explorer
        for p in self.unique_parent_dirs():
            subprocess.run([self.command, str(p)])

    def parse_selected(self) -> None:
        """Parse selected layers. Populate self.locs."""
        for lyr in self.selected_layers:
            path, query = self.parse_path(lyr.layer().source())
            if path is not None:
                self.locs.append((path, query))

    def unique_parent_dirs(self) -> List[Path]:
        """Return list of unique parent directories from list of paths.

        :return: List of unique parent directories paths within self.locs.
        """
        return list(set([path.parent for path, query in self.locs]))

    @property
    def layers_selected(self) -> bool:
        """Check if there are any layers selected.

        :return: Whether there are any layers selected.
        """
        view = iface.layerTreeView()
        self.selected_layers = [n for n in view.selectedNodes() if QgsLayerTree.isLayer(n)]
        return len(self.selected_layers) > 0

    @staticmethod
    def build_string(paths: List[tuple]) -> str:
        """Construct a string using pathfinders current settings.

        :param paths: A list of tuples (path, query) where the first item contains
        the valid file path and the second contains data provider information such
        as the layer name and subset string.
        :return: Formatted string representing one or more file paths.
        """
        settings = QSettings()
        settings.beginGroup('pathfinder')
        n = len(paths)

        q = get_char('quote_char')
        s = get_char('separ_char')

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
    def parse_path(path: str, must_exist: bool = True) -> tuple:
        """Strip common appendices from path string according to pathfinder settings.

        :param path: String that could be a file path.
        :param must_exist: Whether path has to be a file or folder.
        :return: Tuple containing a valid file path and the desired data provider information.
        """
        # TODO:
        #  - come up with a more clear return than a tuple
        settings = QSettings()
        settings.beginGroup('pathfinder')
        parts = path.split('?')[0].split('|')

        try:
            if parts[0].startswith('file:'):
                # convert uri to path
                fp = Path(url2pathname(urlparse(parts[0]).path))
            else:
                fp = Path(parts[0])
        except OSError:
            # return None for now
            return None, None

        if must_exist and not exists(fp):
            return None, None

        n = len(parts)
        has_layer_name = n > 1
        is_subset = n > 2

        query = ''

        if fp.is_dir():
            # vector dataset was loaded from a directory
            layername = parts[1].split('=')[1]
            shp_path = fp.joinpath(layername).with_suffix('.shp')
            if shp_path.exists():
                return shp_path, query

        if has_layer_name and settings.value('incl_layer_name', type=bool):
            query += f'|{parts[1]}'

        if is_subset and settings.value('incl_subset_str', type=bool):
            query += f'|{parts[2]}'

        return fp, query
