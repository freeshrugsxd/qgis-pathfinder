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
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction
from qgis.gui import QgisInterface

from .resources import *  # noqa

try:
    # dev import
    from lib.eventfilter import PathfinderEventFilter
    from lib.settingsdialog import PathfinderSettingsDialog
    from lib.layertreecontextmenumanager import LayerTreeContextMenuManager
except ModuleNotFoundError:
    # qgis import
    from pathfinder.lib.eventfilter import PathfinderEventFilter  # noqa
    from pathfinder.lib.settingsdialog import PathfinderSettingsDialog  # noqa
    from pathfinder.lib.layertreecontextmenumanager import LayerTreeContextMenuManager  # noqa


class Pathfinder:
    """QGIS Plugin Implementation."""

    def __init__(self, iface: QgisInterface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        """
        # Save reference to the QGIS interface
        self.iface = iface

    def initGui(self):  # noqa
        """Register event filter and add toolbar icon."""
        self.contextManager = LayerTreeContextMenuManager()  # noqa
        self.contextManager.addProvider(PathfinderEventFilter())

        self.settings_dialog = QAction(  # noqa
            QIcon(':/plugins/pathfinder/icons/copy.svg'),
            'pathfinder',
            self.iface.mainWindow())

        self.settings_dialog.triggered.connect(self.show_settings_dialog)
        self.iface.addToolBarIcon(self.settings_dialog)

    def show_settings_dialog(self):
        self.dialog = PathfinderSettingsDialog()  # noqa
        self.dialog.show()

    def unload(self):
        self.iface.removeToolBarIcon(self.settings_dialog)
