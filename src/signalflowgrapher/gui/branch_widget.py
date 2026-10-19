from PySide6.QtCore import Qt, QPoint, QPointF, QRect, QMargins
from PySide6.QtWidgets import QSizePolicy
from PySide6.QtGui import (
    QPainter, QPainterPath, QPainterPathStroker, QRegion, QCursor, QPen,
    QMouseEvent)
from signalflowgrapher.gui.graph_item import (
    GraphItem, WidgetClickEvent, WidgetEvent)
from signalflowgrapher.model.model import (
    CurvedBranch, PositionedNode, CurvedBranchTransformedEvent,
    PositionedNodeMovedEvent)
import math
from signalflowgrapher.gui.geometry import rotate_pointF, rotate_point
from signalflowgrapher.gui import glyphs
from signalflowgrapher.gui.view_transform import ViewTransform


class BranchWidget(GraphItem):
    def __init__(self,
                 owner: CurvedBranch,
                 view: ViewTransform,
                 *args,
                 ** kwargs):
        super().__init__(*args, **kwargs)
        self.__owner = owner
        self.__view = view
        (self.__start,
         self.__end,
         self.__spline1,
         self.__spline2) = self.__model_points()
        self.__branch = QPainterPath()
        # Everything that is drawn is scaled with the zoom (the dimensions
        # at zoom 100% are in glyphs.py); this is the zoom the widget was
        # built for
        self.__zoom = self.__view.zoom
        self.__arrow_mask = None
        self.__arrow = None
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.updateGeometry()

    def updateGeometry(self):
        zoom = self.__view.zoom
        self.__zoom = zoom

        # Calculate path absolute
        branch_abs = QPainterPath()
        branch_abs.moveTo(self.__start)
        branch_abs.cubicTo(self.__spline1, self.__spline2, self.__end)

        branch_middle = self.__get_bezier_middle(branch_abs)
        middle_angle = self.__get_bezier_middle_angle(branch_abs)

        # Calculate arrow absolute
        arrow_abs = self.__calculate_arrow(
            branch_middle,
            middle_angle,
            glyphs.ARROW_HEIGHT * zoom,
            glyphs.ARROW_LENGTH * zoom,
            glyphs.ARROW_SIDE_SPLINE_DEPTH * zoom,
            glyphs.ARROW_BACK_SPLINE_DEPTH * zoom)

        # Calculate arrow mask absolute. The mask is the area that reacts
        # to the mouse and has space for anti aliasing pixels; it does not
        # get smaller than a minimum.
        mask_height_offset = max(
            glyphs.ARROW_MASK_HEIGHT_OFFSET * zoom,
            glyphs.MIN_ARROW_MASK_HEIGHT_OFFSET)
        mask_length_offset = max(
            glyphs.ARROW_MASK_LENGTH_OFFSET * zoom,
            glyphs.MIN_ARROW_MASK_LENGTH_OFFSET)
        arrow_mask_abs = self.__calculate_arrow(
            branch_middle,
            middle_angle,
            glyphs.ARROW_HEIGHT * zoom + mask_height_offset,
            glyphs.ARROW_LENGTH * zoom + mask_length_offset,
            glyphs.ARROW_SIDE_SPLINE_DEPTH * zoom,
            glyphs.ARROW_BACK_SPLINE_DEPTH * zoom)

        # Add some margin to avoid cutting off anti aliasing pixels of branch
        branch_aliasing_margin = glyphs.branch_aliasing_margin(zoom)
        geo_branch = branch_abs.boundingRect() \
                               .toRect().marginsAdded(QMargins(
                                   branch_aliasing_margin,
                                   branch_aliasing_margin,
                                   branch_aliasing_margin,
                                   branch_aliasing_margin))

        # Get bounding rect of arrow mask
        # The mask already has a margin to avoid cuttin of anti aliasing pixels
        geo_arrow_mask = arrow_mask_abs.boundingRect().toRect()

        # Unite arrow mask bounds and branch bounds and set as geometry
        united = geo_branch.united(geo_arrow_mask)
        self.setGeometry(united)
        super().updateGeometry()

        # Translate absolute paths to relative paths for use in widget
        offset = self.mapFromParent(QPoint())
        path_rel = QPainterPath(branch_abs)
        path_rel.translate(offset)
        self.__branch = path_rel
        # Middle of the curve in widget coordinates; only changes with the
        # shape, so it is computed here and not at every label refresh
        self.__branch_middle = self.__get_bezier_middle(self.__branch)

        arrow_rel = QPainterPath(arrow_abs)
        arrow_rel.translate(offset)
        self.__arrow = arrow_rel

        arrow_mask_rel = QPainterPath(arrow_mask_abs)
        arrow_mask_rel.translate(offset)
        self.__arrow_mask = arrow_mask_rel

        stroker = QPainterPathStroker()
        stroker.setWidth(max(glyphs.BRANCH_HIT_WIDTH * zoom,
                             glyphs.MIN_BRANCH_HIT_WIDTH))
        wide_stroke = stroker.createStroke(self.__branch)
        stroker.setWidth(glyphs.BRANCH_PEN_WIDTH * zoom)
        narrow_stroke = stroker.createStroke(self.__branch)
        branch_outlet = wide_stroke.united(narrow_stroke).toFillPolygon()
        mask_poly_f = self.__arrow_mask.toFillPolygon().united(branch_outlet)

        region = QRegion(mask_poly_f.toPolygon())
        self.setMask(region)
        self.update()

    def __model_points(self):
        """
        The four points of the branch as the widget draws them: start,
        end, spline1, spline2 in the coordinates of the parent widget
        (screen pixels, from the world coordinates of the model).
        """
        owner = self.__owner
        to_screen = self.__view.to_screen_point
        return (to_screen(QPointF(owner.start.x, owner.start.y)),
                to_screen(QPointF(owner.end.x, owner.end.y)),
                to_screen(QPointF(owner.spline1_x, owner.spline1_y)),
                to_screen(QPointF(owner.spline2_x, owner.spline2_y)))

    def refresh(self, force: bool = False):
        """
        Derive the geometry from the model: all four points are read, so
        the result does not depend on which event triggered the refresh.

        If the shape is unchanged and only moved (the whole graph was
        panned) the widget is just moved, which is much cheaper than
        rebuilding paths and masks and gives the identical result.
        """
        new_points = self.__model_points()
        old_points = (self.__start, self.__end,
                      self.__spline1, self.__spline2)
        zoom_changed = self.__zoom != self.__view.zoom
        if not force and not zoom_changed and new_points == old_points:
            return
        delta = new_points[0] - old_points[0]
        only_moved = not zoom_changed and all(
            new - old == delta
            for new, old in zip(new_points, old_points))
        (self.__start,
         self.__end,
         self.__spline1,
         self.__spline2) = new_points
        if only_moved and not force:
            self.move(self.pos() + delta)
        else:
            self.updateGeometry()

    def branch_transformed_event(self,
                                 event: CurvedBranchTransformedEvent):
        """
        Triggered after the splines of a branch have been moved.
        """
        if self.__owner is event.branch:
            self.refresh()

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        """
        Triggered after the node has been moved.
        """
        if self.__owner.start is event.node \
                or self.__owner.end is event.node:
            self.refresh()

    def get_handles(self):
        """
        Create and get the two handle widgets for spline1 and spline2.
        """
        handle1 = Spline1HandleWidget(
            parent=self.parent(),
            branch=self.__owner,
            node=self.__owner.start,
            view=self.__view)
        handle2 = Spline2HandleWidget(
            parent=self.parent(),
            branch=self.__owner,
            node=self.__owner.end,
            view=self.__view)
        return [handle1, handle2]

    def paintEvent(self, QPaintEvent):
        zoom = self.__view.zoom
        pen = QPen()
        pen.setWidthF(glyphs.BRANCH_PEN_WIDTH * zoom)
        if self.selected:
            pen.setColor(self.palette().highlight().color())
        else:
            pen.setColor(self.palette().text().color())

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.drawPath(self.__branch)

        pen.setWidthF(glyphs.BRANCH_ARROW_PEN_WIDTH * zoom)
        painter.setPen(pen)
        if self.selected:
            painter.setBrush(self.palette().highlight())
        else:
            painter.setBrush(self.palette().text())

        painter.drawPath(self.__arrow)
        painter.end()

    def __calculate_arrow(self,
                          branch_middle: QPointF,
                          middle_angle: QPointF,
                          arrow_height: float,
                          arrow_length: float,
                          side_spline_depth: float,
                          back_spline_depth: float) -> QPainterPath:
        """
        Calculate the QPainterPath of an arrow consisting
        of three Bézier curves
        """

        # Calculate the edge positions of the triangle
        head_edge_not_rotated = QPointF(branch_middle.x()
                                        + (arrow_length / 2),
                                        branch_middle.y())

        head_edge = rotate_pointF(branch_middle,
                                  head_edge_not_rotated,
                                  middle_angle)

        top_edge = rotate_pointF(branch_middle,
                                 QPointF(head_edge_not_rotated.x() -
                                         arrow_length,
                                         head_edge_not_rotated.y() -
                                         arrow_height),
                                 middle_angle)
        bottom_edge = rotate_pointF(branch_middle,
                                    QPointF(head_edge_not_rotated.x() -
                                            arrow_length,
                                            head_edge_not_rotated.y() +
                                            arrow_height),
                                    middle_angle)

        # Calculate the angle of the top of the arrow
        arrow_top_angle = math.tanh(arrow_height / arrow_length)

        # Calculate the position of the splines for the sides
        # The splines are positioned at the middle of the sides
        # with a defined right-angled spacing
        arrow_side_length = math.sqrt(math.pow(arrow_length, 2) +
                                      math.pow(arrow_height, 2))
        side_spline_angle = math.tanh(side_spline_depth /
                                      (arrow_side_length / 2))
        side_spline_length = (arrow_side_length / 2) / math.cos(
            side_spline_angle)

        # Rotate point arround heade_edge for reaching the calculated position
        # then rotate it around the arrow angle
        top_spline = rotate_pointF(branch_middle,
                                   rotate_pointF(
                                       head_edge_not_rotated,
                                       QPointF(head_edge_not_rotated.x()
                                               - side_spline_length,
                                               head_edge_not_rotated.y()),
                                       arrow_top_angle -
                                       side_spline_angle),
                                   middle_angle)

        bottom_spline = rotate_pointF(branch_middle,
                                      rotate_pointF(
                                          head_edge_not_rotated,
                                          QPointF(head_edge_not_rotated.x()
                                                  - side_spline_length,
                                                  head_edge_not_rotated.y()),
                                          -(arrow_top_angle -
                                            side_spline_angle)),
                                      middle_angle)

        back_spline = rotate_pointF(branch_middle,
                                    QPointF(head_edge_not_rotated.x() -
                                            arrow_length + back_spline_depth,
                                            head_edge_not_rotated.y()),
                                    middle_angle)

        # Build path for drawing arrow
        arrow = QPainterPath()
        arrow.moveTo(head_edge)
        arrow.cubicTo(top_spline,
                      top_spline,
                      top_edge)
        arrow.cubicTo(back_spline,
                      back_spline,
                      bottom_edge)
        arrow.cubicTo(bottom_spline,
                      bottom_spline,
                      head_edge)

        return arrow

    def get_branch_middle(self) -> QPointF:
        """
        Get the point in the middle of the branch bezier curve
        """
        translate = self.mapToParent(QPoint())
        return self.__branch_middle + translate

    def __get_bezier_middle(self, bezier: QPainterPath) -> QPointF:
        """
        Get the point in the middle of a bezier curve.
        """
        percent_middle = bezier.percentAtLength(
            bezier.length() / 2)
        return bezier.pointAtPercent(percent_middle)

    def get_branch_middle_angle(self) -> float:
        """
        Get the angle in the middle of the branch bezier curve.
        """
        return self.__get_bezier_middle_angle(self.__branch)

    def __get_bezier_middle_angle(self, bezier: QPainterPath):
        """
        Get the angle in the middle of a bezier curve.
        """
        percent_middle = bezier.percentAtLength(
            bezier.length() / 2)
        return -math.radians(
            bezier.angleAtPercent(percent_middle))

    def get_center(self) -> QPointF:
        """
        Get the center of the branch widget.
        This is the middle of the branch not the real widget middle.
        """
        return self.get_branch_middle()

    def __get_handle_pos(self, origin, spline, width, height):
        p = QPoint(int(origin.x() - (spline.x() - origin.x()) - (width / 2)),
                   int(origin.y() - (spline.y() - origin.y()) - (height / 2)))
        return p

    def mouseMoveEvent(self, event: QMouseEvent):
        # Stop propagation of move event on branch
        # because the branch cant be moved
        pass


