from pathfinder.pathfinder import PathfinderPlugin


def classFactory(iface):
    """Load plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    return PathfinderPlugin(iface)
