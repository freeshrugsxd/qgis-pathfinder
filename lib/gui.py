from pathlib import Path

from qgis.core import QgsApplication
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDialog, QDialogButtonBox

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.i18n import tr
from pathfinder.lib.settings import Settings
from pathfinder.lib.constants import PLUGIN_DIR, SYSTEM_IS_WINDOWS

FORM_CLASS, _ = uic.loadUiType(PLUGIN_DIR / 'ui' / 'settingsdiag.ui')

class PathfinderSettingsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.settings = Settings()

        self.connect_handlers()
        self.restore_settings()
        self.update_preview()

    def connect_handlers(self):
        # comboboxes https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QComboBox.html
        self.quote_cbox.currentTextChanged.connect(lambda v: self.on_curr_changed('quote_char', v))
        self.separ_cbox.currentTextChanged.connect(lambda v: self.on_curr_changed('separ_char', v))

        # lineedits https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QLineEdit.html
        self.quote_char_custom.textChanged.connect(lambda v: self.on_changed('quote_char_custom', v))
        self.separ_char_custom.textChanged.connect(lambda v: self.on_changed('separ_char_custom', v))
        self.prefix.textChanged.connect(lambda v: self.on_changed('prefix', v))
        self.postfix.textChanged.connect(lambda v: self.on_changed('postfix', v))

        # checkboxes https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QCheckBox.html
        self.incl_file_name.stateChanged.connect(lambda v: self.on_changed('incl_file_name', v))
        self.incl_layer_name.stateChanged.connect(lambda v: self.on_changed('incl_layer_name', v))
        self.incl_subset_str.stateChanged.connect(lambda v: self.on_changed('incl_subset_str', v))
        self.single_path_quote.stateChanged.connect(lambda v: self.on_changed('single_path_quote', v))
        self.single_path_affix.stateChanged.connect(lambda v: self.on_changed('single_path_affix', v))
        self.paths_on_new_line.stateChanged.connect(lambda v: self.on_changed('paths_on_new_line', v))
        self.show_notification.stateChanged.connect(lambda v: self.on_changed('show_notification', v))
        self.original_vrt_ds.stateChanged.connect(lambda v: self.on_changed('original_vrt_ds', v))

        # spin box https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QSpinBox.html
        self.notify_duration.valueChanged.connect(lambda v: self.on_changed('notify_duration', v))

        # buttons https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QDialogButtonBox.html
        self.buttonBox.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self.restore_defaults)

    def restore_settings(self):
        """Reflect pathfinder's current settings inside the settings dialog."""
        self.quote_cbox.setCurrentText(self.settings.quote_char.value())
        self.separ_cbox.setCurrentText(self.settings.separ_char.value())

        self.quote_char_custom.setText(self.settings.quote_char_custom.value())
        self.separ_char_custom.setText(self.settings.separ_char_custom.value())
        self.prefix.setText(self.settings.prefix.value())
        self.postfix.setText(self.settings.postfix.value())

        self.incl_file_name.setChecked(self.settings.incl_file_name.value())
        self.incl_layer_name.setChecked(self.settings.incl_layer_name.value())
        self.incl_subset_str.setChecked(self.settings.incl_subset_str.value())
        self.single_path_quote.setChecked(self.settings.single_path_quote.value())
        self.single_path_affix.setChecked(self.settings.single_path_affix.value())
        self.paths_on_new_line.setChecked(self.settings.paths_on_new_line.value())
        self.show_notification.setChecked(self.settings.show_notification.value())
        self.original_vrt_ds.setChecked(self.settings.original_vrt_ds.value())

        self.notify_duration.setValue(self.settings.notify_duration.value())

    def on_curr_changed(self, key, value):
        """Enable/disable custom character lineEdit and forward key and value to on_changed().

        Args:
            key (str): The name of the setting.
            value (str): The new value of the setting.

        """
        getattr(self, f'{key}_custom').setEnabled(value == tr('Other'))
        self.on_changed(key, value)

    def on_changed(self, key, value):
        """Change the setting key to value and update the preview.

        Args:
            key (str): The name of the setting.
            value (str): The new value of the setting.

        """
        getattr(self.settings, key).setValue(value)
        self.update_preview()

    def update_preview(self, n=2):
        """Build n strings from a mock path and display it in the paths_preview QLabel.

        Args:
            n (int): The number of mock paths to be displayed in the preview. Optional. [default: 2]

        """
        pf = Pathfinder()

        base_dict = {
            'provider': 'ogr',
            'path': 'dir/subdir/file.ext',
        }

        if self.settings.incl_layer_name.value():
            base_dict['layerName'] = 'lyr'

        if self.settings.incl_subset_str.value():
            base_dict['subset'] = 'id > 0'

        parsed = [base_dict.copy() for _ in range(n)]
        out = pf.build_string(parsed)
        self.paths_preview.setText(out)

    def restore_defaults(self):
        """Reset settings to their default values."""
        for setting in self.settings.settings_node.childrenSettings():
            setting.setValue(setting.defaultValue())

        self.restore_settings()
        self.show()

    def keyPressEvent(self, event):
        """Do things on key press.

        Args:
            event (QKeyEvent): a Qt key event

        """
        # close dialog on Escape
        if event.key() == Qt.Key.Key_Escape:
            self.close()


def determine_menu_position(menu, idx=-3):
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
    if not (separators:=[i for i, a in enumerate(menu.actions()) if a.isSeparator()]):
        return 0

    while idx < -len(separators):
        idx += 1
    while idx >= len(separators):
        idx -= 1

    return separators[idx]


def modify_context_menu(menu):
    """Add pathfinder entries to context menu.

    Args:
        menu (QMenu): context menu object

    """
    if (pf := Pathfinder()).layers_selected:
        pf.parse_selected()  # parse selected layers and populate pf.locs

        # only show entries if there are existing files selected
        if any(Path(d['path']).exists() for d in pf.locs):
            cp_action_label = tr('Copy Paths') if len(pf.locs) > 1 else tr('Copy Path')

            # determine position within context menu
            # there is an invisible separator that is gone when more than one layer is selected ???
            idx = -2 if len(pf.selected_layers) > 1 else -3
            menu_idx = determine_menu_position(menu, idx)

            # adding stuff bottom to top, so we can just reuse menu_idx for insertion
            menu.insertSeparator(menu.actions()[menu_idx])  # separator below entry
            open_in_explorer = QAction(QIcon(f'{PLUGIN_DIR}/icons/open_in_explorer.svg'), tr('Show in Explorer'), menu)
            open_in_explorer.triggered.connect(pf.open_in_explorer)
            menu.insertAction(menu.actions()[menu_idx], open_in_explorer)

            # give option to copy location with double backslash when shift modifier is pressed
            shift_mod = QgsApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier
            if shift_mod and SYSTEM_IS_WINDOWS:
                cp_src_double_backslash = QAction(QIcon(f'{PLUGIN_DIR}/icons/copy.svg'), f'{cp_action_label} (\\\\)', menu)
                cp_src_double_backslash.triggered.connect(lambda: pf.copy_double_backslash())
                menu.insertAction(menu.actions()[menu_idx], cp_src_double_backslash)

            cp_src = QAction(QIcon(f'{PLUGIN_DIR}/icons/copy.svg'), cp_action_label, menu)
            cp_src.triggered.connect(lambda: pf.copy())
            menu.insertAction(menu.actions()[menu_idx], cp_src)
            menu.insertSeparator(menu.actions()[menu_idx])  # seperator above entry, hidden if on top
