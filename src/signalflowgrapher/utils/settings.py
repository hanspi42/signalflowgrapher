from PySide6.QtCore import QSettings

# The mini map is off until the user switches it on
DEFAULT_MINIMAP_VISIBLE = False


class AppSettings:
    """
    Settings of the program that are remembered between two sessions. They
    are not part of a graph and not saved in graph files.
    """

    ORGANIZATION = "signalflowgrapher"
    APPLICATION = "signalflowgrapher"

    def __init__(self, qsettings: QSettings = None):
        # An ini file on every system (not the registry or a plist), in the
        # folder for settings of the user; the folder can be redirected with
        # QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, folder)
        self.__settings = qsettings if qsettings is not None else QSettings(
            QSettings.IniFormat, QSettings.UserScope,
            self.ORGANIZATION, self.APPLICATION)

    def minimap_visible(self) -> bool:
        return self.__settings.value("view/minimap",
                                     DEFAULT_MINIMAP_VISIBLE, type=bool)

    def set_minimap_visible(self, visible: bool):
        self.__settings.setValue("view/minimap", bool(visible))
        self.__settings.sync()
