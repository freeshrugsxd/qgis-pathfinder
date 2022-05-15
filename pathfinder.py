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
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.gui import QgisInterface

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.eventfilter import PathfinderEventFilter
from pathfinder.lib.layertreecontextmenumanager import LayerTreeContextMenuManager
from pathfinder.lib.settingsdialog import PathfinderSettingsDialog
from pathfinder.lib.i18n import tr

from pathfinder.resources import *  # noqa


# noinspection PyAttributeOutsideInit
class PathfinderPlugin:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        settings = QSettings()

        plugin_dir = Path(__file__).resolve().parent

        # initialize locale and translator
        locale = settings.value('locale/userLocale')[0:2]
        locale_path = plugin_dir / 'i18n' / f'pathfinder_{locale}.qm'

        if locale_path.exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path))
            QCoreApplication.installTranslator(self.translator)

    # noinspection PyPep8Naming
    def initGui(self):
        """Register event filter and add toolbar icon."""
        self.contextManager = LayerTreeContextMenuManager()
        self.contextManager.addProvider(PathfinderEventFilter())

        # setting up keyboard shortcut actions
        self.copy_action1 = QAction(tr('Copy Path'), self.iface.mainWindow())
        self.copy_action2 = QAction(tr('Copy Path (\\\\)'), self.iface.mainWindow())
        self.show_action = QAction(tr('Show in Explorer'), self.iface.mainWindow())

        # register shortcuts
        self.iface.registerMainWindowAction(self.copy_action1, 'Ctrl+E')
        self.iface.registerMainWindowAction(self.copy_action2, 'Ctrl+Shift+E')
        self.iface.registerMainWindowAction(self.show_action,  'Ctrl+R')

        # shortcuts won't work unless actions are added to this menu
        self.iface.addPluginToMenu('&pathfinder', self.copy_action1)
        self.iface.addPluginToMenu('&pathfinder', self.copy_action2)
        self.iface.addPluginToMenu('&pathfinder', self.show_action)

        # bind actions
        self.copy_action1.triggered.connect(lambda: self.on_key_pressed(0))
        self.copy_action2.triggered.connect(lambda: self.on_key_pressed(1))
        self.show_action.triggered.connect(lambda: self.on_key_pressed(2))

        # register settings dialog
        self.settings_dialog = QAction(
            QIcon(':/plugins/pathfinder/icons/copy.svg'),
            tr('pathfinder Settings'),
            self.iface.mainWindow()
        )

        self.settings_dialog.triggered.connect(self.show_settings_dialog)
        self.iface.addToolBarIcon(self.settings_dialog)

    # noinspection PyMethodMayBeStatic
    def on_key_pressed(self, call_idx):
        pf = Pathfinder()
        if pf.layers_selected:
            calls = {0: pf.copy, 1: pf.copy_double_backslash, 2: pf.open_in_explorer}
            pf.parse_selected()
            calls[call_idx]()

    def show_settings_dialog(self):
        self.dialog = PathfinderSettingsDialog()
        self.dialog.show()

    def unload(self):
        self.iface.removeToolBarIcon(self.settings_dialog)
        self.iface.unregisterMainWindowAction(self.copy_action1)
        self.iface.unregisterMainWindowAction(self.copy_action2)
        self.iface.unregisterMainWindowAction(self.show_action)
        del self.contextManager

