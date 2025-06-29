from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtWidgets import QAction

from pathfinder.icons import icon_copy_path, icon_open_in_explorer
from pathfinder.lib.core import Pathfinder
from pathfinder.lib.gui import PathfinderSettingsDialog, modify_context_menu
from pathfinder.lib.i18n import tr
from pathfinder.lib.settings import Settings
from pathfinder.lib.constants import PLUGIN_DIR

# noinspection PyAttributeOutsideInit
class PathfinderPlugin:
    def __init__(self, iface: QgisInterface):
        self.iface = iface
        settings = QSettings()

        # initialize locale and translator
        locale = settings.value('locale/userLocale')[0:2]

        if (locale_path := PLUGIN_DIR / 'i18n' / f'pathfinder_{locale}.qm').exists():
            self.translator = QTranslator()
            self.translator.load(str(locale_path))
            QCoreApplication.installTranslator(self.translator)

        self.dialog = None
        self.menu = None

    # noinspection PyPep8Naming
    def initGui(self):
        """Register event filter and add toolbar icon."""
        self.iface.layerTreeView().contextMenuAboutToShow.connect(modify_context_menu)

        # register settings
        Settings()

        # setting up keyboard shortcut actions
        self.copy_action1 = QAction(icon_copy_path, tr('Copy Path'), self.iface.mainWindow())
        self.copy_action2 = QAction(icon_copy_path, tr('Copy Path (\\\\)'), self.iface.mainWindow())
        self.show_action = QAction(icon_open_in_explorer, tr('Show in Explorer'), self.iface.mainWindow())

        # register shortcuts
        self.iface.registerMainWindowAction(action=self.copy_action1, defaultShortcut=None)
        self.iface.registerMainWindowAction(action=self.copy_action2, defaultShortcut=None)
        self.iface.registerMainWindowAction(action=self.show_action, defaultShortcut=None)

        # bind actions
        self.copy_action1.triggered.connect(lambda: self.on_triggered('copy'))
        self.copy_action2.triggered.connect(lambda: self.on_triggered('copy_double_backslash'))
        self.show_action.triggered.connect(lambda: self.on_triggered('open_in_explorer'))

        # register settings dialog
        self.settings_dialog = QAction(icon_copy_path, tr('Settings…'), self.iface.mainWindow())
        self.settings_dialog.triggered.connect(self.show_settings_dialog)
        self.iface.addToolBarIcon(self.settings_dialog)

        # shortcuts won't work unless actions are added to this menu
        self.menu = self.iface.pluginMenu().addMenu(icon_copy_path, '&pathfinder')
        self.menu.addAction(self.copy_action1)
        self.menu.addAction(self.copy_action2)
        self.menu.addAction(self.show_action)
        self.menu.addSeparator()
        self.menu.addAction(self.settings_dialog)

    # noinspection PyMethodMayBeStatic
    def on_triggered(self, fn):
        """Call pathfinder method.

        Args:
            fn: method name

        """
        if (pf := Pathfinder()).layers_selected:
            pf.parse_selected()
            getattr(pf, fn)()

    def show_settings_dialog(self):
        """Show pathfinder settings dialog."""
        if self.dialog is None:
            self.dialog = PathfinderSettingsDialog(self.iface.mainWindow())

        self.dialog.show()
        self.dialog.activateWindow()

    def unload(self):
        self.iface.removeToolBarIcon(self.settings_dialog)
        self.iface.pluginMenu().removeAction(self.menu.menuAction())
        self.iface.unregisterMainWindowAction(self.copy_action1)
        self.iface.unregisterMainWindowAction(self.copy_action2)
        self.iface.unregisterMainWindowAction(self.show_action)
        self.iface.layerTreeView().contextMenuAboutToShow.disconnect(modify_context_menu)
        Settings.unregister()
        del self.dialog
