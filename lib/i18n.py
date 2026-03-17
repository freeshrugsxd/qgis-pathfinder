from qgis.PyQt.QtCore import QCoreApplication


def tr(text, context='@default'):
    return QCoreApplication.translate(context, text)
