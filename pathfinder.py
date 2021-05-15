# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pathfinder
 Add layer context menu entries that allow you to copy its source or open
 the file explorer at its location.
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

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.eventfilter import PathfinderEventFilter
from pathfinder.lib.layertreecontextmenumanager import LayerTreeContextMenuManager
from pathfinder.lib.settingsdialog import PathfinderSettingsDialog
from pathfinder.resources import *  # noqa


class PathfinderPlugin:
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

        # setting up keyboard shortcut actions
        self.copy_action1 = QAction('&Copy Path', self.iface.mainWindow())
        self.copy_action2 = QAction('Copy &Path (\\\\)', self.iface.mainWindow())
        self.show_action = QAction('Show in Explore&r', self.iface.mainWindow())

        # register shortcuts
        self.iface.registerMainWindowAction(self.copy_action1, 'Ctrl+E')
        self.iface.registerMainWindowAction(self.copy_action2, 'Ctrl+Shift+E')
        self.iface.registerMainWindowAction(self.show_action, 'Ctrl+R')

        # shortcuts won't work unless actions are added to this menu
        self.iface.addPluginToMenu('&pathfinder', self.copy_action1)
        self.iface.addPluginToMenu('&pathfinder', self.copy_action2)
        self.iface.addPluginToMenu('&pathfinder', self.show_action)

        # bind actions
        self.copy_action1.triggered.connect(lambda: self.on_key_pressed(0))
        self.copy_action2.triggered.connect(lambda: self.on_key_pressed(1))
        self.show_action.triggered.connect(lambda: self.on_key_pressed(2))

        # register settings dialog
        self.settings_dialog = QAction(  # noqa
            QIcon(':/plugins/pathfinder/icons/copy.svg'),
            'pathfinder Settings',
            self.iface.mainWindow()
        )

        self.settings_dialog.triggered.connect(self.show_settings_dialog)
        self.iface.addToolBarIcon(self.settings_dialog)

    def on_key_pressed(self, call_idx):  # noqa
        pf = Pathfinder()
        if pf.layers_selected:
            calls = {0: pf.copy, 1: pf.copy_double_backslash, 2: pf.open_in_explorer}
            pf.parse_selected()
            calls[call_idx]()

    def show_settings_dialog(self):
        self.dialog = PathfinderSettingsDialog()  # noqa
        self.dialog.show()

    def unload(self):
        self.iface.removeToolBarIcon(self.settings_dialog)
        self.iface.unregisterMainWindowAction(self.copy_action1)
        self.iface.unregisterMainWindowAction(self.copy_action2)
        self.iface.unregisterMainWindowAction(self.show_action)
