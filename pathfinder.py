# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathfinder
 Add layer context menu entries to copy source location to clipboard and
 to open in file explorer.
                              -------------------
        begin                : 2020-09-16
        git sha              :
        copyright            :
        email                : silvio.bentzien@protonmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

"""

import subprocess
from pathlib import Path
from platform import system as pf_system

from PyQt5.QtCore import QObject, QEvent, QSettings, Qt, QTranslator, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QApplication

from qgis.core import QgsLayerTree
from qgis.gui import QgsLayerTreeView
from qgis.utils import iface

from .layertreecontextmenumanager import LayerTreeContextMenuManager

from .resources import *


class Pathfinder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):  # noqa
        """Register event filter."""
        self.contextManager = LayerTreeContextMenuManager()
        self.contextManager.addProvider(PathfinderEventFilter())

    def unload(self):
        pass


class PathfinderEventFilter(QObject):
    """Filter Object receiving events through eventFilter method."""

    def __init__(self):
        super().__init__()
        self.system = pf_system()  # get system OS
        self.locs = []

        plugin_dir = Path(__file__).resolve().parent

        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = plugin_dir / "i18n" / f"pathfinder_{locale}.qm"

        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path))
            QCoreApplication.installTranslator(self.translator)

        # platform specific commands to open the system's *most likely* file explorer
        self.commands = {"Windows": "explorer", "Linux": "xdg-open", "Darwin": "open"}

        self.command = self.commands[self.system]

    def __call__(self, menu, event):  # noqa
        """Add custom actions at the end of the default context menu."""

        shift_mod = event.modifiers() == Qt.ShiftModifier
        view = iface.layerTreeView()

        # return default context menu if no layer is selected
        lyrs = self.get_selected_layers(view)
        if not lyrs:
            return menu

        self.locs = self.get_locations(lyrs)  # list of valid file paths

        cp_action_label = (
            self.tr("Copy Paths") if len(self.locs) > 1 else self.tr("Copy Path")
        )

        # determine position within context menu based on present separators
        menu_idx = self.set_menu_position(-3, menu)

        # we add stuff bottom to top, so we can just reuse menu_idx
        menu.insertSeparator(menu.actions()[menu_idx])  # separator below entry

        if self.unique_parent_dirs():
            open_in_explorer = QAction(
                QIcon(":/plugins/copy_source_location/icons/open_in_explorer.svg"),
                self.tr("Show in Explorer"),
                menu,
            )

            open_in_explorer.triggered.connect(self.open_in_explorer)
            menu.insertAction(menu.actions()[menu_idx], open_in_explorer)

        if any(
            [is_file(loc) for loc in self.locs]
        ):  # only show entries if there are actual file layers
            # give option to copy location with double backslash when shift modifier is pressed
            if self.system == "Windows" and shift_mod:
                cp_src_double_backslash = QAction(
                    QIcon(":/plugins/copy_source_location/icons/copy.svg"),
                    f"{cp_action_label} (\\\\)",
                    menu,
                )

                cp_src_double_backslash.triggered.connect(
                    self.paths_to_clipboard_double_backslash
                )
                menu.insertAction(menu.actions()[menu_idx], cp_src_double_backslash)

            cp_src = QAction(
                QIcon(":/plugins/copy_source_location/icons/copy.svg"),
                cp_action_label,
                menu,
            )

            cp_src.triggered.connect(self.paths_to_clipboard)
            menu.insertAction(menu.actions()[menu_idx], cp_src)

        menu.insertSeparator(
            menu.actions()[menu_idx]
        )  # seperator above entry, hidden if on top

        return menu

    def paths_to_clipboard(self):  # noqa
        """Copy paths to clipboard making use of pandas.Series.to_clipboard() method.
        Multiple file paths are enclosed in double quotes and separated by a space.
        A single path is not quoted.
        """
        s = (
            " ".join([f'"{str(p)}"' for p in self.locs])
            if len(self.locs) > 1
            else str(self.locs[0])
        )
        QApplication.clipboard().setText(s)

    def paths_to_clipboard_double_backslash(self):  # noqa
        """Copy comma separated list of paths with two backslashes to clipboard."""

        s = ",".join([str(p).replace("\\", "\\\\") for p in self.locs])

        QApplication.clipboard().setText(s)

    def open_in_explorer(self):  # noqa
        """Open unique parent directories in a file explorer."""
        for p in self.unique_parent_dirs():
            subprocess.run([self.command, str(p)])

    def get_selected_layers(self, view: QgsLayerTreeView) -> list:  # noqa
        """Return list of selected layers from view.

        :param view: QgsLayerTreeView instance.
        :return: List of selected nodes that are layers.
        """
        return [n for n in view.selectedNodes() if QgsLayerTree.isLayer(n)]

    def get_locations(self, lyrs: list) -> list:  # noqa
        """Return all unique valid file locations from list of layers.

        :param lyrs: List of QGIS layers.
        :return: List of distinct and valid file paths.
        """
        return list(
            filter(
                lambda x: is_file(x),
                set([Path(clean_path(n.layer().source())) for n in lyrs]),
            )
        )

    def set_menu_position(self, idx: int, menu: QMenu) -> int:  # noqa
        """Return menu index of the idxth separator object.

        :param idx: Number of separator we want to use to insert our actions at.
        :param menu: QMenu object.
        :return: Index of the target separator.
        """
        # TODO: make sure index idx is never out of range
        return [i for i, a in enumerate(menu.actions()) if a.isSeparator()][idx]

    def unique_parent_dirs(self) -> list:
        """Return list of unique parent directories from list of paths.

        :return: List of unique parent directories paths within self.locs.
        """
        return list(set([loc.parent for loc in self.locs]))


def is_file(loc: Path) -> bool:
    """Path.is_file(), but return False instead of raising OSErrors.

    :param loc: pathlib.Path object.
    :return: Whether this path is a regular file.
    """
    try:
        if loc.is_file():
            return True
    except OSError:
        return False


def clean_path(path: str) -> str:  # noqa
    """Strip common appendices from path string.

    :param path: String that could be a file path.
    :return: Cleaned path string.
    """
    return path.split("|")[0].split("?")[0].replace("file:", "")

