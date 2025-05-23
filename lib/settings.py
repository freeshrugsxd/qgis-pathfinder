from qgis.core import QgsSettingsEntryBool, QgsSettingsEntryInteger, QgsSettingsEntryString, QgsSettingsTree

from pathfinder.lib.i18n import tr

class Settings:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            settings_node = QgsSettingsTree.createPluginTreeNode(pluginName='pathfinder')

            cls.quote_char = QgsSettingsEntryString('quote_char', settings_node, '"')
            cls.separ_char = QgsSettingsEntryString('separ_char', settings_node, tr('Space'))
            cls.quote_char_custom = QgsSettingsEntryString('quote_char_custom', settings_node, '')
            cls.separ_char_custom = QgsSettingsEntryString('separ_char_custom', settings_node, '')
            cls.prefix = QgsSettingsEntryString('prefix', settings_node, '')
            cls.postfix = QgsSettingsEntryString('postfix', settings_node, '')
            cls.single_path_quote = QgsSettingsEntryBool('single_path_quote', settings_node, False)
            cls.single_path_affix = QgsSettingsEntryBool('single_path_affix', settings_node, False)
            cls.incl_file_name = QgsSettingsEntryBool('incl_file_name', settings_node, False)
            cls.incl_layer_name = QgsSettingsEntryBool('incl_layer_name', settings_node, True)
            cls.incl_subset_str = QgsSettingsEntryBool('incl_subset_str', settings_node, False)
            cls.show_notification = QgsSettingsEntryBool('show_notification', settings_node, False)
            cls.paths_on_new_line = QgsSettingsEntryBool('paths_on_new_line', settings_node, False)
            cls.original_vrt_ds = QgsSettingsEntryBool('original_vrt_ds', settings_node, False)
            cls.notify_duration = QgsSettingsEntryInteger('notify_duration', settings_node, 5)
            cls.settings_node = settings_node
        return cls.instance

    @staticmethod
    def unregister():
        QgsSettingsTree.unregisterPluginTreeNode(pluginName='pathfinder')
