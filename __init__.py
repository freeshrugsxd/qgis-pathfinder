# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Copy Source Location
 Add layer context menu entries to copy source location or
 to open in file explorer
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
from pathfinder.pathfinder import PathfinderPlugin


def classFactory(iface):  # noqa
    """ Load plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    return PathfinderPlugin(iface)
