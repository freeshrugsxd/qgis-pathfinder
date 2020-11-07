"""
LayerTreeContextMenuManager
--
Utility class to extend the default layer tree context menu

It patches the default menuProvider (if not already patched by another plugin) and
provides an addProvider method. Providers added via this method will be removed
when the LayerTreeContextMenuManager is deleted

Example usage (adds a useless "Print Clicked" action to the context menu):

```
def foo(menu):
    menu.addAction("Print clicked").triggered.connect(lambda: print("Clicked"))

contextMenuManager = LayerTreeContextMenuManager()
contextMenuManager.addProvider(foo)
```

The provider can be any python callable that takes a QMenu and modifies it

Here's a small example that adds opacity controls in the context menu

```
from functools import partial

class OpacityMenuProvider:
    def __init__(self):
        self.view = iface.layerTreeView()

    def __call__(self, menu):
        if QgsLayerTree.isLayer(self.view.currentNode()):
            menu.addSeparator()
            for opacity in [25, 50, 75, 100]:
                action = QAction(f"Set opacity {opacity}%", menu)
                menu.addAction(action)
                action.triggered.connect(partial(self.set_opacity, opacity/100))

    def set_opacity(self, value):
        layer = self.view.currentNode().layer()
        try:
            layer.setOpacity(value)
        except AttributeError:
            layer.renderer().setOpacity(value)
        layer.triggerRepaint()


contextMenuManager = LayerTreeContextMenuManager()
contextMenuManager.addProvider(OpacityMenuProvider())
```

"""
from PyQt5.QtCore import QObject, QEvent
from qgis.utils import iface


def createContextMenu(event):
    """Patched version of createContextMenu

    Args:
        event (QEvent): event which triggered the context menu (QEvent.ContextMenu)
            forwarded to keep track of the modifiers

    Returns:
        QMenu: context menu
    """
    menu = iface.layerTreeView().menuProvider()._original()
    for provider in iface.layerTreeView().menuProvider().providers:

        # Accept two providers signatures
        try:
            provider(menu, event)
        except TypeError:
            provider(menu)
    return menu


class LayerTreeContextMenuManager(QObject):
    """ Installed as an event filter on the QGIS layer tree
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = iface.layerTreeView()
        self.menuProvider = self.view.menuProvider()

        # List of custom providers intalled by this plugin
        self.providers = []

        # Patch the menuProvider
        self.patch()

        # Install itself as an eventFilter on the view
        self.view.viewport().installEventFilter(self)

    def patch(self):

        # Patch the default menuProvider
        # Keep a reference to the old one
        if not hasattr(self.menuProvider, "_original"):
            self.menuProvider._original = self.menuProvider.createContextMenu
        if not hasattr(self.menuProvider, "providers"):
            self.menuProvider.providers = []

        self.menuProvider.createContextMenu = createContextMenu

    def eventFilter(self, obj, event):
        """ Allow to call the patched createContextMenu (otherwise, the original c++
        version is called) """
        if event.type() == QEvent.ContextMenu:
            menu = self.menuProvider.createContextMenu(event)
            menu.exec(self.view.mapToGlobal(event.pos()))
            return True
        return False

    def addProvider(self, provider):
        if not callable(provider):
            return
        if provider in self.menuProvider.providers:
            return
        self.providers.append(provider)
        self.menuProvider.providers.append(provider)

    def removeProvider(self, provider):
        try:
            self.menuProvider.providers.remove(provider)
        except ValueError:
            pass

    def __del__(self):
        for provider in self.providers:
            self.removeProvider(provider)
        self.view.viewport().removeEventFilter(self)
