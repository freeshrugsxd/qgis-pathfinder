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

from pathfinder.lib.utils import DEFAULTS, get_char, is_file


class Pathfinder(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.locs = []
        self.selected_layers = []
        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

        # platform specific commands to open the system's *most likely* file explorer
        commands = {'Windows': 'explorer', 'Linux': 'xdg-open', 'Darwin': 'open'}
        self.command = commands[pf_system()]

    def copy(self) -> None:
        """Copy paths to clipboard."""
        text = self.build_string(self.locs)
        QApplication.clipboard().setText(text)
        self.notify(text)

    def copy_double_backslash(self) -> None:
        """Copy paths to clipboard but substitude extra backslashes for UTF-8 pasting."""
        text = self.build_string(self.locs).replace('\\', '\\\\')
        QApplication.clipboard().setText(text)
        self.notify(text)

    def notify(self, text: str) -> None:
        if self.settings.value('show_notification', type=bool):
            iface.messageBar().pushMessage('Copied to clipboard', text, level=0, duration=4)

    def open_in_explorer(self) -> None:
        """Open unique parent directories in a file explorer."""
        # TODO: select files in file explorer
        for p in self.unique_parent_dirs():
            subprocess.run([self.command, str(p)])

    def parse_selected(self) -> None:
        """Extract viable layers and parse their source."""
        self.locs = [(p, q) for p, q in [self.parse_path(n.layer().source()) for n in self.selected_layers] if p]

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
    def build_string(paths: List[tuple]) -> str:  # noqa
        """Construct a string using pathfinders current settings.

        :param paths: A list of tuples (path, info) where paths[0] contains the valid file path
        and paths[1] contains data provider information such as the layer name and
        subset string.
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
    def parse_path(path: str, must_be_file: bool = True) -> tuple:
        """Strip common appendices from path string according to pathfinder settings.

        :param path: String that could be a file path.
        :param must_be_file: Whether path has to be a file or not.
        :return: Tuple containing a valid file path and the desired data provider information.
        """
        # TODO:
        #  - allow for non file layer to successfully pass through here
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
            # TODO: fix Bad URL error when a XYZ layer comes through here
            # return None for now
            return None, None

        # return tuple of Nones if s
        if must_be_file and not is_file(fp):
            return None, None

        n = len(parts)
        has_layer_name = n > 1
        is_subset = n > 2

        query = ''

        if has_layer_name and settings.value('incl_layer_name', type=bool):
            query += f'|{parts[1]}'

        if is_subset and settings.value('incl_subset_str', type=bool):
            query += f'|{parts[2]}'

        return fp, query
