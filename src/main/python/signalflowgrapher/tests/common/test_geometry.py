from unittest import TestCase
from signalflowgrapher.common.geometry import rotate, move, distance, collinear
import math


class TestGeometry(TestCase):

    def test_full_rotate(self):
        point = (10, 10)
        origin = (0, 0)

        (x, y) = rotate(origin, point, 2 * math.pi)
        self.assertAlmostEqual(x, 10, delta=0.00000001)
        self.assertAlmostEqual(y, 10, delta=0.00000001)

    def test_no_rotate(self):
        point = (10, 10)
        origin = (0, 0)

        (x, y) = rotate(origin, point, 0)
        self.assertAlmostEqual(x, 10, delta=0.00000001)
        self.assertAlmostEqual(y, 10, delta=0.00000001)

    def test_rotate_180(self):
        point = (10, 10)
        origin = (0, 0)

        (x, y) = rotate(origin, point, math.pi)
        self.assertAlmostEqual(x, -10, delta=0.00000001)
        self.assertAlmostEqual(y, -10, delta=0.00000001)

    def test_rotate_90(self):
        point = (10, 10)
        origin = (0, 0)

        (x, y) = rotate(origin, point, 0.5 * math.pi)
        self.assertAlmostEqual(x, -10, delta=0.00000001)
        self.assertAlmostEqual(y, 10, delta=0.00000001)

    def test_rotate_63(self):
        point = (-4, 4)
        origin = (-4, 1.98)

        (x, y) = rotate(origin, point, 0.35 * math.pi)
        self.assertAlmostEqual(x, -5.8, delta=0.01)
        self.assertAlmostEqual(y, 2.9, delta=0.01)

    def test_move_diagonal(self):
        point_1 = (0, 0)
        point_2 = (4, 4)
        distance = math.sqrt(32)
        (x, y) = move(point_1, point_2, distance / 2)
        self.assertAlmostEqual(x, 2, delta=0.00000001)
        self.assertAlmostEqual(y, 2, delta=0.00000001)

        (x, y) = move(point_1, point_2, distance)
        self.assertAlmostEqual(x, 4, delta=0.00000001)
        self.assertAlmostEqual(y, 4, delta=0.00000001)

    def test_move_vertical(self):
        point_1 = (0, 0)
        point_2 = (0, 10)
        (x, y) = move(point_1, point_2, 5)
        self.assertAlmostEqual(x, 0, delta=0.00000001)
        self.assertAlmostEqual(y, 5, delta=0.00000001)

    def test_move_horizontal(self):
        point_1 = (0, 0)
        point_2 = (8, 0)
        (x, y) = move(point_1, point_2, 4)
        self.assertAlmostEqual(x, 4, delta=0.00000001)
        self.assertAlmostEqual(y, 0, delta=0.00000001)

    def test_distance_0(self):
        point_1 = (25, 25)
        point_2 = (25, 25)
        self.assertAlmostEqual(distance(point_1, point_2), 0, delta=0.00000001)

    def test_distance(self):
        point_1 = (25, 25)
        point_2 = (36, 19)
        self.assertAlmostEqual(distance(point_1, point_2),
                               12.52996409,
                               delta=0.00000001)

    def test_distance_negative(self):
        point_1 = (58, 27)
        point_2 = (-9, 0)
        self.assertAlmostEqual(distance(point_1, point_2),
                               72.23572523,
                               delta=0.00000001)

    def test_collinear_one_point(self):
        point_1 = (30, 30)
        self.assertTrue(collinear([point_1]))

    def test_collinear_two_poins(self):
        point_1 = (30, 30)
        point_2 = (8, 22)
        self.assertTrue(collinear([point_1, point_2]))

    def test_collinear_three_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 120)
        self.assertTrue(collinear([point_1, point_2, point_3]))

    def test_not_collinear_three_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 119)
        self.assertFalse(collinear([point_1, point_2, point_3]))

    def test_collinear_four_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 120)
        point_4 = (240, 240)
        self.assertTrue(collinear([point_1, point_2, point_3, point_4]))

    def test_not_collinear_four_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 120)
        point_4 = (240, 239)
        self.assertFalse(collinear([point_1, point_2, point_3, point_4]))

    def test_collinear_five_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 120)
        point_4 = (240, 240)
        point_5 = (480, 480)
        self.assertTrue(collinear([point_1,
                                   point_2,
                                   point_3,
                                   point_4,
                                   point_5]))

    def test_not_collinear_five_poins(self):
        point_1 = (30, 30)
        point_2 = (60, 60)
        point_3 = (120, 120)
        point_4 = (240, 240)
        point_5 = (481, 480)
        self.assertFalse(collinear([point_1,
                                    point_2,
                                    point_3,
                                    point_4,
                                    point_5]))
