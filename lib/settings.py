from qgis.core import QgsSettingsEntryBool, QgsSettingsEntryInteger, QgsSettingsEntryString, QgsSettingsTree

from pathfinder.lib.i18n import tr

class Settings:
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            settings_node = QgsSettingsTree.createPluginTreeNode(pluginName='pathfinder')

            cls.quote_char = QgsSettingsEntryString(name='quote_char', parent=settings_node, defaultValue='"', description='The character surrounding individual paths.')
            cls.separ_char = QgsSettingsEntryString(name='separ_char', parent=settings_node, defaultValue=tr('Space'), description='The character separating multiple paths.')

            cls.quote_char_custom = QgsSettingsEntryString(name='quote_char_custom', parent=settings_node, defaultValue='', description='The character surrounding individual paths.')
            cls.separ_char_custom = QgsSettingsEntryString(name='separ_char_custom', parent=settings_node, defaultValue='', description='The character separating multiple paths.')
            cls.prefix = QgsSettingsEntryString(name='prefix', parent=settings_node, defaultValue='', description='Prefix character/s prepended to paths.')
            cls.postfix = QgsSettingsEntryString(name='postfix', parent=settings_node, defaultValue='', description='Postfix character/s appended to paths.')
            cls.single_path_quote = QgsSettingsEntryBool(name='single_path_quote', parent=settings_node, defaultValue=False, description='Whether to use quoting when only a single path is returned.')
            cls.single_path_affix = QgsSettingsEntryBool(name='single_path_affix', parent=settings_node, defaultValue=False, description='Whether to apply prefix and postfix characters when only a single path is returned.')
            cls.incl_file_name = QgsSettingsEntryBool(name='incl_file_name', parent=settings_node, defaultValue=True, description='Whether to include the file name.')
            cls.incl_layer_name = QgsSettingsEntryBool(name='incl_layer_name', parent=settings_node, defaultValue=False, description='Whether to append the layer name part to the path. Useful for file formats that can containing multiple layers.')
            cls.incl_subset_str = QgsSettingsEntryBool(name='incl_subset_str', parent=settings_node, defaultValue=False, description='Whether to append the subset string to the vector layer path. Useful to retain information about applied filter expressions.')
            cls.show_notification = QgsSettingsEntryBool(name='show_notification', parent=settings_node, defaultValue=False, description='Whether to show a notification on successful operations.')
            cls.paths_on_new_line = QgsSettingsEntryBool(name='paths_on_new_line', parent=settings_node, defaultValue=False, description='Whether to place each path on a separate line.')
            cls.original_vrt_ds = QgsSettingsEntryBool(name='original_vrt_ds', parent=settings_node, defaultValue=False, description='Whether to return the path to the underlying data source of an OGR VRT dataset (e.g. the source XLSX Excel file of a spreadsheet layer) instead of the path to the VRT file.')
            cls.notify_duration = QgsSettingsEntryInteger(name='notify_duration', parent=settings_node, defaultValue=5, description='Amount of time in seconds to display the notification for.')
            cls.settings_node = settings_node
        return cls.instance

    @staticmethod
    def unregister():
        QgsSettingsTree.unregisterPluginTreeNode(pluginName='pathfinder')
