from pathlib import Path

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from qgis.PyQt import uic

from pathfinder.lib.core import Pathfinder
from pathfinder.lib.utils import DEFAULTS

# TODO:
#  - update translations for settings

FORM_CLASS, _ = uic.loadUiType(Path(__file__).parents[1] / 'ui' / 'settingsdiag.ui')


class PathfinderSettingsDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        super(PathfinderSettingsDialog, self).__init__(parent)
        self.setupUi(self)

        self.settings = QSettings()
        self.settings.beginGroup('pathfinder')

        self.create_bindings()
        self.restore_settings()
        self.update_preview()

    def create_bindings(self) -> None:
        """Create bindings for the all elements."""
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

        # buttons https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QDialogButtonBox.html
        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_defaults)

    def restore_settings(self) -> None:
        """Reflect pathfinder's current settings inside the settings dialog."""
        self.quote_cbox.setCurrentText(self.settings.value('quote_char', DEFAULTS['quote_char']))
        self.separ_cbox.setCurrentText(self.settings.value('separ_char', DEFAULTS['separ_char']))

        self.quote_char_custom.setText(self.settings.value('quote_char_custom', DEFAULTS['quote_char_custom']))
        self.separ_char_custom.setText(self.settings.value('separ_char_custom', DEFAULTS['separ_char_custom']))
        self.prefix.setText(self.settings.value('prefix', DEFAULTS['prefix']))
        self.postfix.setText(self.settings.value('postfix', DEFAULTS['postfix']))

        # cast state to int because the value is returned as string from persistent storage
        self.incl_file_name.setCheckState(self.settings.value('incl_file_name', DEFAULTS['incl_file_name'], int))
        self.incl_layer_name.setCheckState(self.settings.value('incl_layer_name', DEFAULTS['incl_layer_name'], int))
        self.incl_subset_str.setCheckState(self.settings.value('incl_subset_str', DEFAULTS['incl_subset_str'], int))
        self.single_path_quote.setCheckState(self.settings.value('single_path_quote', DEFAULTS['single_path_quote'], int))
        self.single_path_affix.setCheckState(self.settings.value('single_path_affix', DEFAULTS['single_path_affix'], int))
        self.paths_on_new_line.setCheckState(self.settings.value('paths_on_new_line', DEFAULTS['paths_on_new_line'], int))
        self.show_notification.setCheckState(self.settings.value('show_notification', DEFAULTS['show_notification'], int))

    def on_curr_changed(self, key: str, value: str) -> None:
        """Enable/Disable corresponding custom character lineedit if necessary and forward
        key and value to on_changed().

        :param key: The name of the setting.
        :param value: The new value of the setting.
        """
        getattr(self, f'{key}_custom').setEnabled(value == self.tr('Other'))
        self.on_changed(key, value)

    def on_changed(self, key: str, value: str) -> None:
        """Change the setting ``key`` to ``value`` and update the preview.

        :param key: The name of the setting.
        :param value: The new value of the setting.
        """
        self.settings.setValue(key, value)
        self.update_preview()

    def update_preview(self, n: int = 2) -> None:
        """Construct a string of ``n`` mock paths using the current settings and display it in the
        paths_preview QLabel.

        :param n: The number of mock paths to be displayed in the preview. Optional. [default: 2]
        """
        pf = Pathfinder()
        # TODO: allow user to manipulate n
        paths = n * ['dir/subdir/file.ext|layername=lyr|subset=id > 0']
        parsed = [pf.parse_path(path, must_exist=False) for path in paths]
        out = pf.build_string(parsed)
        self.paths_preview.setText(out)

    def restore_defaults(self) -> None:
        """Reset settings to their default values."""
        for k, v in DEFAULTS.items():
            self.settings.setValue(k, v)

        self.restore_settings()
        self.show()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Modify key press events.

        :param event:
        """
        # gobble Enter
        if event.key() == Qt.Key_Enter:
            pass

        # close dialog on Escape
        if event.key() == Qt.Key_Escape:
            self.close()
