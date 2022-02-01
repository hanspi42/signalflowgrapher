from PyQt5.QtCore import QPoint, QPointF
from signalflowgrapher.common.geometry import rotate


def rotate_point(origin: QPoint, point: QPoint, angle: QPoint):
    """
    Rotate point around origin by the angle.
    """
    [x, y] = rotate(
        [origin.x(), origin.y()],
        [point.x(), point.y()],
        angle)
    return QPoint(int(x), int(y))


def rotate_pointF(origin: QPointF, point: QPointF, angle: QPointF):
    """
    Rotate point around origin by the angle.
    """
    [x, y] = rotate(
        [origin.x(), origin.y()],
        [point.x(), point.y()],
        angle)
    return QPointF(x, y)
