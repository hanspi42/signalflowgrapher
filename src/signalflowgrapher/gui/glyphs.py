"""
Dimensions of everything that is drawn, at zoom 100%.

All of them are multiplied by the zoom when drawn, so that the relation
between node size, line widths, arrows and text is the same at every zoom,
as it is in the TikZ output. The sizes are pixels at zoom 100%.

Things that are for the mouse and not for the eye (the area in which a
click hits a node, a branch or a handle) do not get smaller than the
minimum sizes at the end, so that everything can still be grabbed when the
whole graph is zoomed out.
"""
import math

# ---- node
NODE_RADIUS = 8
NODE_CIRCLE_WIDTH = 3
# Half of the width of the node widget: radius and line width
NODE_HALF_SIZE = NODE_RADIUS + NODE_CIRCLE_WIDTH

# ---- branch
BRANCH_PEN_WIDTH = 3
BRANCH_ARROW_PEN_WIDTH = 1
# The arrow has the form of a triangle. Half of the width of the arrow
# (at the back):
ARROW_HEIGHT = 9
# Length of the arrow from top to back:
ARROW_LENGTH = 27
# The triangle is drawn with 3 bezier curves. These numbers determine the
# bend of the curves:
ARROW_SIDE_SPLINE_DEPTH = 2
ARROW_BACK_SPLINE_DEPTH = 5.5
# Space around the arrow for the click area (also anti aliasing pixels)
ARROW_MASK_LENGTH_OFFSET = 8
ARROW_MASK_HEIGHT_OFFSET = 5
# Space around the branch that is kept in the widget for anti aliasing
BRANCH_ALIASING_MARGIN = 4
# Width of the click area around the curve
BRANCH_HIT_WIDTH = 8

# ---- spline handle
HANDLE_RADIUS = 5
HANDLE_CIRCLE_WIDTH = 2
# Width of the click area around the line from the node to the handle
HANDLE_LINE_HIT_WIDTH = 4

# ---- label
LABEL_FONT_POINTS = 13

# ---- minimum sizes of click areas, in pixels on the screen
MIN_NODE_HIT_RADIUS = 5
MIN_BRANCH_HIT_WIDTH = 6
MIN_ARROW_MASK_LENGTH_OFFSET = 4
MIN_ARROW_MASK_HEIGHT_OFFSET = 3
MIN_HANDLE_HIT_RADIUS = 5
MIN_HANDLE_LINE_HIT_WIDTH = 4

# ---- grid lines that are closer than this are not drawn (they would only
# be a grey area)
MIN_VISIBLE_GRID_SPACING = 6


def node_half_size(zoom: float) -> int:
    """
    Half of the width of the node widget in pixels. The widget has an even
    size so that its centre is on a pixel. It is as big as the drawn node,
    but not smaller than the click area minimum.
    """
    return max(math.ceil(NODE_HALF_SIZE * zoom - 1e-9), MIN_NODE_HIT_RADIUS)


def handle_hit_radius(zoom: float) -> int:
    """Radius of the click area (and widget size) of the handle knob."""
    return max(math.ceil((HANDLE_RADIUS + HANDLE_CIRCLE_WIDTH) * zoom - 1e-9),
               MIN_HANDLE_HIT_RADIUS)


def branch_aliasing_margin(zoom: float) -> int:
    return max(math.ceil(BRANCH_ALIASING_MARGIN * zoom - 1e-9), 2)
