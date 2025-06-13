from pathlib import Path

from qgis.PyQt.QtGui import QIcon

icon_dir = Path(__file__).parent
icon_copy_path = QIcon(str(Path(icon_dir / 'copy.svg')))
icon_open_in_explorer = QIcon(str(Path(icon_dir / 'open_in_explorer.svg')))

__all__ = ['icon_copy_path', 'icon_open_in_explorer']
