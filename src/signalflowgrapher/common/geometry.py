import math


# taken from:
# https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
def rotate(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox = origin[0]
    oy = origin[1]
    px = point[0]
    py = point[1]

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy


def move(point_1, point_2, delta):
    """
    Move a point delta pixel from point_1 towards point_2
    """
    vector_x = point_2[0] - point_1[0]
    vector_y = point_2[1] - point_1[1]
    length = math.sqrt(math.pow(abs(vector_x), 2) + math.pow(abs(vector_y), 2))
    if length == 0:
        raise ValueError(
            "Unable to calculate angle. Given points have same position.")
    norm_x = vector_x / length
    norm_y = vector_y / length
    return point_1[0] + delta * norm_x, point_1[1] + delta * norm_y


def distance(point_1, point_2):
    """
    Calculate the distance between two points
    """
    vector_x = point_2[0] - point_1[0]
    vector_y = point_2[1] - point_1[1]
    return math.sqrt(math.pow(abs(vector_x), 2) + math.pow(abs(vector_y), 2))


def collinear(points):
    """
    Returns true, if the given points are all collinear
    which means, they are on the same line.

    If the function is called with less than 3 points, it will
    always return true.
    """
    if (len(points) < 3):
        return True

    if (len(points) == 3):
        return (points[1][1] - points[0][1]) * (points[2][0] - points[1][0]) \
            == (points[2][1] - points[1][1]) * (points[1][0] - points[0][0])

    # loop
    for i in range(len(points) - 2):
        if (not collinear(points[i:i+3])):
            return False

    return True