class SplineHandleWidgetPressEvent(WidgetClickEvent):
    """
    Occurs after mouse press on spline handle widget.
    """

    def __init__(self, widget, mouse_event, *args, **kwargs):
        super().__init__(widget, mouse_event.globalPosition().toPoint(), mouse_event,
                         *args, **kwargs)


class SplineHandleWidgetReleaseEvent(WidgetClickEvent):
    """
    Occurs after mouse release on spline handle widget.
    """

    def __init__(self, widget, mouse_press, mouse_event, *args, **kwargs):
        super().__init__(widget, mouse_press, mouse_event, *args, **kwargs)


class SplineHandleWidgetMoveEvent(WidgetEvent):
    """
    Occurs after spline handle widget moved.
    """

    def __init__(self, widget, dx, dy):
        super().__init__(widget)
        self.dx = dx
        self.dy = dy


class SplineHandleWidget(GraphItem):
    def __init__(self, *args,
                 branch: CurvedBranch, node: PositionedNode,
                 view: ViewTransform,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.__branch = branch
        self.__node = node
        self.__view = view
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._origin_abs = self._model_origin()
        self._spline_abs = self._model_spline()
        self._origin_ = None
        self._spline_ = None
        self.__handle_pos = None
        # Everything that is drawn is scaled with the zoom (the dimensions
        # at zoom 100% are in glyphs.py)
        self.__zoom = self.__view.zoom
        self.updateGeometry()

    def updateGeometry(self):
        zoom = self.__view.zoom
        self.__zoom = zoom

        # Get absolute position of handle by spline
        __handle_pos_abs = rotate_point(
            self._origin_abs,
            self._spline_abs,
            math.radians(180))

        # Calculate bounding rect including circle and line. The circle
        # area also is the area that reacts to the mouse; it does not get
        # smaller than a minimum.
        rect = QRect(self._origin_abs, __handle_pos_abs).normalized()  # Line
        hit_radius = glyphs.handle_hit_radius(zoom)
        circle_offset = QPoint(hit_radius, hit_radius)
        circle_rect = QRect(__handle_pos_abs - circle_offset,  # Circle
                            __handle_pos_abs + circle_offset).normalized()

        self.setGeometry(rect.united(circle_rect))

        self.__handle_pos = self.mapFromParent(__handle_pos_abs)
        self._origin = self.mapFromParent(self._origin_abs)
        self._spline = self.mapFromParent(self._spline_abs)

        # Create line
        self.line_path = QPainterPath()
        self.line_path.moveTo(self.__handle_pos)
        self.line_path.lineTo(self._origin)

        # Create and set mask
        circle_mask_rect = QRect(__handle_pos_abs - circle_offset,  # Circle
                                 __handle_pos_abs + circle_offset).normalized()
        circle_region = QRegion(circle_mask_rect, QRegion.Ellipse)
        offset = self.mapFromParent(QPoint())
        circle_region.translate(offset)

        # Create stroke to give space for anti aliasing pixels of line
        stroker = QPainterPathStroker()
        stroker.setWidth(max(glyphs.HANDLE_LINE_HIT_WIDTH * zoom,
                             glyphs.MIN_HANDLE_LINE_HIT_WIDTH))
        line_stroke = stroker.createStroke(self.line_path)

        mask = circle_region.united(
            QRegion(line_stroke.toFillPolygon().toPolygon()))
        self.setMask(mask)
        super().updateGeometry()

    def get_branch(self):
        return self.__branch

    def get_center(self) -> QPointF:
        return rotate_point(
            self._origin_abs,
            self._spline_abs,
            math.radians(180))

    def get_world_center(self) -> QPointF:
        """
        Position of the knob in world coordinates: the spline point
        mirrored at the node, from the model (whole units, like the
        drawing).
        """
        origin = QPoint(int(self.__node.x), int(self.__node.y))
        spline_x, spline_y = self._model_spline_world()
        return rotate_point(origin, QPoint(int(spline_x), int(spline_y)),
                            math.radians(180))

    def get_node(self):
        return self.__node

    def _model_origin(self) -> QPoint:
        """The node the handle belongs to, as the widget draws it."""
        return self.__view.to_screen_point(
            QPointF(self.__node.x, self.__node.y))

    def _model_spline_world(self):
        """World coordinates (x, y) of the spline point of the handle."""
        raise NotImplementedError

    def _model_spline(self) -> QPoint:
        """The spline control point the handle controls, as drawn."""
        x, y = self._model_spline_world()
        return self.__view.to_screen_point(QPointF(x, y))

    def refresh(self, force: bool = False):
        """
        Derive node and spline position from the model.
        """
        origin = self._model_origin()
        spline = self._model_spline()
        if (force or self.__zoom != self.__view.zoom
                or origin != self._origin_abs or spline != self._spline_abs):
            self._origin_abs = origin
            self._spline_abs = spline
            self.updateGeometry()

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        if self.get_node() is event.node:
            self.refresh()

    def branch_transformed_event(self, event: CurvedBranchTransformedEvent):
        if self.get_branch() is event.branch:
            self.refresh()

    def paintEvent(self, QPaintEvent):
        zoom = self.__view.zoom
        pen = QPen()
        pen.setColor(self.palette().text().color())
        pen.setWidthF(glyphs.HANDLE_CIRCLE_WIDTH * zoom)
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)

        # Paint line to origin
        painter.drawPath(self.line_path)

        # Paint circle
        radius = glyphs.HANDLE_RADIUS * zoom
        painter.setBrush(self.palette().window())
        painter.drawEllipse(QPointF(self.__handle_pos), radius, radius)
        painter.end()

    def mousePressEvent(self, event):
        super(SplineHandleWidget, self).mousePressEvent(event, False)
        super()._notify(
            SplineHandleWidgetPressEvent(self, event))

    def mouseMoveEvent(self, event: QMouseEvent):
        # Move is only triggered with left mouse button pressed
        if event.buttons() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            global_position = event.globalPosition().toPoint()
            diff = global_position - self._mouse_move_pos

            self._notify(
                SplineHandleWidgetMoveEvent(
                    self,
                    diff.x(),
                    diff.y()))
            self._mouse_move_pos = global_position

    def mouseReleaseEvent(self, event: QMouseEvent):
        super()._notify(
            SplineHandleWidgetReleaseEvent(self,
                                           self._mouse_press_pos, event))
        super(SplineHandleWidget, self).mouseReleaseEvent(event)


class Spline1HandleWidget(SplineHandleWidget):
    """
    Spline handle widget for spline1 of branch widget.
    """

    def _model_spline_world(self):
        branch = self.get_branch()
        return branch.spline1_x, branch.spline1_y


class Spline2HandleWidget(SplineHandleWidget):
    """
    Spline handle widget for spline2 of branch widget.
    """

    def _model_spline_world(self):
        branch = self.get_branch()
        return branch.spline2_x, branch.spline2_y
