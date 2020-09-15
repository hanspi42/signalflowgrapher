from unittest import TestCase
from unittest.mock import MagicMock
from signalflowgrapher.common.observable import ValueObservable


class TestValueObservable(TestCase):
    def test_notify(self):
        mock = MagicMock()

        obs = ValueObservable(10)
        obs.observe(mock.on_change)
        obs.set(20)

        mock.on_change.assert_called_once_with(10, 20)

        # Test with second observer
        mock.reset_mock()
        mock_2 = MagicMock()
        obs.observe(mock_2.on_change_2)
        obs.set(9)
        mock.on_change.assert_called_once_with(20, 9)
        mock_2.on_change_2.assert_called_once_with(20, 9)

    def test_get(self):
        obs = ValueObservable(9)
        self.assertEqual(9, obs.get())
        obs.set(102)
        self.assertEqual(102, obs.get())
