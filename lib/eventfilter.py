from pathlib import Path
from platform import system as pf_system

from PyQt5.QtCore import QCoreApplication, QObject, QSettings, Qt, QTranslator
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.utils import is_file


class PathfinderEventFilter(QObject):
    """Filter Object receiving events through eventFilter method.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
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

    def __call__(self, menu, event):  # noqa
        """Add custom actions to the default context menu.
        """
        shift_mod = event.modifiers() == Qt.ShiftModifier
        pf = Pathfinder()

        # return default context menu if no layer is selected
        if not pf.layers_selected:
            return menu

        pf.get_locations()  # list of valid file paths

        cp_action_label = (self.tr('Copy Paths') if len(pf.locs) > 1 else self.tr('Copy Path'))

        # determine position within context menu
        menu_idx = self.set_menu_position(menu)

        # adding stuff bottom to top, so we can just reuse menu_idx for insertion
        menu.insertSeparator(menu.actions()[menu_idx])  # separator below entry

        if pf.unique_parent_dirs():
            open_in_explorer = QAction(
                QIcon(':/plugins/pathfinder/icons/open_in_explorer.svg'),
                self.tr('Show in Explorer'),
                menu,
            )

            open_in_explorer.triggered.connect(lambda: pf.open_in_explorer())
            menu.insertAction(menu.actions()[menu_idx], open_in_explorer)

        # only show entries if there are actual file layers
        if any([is_file(loc[0]) for loc in pf.locs]):

            # give option to copy location with double backslash when shift modifier is pressed
            if pf_system() == 'Windows' and shift_mod:

                cp_src_double_backslash = QAction(
                    QIcon(':/plugins/pathfinder/icons/copy.svg'),
                    f'{cp_action_label} (\\\\)',
                    menu,
                )

                cp_src_double_backslash.triggered.connect(lambda: pf.copy_double_backslash())
                menu.insertAction(menu.actions()[menu_idx], cp_src_double_backslash)

            cp_src = QAction(
                QIcon(':/plugins/pathfinder/icons/copy.svg'),
                cp_action_label,
                menu,
            )

            cp_src.triggered.connect(lambda: pf.copy())
            menu.insertAction(menu.actions()[menu_idx], cp_src)

        menu.insertSeparator(menu.actions()[menu_idx])  # seperator above entry, hidden if on top

        return menu

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
