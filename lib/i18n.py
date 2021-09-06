from qgis.PyQt.QtWidgets import QApplication


def tr(text, context='@default'):
    return QApplication.translate(context, text)
