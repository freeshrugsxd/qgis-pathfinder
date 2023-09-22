from platform import system as pf_system

from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtGui import QContextMenuEvent, QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.utils import tr


class PathfinderEventFilter(QObject):
    """Filter Object receiving events through eventFilter method."""

    def __init__(self, parent=None):
        super().__init__(parent)

    def __call__(self, menu, event):
        """Add custom actions to the default context menu.

        Args:
            menu (QMenu): the context menu object
            event (QContextMenuEvent): the event

        Returns:
            QMenu: Context menu
        """
        pf = Pathfinder()

        # return default context menu if no layer is selected
        if not pf.layers_selected:
            return menu

        shift_mod = event.modifiers() == Qt.ShiftModifier

        # parse data sources of selected layers and populate pf.locs
        pf.parse_selected()

        cp_action_label = (tr('Copy Paths') if len(pf.locs) > 1 else tr('Copy Path'))

        # determine position within context menu
        menu_idx = self.set_menu_position(menu)

        # adding stuff bottom to top, so we can just reuse menu_idx for insertion
        menu.insertSeparator(menu.actions()[menu_idx])  # separator below entry

        if pf.unique_parent_dirs:
            open_in_explorer = QAction(
                QIcon(':/plugins/pathfinder/icons/open_in_explorer.svg'),
                tr('Show in Explorer'),
                menu,
            )

            open_in_explorer.triggered.connect(lambda: pf.open_in_explorer())
            menu.insertAction(menu.actions()[menu_idx], open_in_explorer)

        # only show entries if there are files selected
        if any([path.exists() for path, _ in pf.locs]):

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

    def set_menu_position(self, menu, idx=-3):
        """Return menu index of the idxᵗʰ separator object.

        If idx is out of bounds, gradually change its value towards 0.

        Note:
            We position the pathfinder menu items based on already available
            separator items in the menu. I want to place it roughly next to the
            Export sub menu, that's why we default to -3.

        Args:
            menu (QMenu): QMenu object.
            idx (int): Index of desired separator object.

        Returns:
            int: Index of the target separator.
        """
        try:
            return [i for i, a in enumerate(menu.actions()) if a.isSeparator()][idx]
        except IndexError:
            return self.set_menu_position(menu, idx - 1 if idx > 0 else idx + 1)
