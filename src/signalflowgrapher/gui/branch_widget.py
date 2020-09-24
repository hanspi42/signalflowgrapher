from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPainterPath, QRegion, QCursor
from PyQt5.Qt import QColor, QMouseEvent, QPainterPathStroker, \
    QPen, QPoint, QPointF, QSizePolicy, QMargins, QRect
from signalflowgrapher.gui.graph_item \
    import GraphItem, WidgetClickEvent, WidgetEvent
from signalflowgrapher.model.model import CurvedBranch, PositionedNode, \
    CurvedBranchTransformedEvent, PositionedNodeMovedEvent, GraphMovedEvent
import math
from signalflowgrapher.gui.geometry import rotate_pointF, rotate_point


class BranchWidget(GraphItem):
    def __init__(self,
                 owner: CurvedBranch,
                 spline1: QPoint,
                 spline2: QPoint,
                 *args,
                 ** kwargs):
        super().__init__(*args, **kwargs)
        self.__owner = owner
        self.__start = QPoint(owner.start.x,
                              owner.start.y)
        self.__end = QPoint(owner.end.x,
                            owner.end.y)
        self.__spline1 = spline1
        self.__spline2 = spline2
        self.__branch = QPainterPath()
        self.__pen_width = 3
        # The arrow has the form of a triangle
        # Half of the width of the arrow (at the back)
        self.__arrow_height = 9
        # Length of the arrow from top to back
        self.__arrow_length = 27
        # The triangle is drawn with 3 bezier curves
        # These numbers determine the bend of the curves
        self.__arrow_side_spline_depth = 2
        self.__arrow_back_spline_depth = 5.5
        # Antialiasing offsets for arrow mask
        self.__arrow_mask_length_offset = 8
        self.__arrow_mask_height_offset = 5
        self.__arrow_mask = None
        self.__arrow = None
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.updateGeometry()

    def updateGeometry(self):
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
            self.__arrow_height,
            self.__arrow_length,
            self.__arrow_side_spline_depth,
            self.__arrow_back_spline_depth)

        # Calculate arrow mask absolute
        arrow_mask_abs = self.__calculate_arrow(
            branch_middle,
            middle_angle,
            self.__arrow_height + self.__arrow_mask_height_offset,
            self.__arrow_length + self.__arrow_mask_length_offset,
            self.__arrow_side_spline_depth,
            self.__arrow_back_spline_depth)

        # Add some margin to avoid cutting off anti aliasing pixels of branch
        branch_aliasing_margin = 4
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

        arrow_rel = QPainterPath(arrow_abs)
        arrow_rel.translate(offset)
        self.__arrow = arrow_rel

        arrow_mask_rel = QPainterPath(arrow_mask_abs)
        arrow_mask_rel.translate(offset)
        self.__arrow_mask = arrow_mask_rel

        stroker = QPainterPathStroker()
        stroker.setWidth(8)
        wide_stroke = stroker.createStroke(self.__branch)
        stroker.setWidth(self.__pen_width)
        narrow_stroke = stroker.createStroke(self.__branch)
        branch_outlet = wide_stroke.united(narrow_stroke).toFillPolygon()
        mask_poly_f = self.__arrow_mask.toFillPolygon().united(branch_outlet)

        region = QRegion(mask_poly_f.toPolygon())
        self.setMask(region)
        self.update()

    def branch_transformed_event(self,
                                 event: CurvedBranchTransformedEvent):
        """
        Triggered after the splines of a branch have been moved.
        Updates the geometry of the widget if necessary.
        """
        if self.__owner is event.branch:
            update_geo = False
            spline1_new = QPoint(event.branch.spline1_x,
                                 event.branch.spline1_y)

            spline2_new = QPoint(event.branch.spline2_x,
                                 event.branch.spline2_y)

            if not self.__spline1 == spline1_new:
                self.__spline1 = spline1_new
                update_geo = True

            if not self.__spline2 == spline2_new:
                self.__spline2 = spline2_new
                update_geo = True

            if update_geo:
                self.updateGeometry()

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        """
        Triggered after the node has been moved.
        Updates the geometry of the widget if necessary.
        """
        if self.__owner.start is event.node:
            self.__start = QPoint(event.node.x,
                                  event.node.y)
            self.updateGeometry()
        if self.__owner.end is event.node:
            self.__end = QPoint(event.node.x,
                                event.node.y)
            self.updateGeometry()

    def graph_moved_event(self, event: GraphMovedEvent):
        """
        Triggered after the whole graph has been moved.
        Does not change the geometry but mvoes the widget.
        """
        self.__start = QPoint(self.__owner.start.x,
                              self.__owner.start.y)
        self.__end = QPoint(self.__owner.end.x,
                            self.__owner.end.y)
        self.__spline1 = QPoint(self.__owner.spline1_x,
                                self.__owner.spline1_y)
        self.__spline2 = QPoint(self.__owner.spline2_x,
                                self.__owner.spline2_y)
        super().graph_moved_event(event)

    def get_handles(self):
        """
        Create and get the two handle widgets for spline1 and spline2.
        """
        handle1 = Spline1HandleWidget(
            parent=self.parent(),
            branch=self.__owner,
            node=self.__owner.start,
            origin=self.__start,
            spline=self.__spline1)
        handle2 = Spline2HandleWidget(
            parent=self.parent(),
            node=self.__owner.end,
            branch=self.__owner,
            origin=self.__end,
            spline=self.__spline2)
        return [handle1, handle2]

    def paintEvent(self, QPaintEvent):
        pen_color = QColor()
        if self.selected:
            pen_color.setNamedColor("blue")
        else:
            pen_color.setNamedColor("black")

        pen = QPen()
        pen.setWidth(self.__pen_width)
        pen.setColor(pen_color)

        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)
        painter.drawPath(self.__branch)

        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(pen_color)  # Use same color as pen for brush

        painter.drawPath(self.__arrow)
        painter.end()

    def __calculate_arrow(self,
                          branch_middle: QPointF,
                          middle_angle: QPointF,
                          arrow_height: int,
                          arrow_length: int,
                          side_spline_depth: int,
                          back_spline_depth: int) -> QPainterPath:
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
        return self.__get_bezier_middle(self.__branch) + translate

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
        p = QPoint(origin.x() - (spline.x() - origin.x()) - (width / 2),
                   origin.y() - (spline.y() - origin.y()) - (height / 2))
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
        super().__init__(widget, mouse_event.globalPos(), mouse_event,
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
                 origin: QPoint, spline: QPoint,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.__branch = branch
        self.__node = node
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._origin_abs = origin
        self._spline_abs = spline
        self._origin_ = None
        self._spline_ = None
        self.__radius = 5
        self.__circle_width = 2
        self.__handle_pos = None
        self.updateGeometry()

    def updateGeometry(self):
        # Get absolute position of handle by spline
        __handle_pos_abs = rotate_point(
            self._origin_abs,
            self._spline_abs,
            math.radians(180))

        # Calculate bounding rect including circle and line
        rect = QRect(self._origin_abs, __handle_pos_abs).normalized()  # Line
        circle_offset = QPoint(self.__circle_width + self.__radius,
                               self.__circle_width + self.__radius)
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
        stroker.setWidth(4)
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

    def get_node(self):
        return self.__node

    def set_origin(self, origin):
        self._origin = origin

    def node_moved_event(self, event: PositionedNodeMovedEvent):
        if self.get_node() is event.node:
            new_origin = QPoint(event.node.x,
                                event.node.y)
            if not self._origin == new_origin:
                self._origin_abs = new_origin
                self.updateGeometry()

    def graph_moved_event(self, event: GraphMovedEvent):
        self._origin_abs = QPoint(
            self.__node.x,
            self.__node.y)
        super().graph_moved_event(event)

    def paintEvent(self, QPaintEvent):
        pen = QPen()
        pen.setWidth(self.__circle_width)
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(pen)

        # Paint line to origin
        painter.drawPath(self.line_path)

        # Paint circle
        q = QColor(Qt.white)
        painter.setBrush(q)
        painter.drawEllipse(self.__handle_pos, self.__radius, self.__radius)
        painter.end()

    def mousePressEvent(self, event):
        super(SplineHandleWidget, self).mousePressEvent(event, False)
        super()._notify(
            SplineHandleWidgetPressEvent(self, event))

    def mouseMoveEvent(self, event: QMouseEvent):
        # Move is only triggered with left mouse button pressed
        if event.buttons() == Qt.LeftButton:
            self.setCursor(QCursor(Qt.ClosedHandCursor))
            global_position = event.globalPos()
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def branch_transformed_event(self, event: CurvedBranchTransformedEvent):
        """
        Triggered after branch has been transformed.
        Makes sure the spline positions is udpated accordingly.
        """
        if self.get_branch() is event.branch:
            new_spline1 = QPoint(event.branch.spline1_x,
                                 event.branch.spline1_y)
            if not self._spline_abs == new_spline1:
                self._spline_abs = new_spline1
                self.updateGeometry()

    def graph_moved_event(self, event: GraphMovedEvent):
        """
        Triggered after whole graph has moved.
        Makes sure the absolute spline position is updated accordingly.
        """
        self._spline_abs = QPoint(self.get_branch().spline1_x,
                                  self.get_branch().spline1_y)
        super().graph_moved_event(event)


class Spline2HandleWidget(SplineHandleWidget):
    """
    Spline handle widget for spline2 of branch widget.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def branch_transformed_event(self, event: CurvedBranchTransformedEvent):
        """
        Triggered after branch has been transformed.
        Makes sure the spline positions is udpated accordingly.
        """
        if self.get_branch() is event.branch:
            new_spline2 = QPoint(event.branch.spline2_x,
                                 event.branch.spline2_y)
            if not self._spline_abs == new_spline2:
                self._spline_abs = new_spline2
                self.updateGeometry()

    def graph_moved_event(self, event: GraphMovedEvent):
        """
        Triggered after whole graph has moved.
        Makes sure the absolute spline position is updated accordingly.
        """
        self._spline_abs = QPoint(self.get_branch().spline2_x,
                                  self.get_branch().spline2_y)
        super().graph_moved_event(event)
