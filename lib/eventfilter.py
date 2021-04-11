import subprocess
from pathlib import Path
from platform import system as pf_system

from PyQt5.QtCore import QCoreApplication, QObject, QSettings, Qt, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QApplication, QMenu

from qgis.core import QgsLayerTree, QgsLayerTreeNode
from qgis.gui import QgsLayerTreeView
from qgis.utils import iface

try:
    # dev import
    from lib.utils import build_string, parse_path, is_file
except ModuleNotFoundError:
    # qgis import
    from pathfinder.lib.utils import build_string, parse_path, is_file  # noqa


class PathfinderEventFilter(QObject):
    """Filter Object receiving events through eventFilter method.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.system = pf_system()  # get system OS
        self.locs = []

        self.settings = QSettings()

        plugin_dir = Path(__file__).resolve().parent

        # initialize locale
        locale = self.settings.value('locale/userLocale')[0:2]
        locale_path = plugin_dir / 'i18n' / f'pathfinder_{locale}.qm'

        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path))
            QCoreApplication.installTranslator(self.translator)

        # platform specific commands to open the system's *most likely* file explorer
        commands = {'Windows': 'explorer', 'Linux': 'xdg-open', 'Darwin': 'open'}

        self.command = commands[self.system]

    def __call__(self, menu, event):  # noqa
        """Add custom actions to the default context menu.
        """
        shift_mod = event.modifiers() == Qt.ShiftModifier
        view = iface.layerTreeView()

        # return default context menu if no layer is selected
        lyrs = self.get_selected_layers(view)
        if not lyrs:
            return menu

        self.locs = self.get_locations(lyrs)  # list of valid file paths

        cp_action_label = (self.tr('Copy Paths') if len(self.locs) > 1 else self.tr('Copy Path'))

        # determine position within context menu
        menu_idx = self.set_menu_position(menu)

        # adding stuff bottom to top, so we can just reuse menu_idx for insertion
        menu.insertSeparator(menu.actions()[menu_idx])  # separator below entry

        if self.unique_parent_dirs():
            open_in_explorer = QAction(
                QIcon(':/plugins/pathfinder/icons/open_in_explorer.svg'),
                self.tr('Show in Explorer'),
                menu,
            )

            open_in_explorer.triggered.connect(self.open_in_explorer)
            menu.insertAction(menu.actions()[menu_idx], open_in_explorer)

        # only show entries if there are actual file layers
        if any([is_file(loc[0]) for loc in self.locs]):

            # give option to copy location with double backslash when shift modifier is pressed
            if self.system == 'Windows' and shift_mod:

                cp_src_double_backslash = QAction(
                    QIcon(':/plugins/pathfinder/icons/copy.svg'),
                    f'{cp_action_label} (\\\\)',
                    menu,
                )

                cp_src_double_backslash.triggered.connect(self.paths_to_clipboard_double_backslash)
                menu.insertAction(menu.actions()[menu_idx], cp_src_double_backslash)

            cp_src = QAction(
                QIcon(':/plugins/pathfinder/icons/copy.svg'),
                cp_action_label,
                menu,
            )

            cp_src.triggered.connect(self.paths_to_clipboard)
            menu.insertAction(menu.actions()[menu_idx], cp_src)

        menu.insertSeparator(menu.actions()[menu_idx])  # seperator above entry, hidden if on top

        return menu

    def paths_to_clipboard(self):  # noqa
        """Copy paths to clipboard.
        """
        QApplication.clipboard().setText(build_string(self.locs))

    def paths_to_clipboard_double_backslash(self):  # noqa
        """Copy paths to clipboard but substitude extra backslashes for UTF-8 pasting.
        """
        QApplication.clipboard().setText(build_string(self.locs).replace('\\', '\\\\'))

    def open_in_explorer(self):  # noqa
        """Open unique parent directories in a file explorer.
        """
        # TODO: select files in file explorer
        for p in self.unique_parent_dirs():
            subprocess.run([self.command, str(p)])

    def get_selected_layers(self, view: QgsLayerTreeView) -> list[QgsLayerTreeNode]:  # noqa
        """Return list of selected layers from view.

        :param view: QgsLayerTreeView instance.
        :return: List of selected nodes that are layers.
        """
        return [n for n in view.selectedNodes() if QgsLayerTree.isLayer(n)]

    def get_locations(self, lyrs: list[QgsLayerTreeNode]) -> list[tuple]:  # noqa
        """Return all unique valid file locations from list of layers.

        :param lyrs: A list of QGIS layers.
        :return: A list of tuples containing a valid file path and it's data provider
        information respective to the pathfinder settings.
        """
        return [(p, i) for p, i in [parse_path(n.layer().source()) for n in lyrs] if p]

    def set_menu_position(self, menu: QMenu, idx: int = -3) -> int:  # noqa
        """Return menu index of the `idxth` separator object.
        If idx is out of bounds, gradually change its value towards 0.

        :param idx: Index of desired separator object.
        :param menu: QMenu object.
        :return: Index of the target separator.
        """
        try:
            return [i for i, a in enumerate(menu.actions()) if a.isSeparator()][idx]
        except IndexError:
            return self.set_menu_position(menu, idx - 1 if idx > 0 else idx + 1)

    def unique_parent_dirs(self) -> list[Path]:
        """Return list of unique parent directories from list of paths.

        :return: List of unique parent directories paths within self.locs.
        """
        return list(set([p.parent for p, i in self.locs]))
