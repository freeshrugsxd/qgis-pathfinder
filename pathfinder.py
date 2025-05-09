from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.gui import PathfinderSettingsDialog, modify_context_menu
from pathfinder.lib.i18n import tr
from pathfinder.lib.utils import PLUGIN_DIR

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

    # noinspection PyPep8Naming
    def initGui(self):
        """Register event filter and add toolbar icon."""
        self.iface.layerTreeView().contextMenuAboutToShow.connect(modify_context_menu)

        # setting up keyboard shortcut actions
        self.copy_action1 = QAction(QIcon(f'{PLUGIN_DIR}/icons/copy.svg'), tr('Copy Path'), self.iface.mainWindow())
        self.copy_action2 = QAction(QIcon(f'{PLUGIN_DIR}/icons/copy.svg'), tr('Copy Path (\\\\)'), self.iface.mainWindow())
        self.show_action = QAction(QIcon(f'{PLUGIN_DIR}/icons/open_in_explorer.svg'), tr('Show in Explorer'), self.iface.mainWindow())

        # register shortcuts
        self.iface.registerMainWindowAction(self.copy_action1, 'Ctrl+E')
        self.iface.registerMainWindowAction(self.copy_action2, 'Ctrl+Shift+E')
        self.iface.registerMainWindowAction(self.show_action,  'Ctrl+R')

        # shortcuts won't work unless actions are added to this menu
        self.iface.addPluginToMenu('&pathfinder', self.copy_action1)
        self.iface.addPluginToMenu('&pathfinder', self.copy_action2)
        self.iface.addPluginToMenu('&pathfinder', self.show_action)

        # bind actions
        self.copy_action1.triggered.connect(lambda: self.on_triggered('copy'))
        self.copy_action2.triggered.connect(lambda: self.on_triggered('copy_double_backslash'))
        self.show_action.triggered.connect(lambda: self.on_triggered('open_in_explorer'))

        # register settings dialog
        self.settings_dialog = QAction(QIcon(f'{PLUGIN_DIR}/icons/copy.svg'), tr('pathfinder Settings'), self.iface.mainWindow())
        self.settings_dialog.triggered.connect(self.show_settings_dialog)
        self.iface.addToolBarIcon(self.settings_dialog)


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
        self.iface.removePluginMenu('&pathfinder', self.copy_action1)
        self.iface.removePluginMenu('&pathfinder', self.copy_action2)
        self.iface.removePluginMenu('&pathfinder', self.show_action)
        self.iface.unregisterMainWindowAction(self.copy_action1)
        self.iface.unregisterMainWindowAction(self.copy_action2)
        self.iface.unregisterMainWindowAction(self.show_action)
        self.iface.layerTreeView().contextMenuAboutToShow.disconnect(modify_context_menu)
        del self.dialog
