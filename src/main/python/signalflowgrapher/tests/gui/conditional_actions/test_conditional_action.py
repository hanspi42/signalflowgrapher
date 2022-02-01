from unittest import TestCase
from unittest.mock import MagicMock
from signalflowgrapher.gui.conditional_actions.conditional_action \
    import ConditionalAction


class TestConditionalAction(TestCase):
    def setUp(self):
        self.conditions = []
        self.control = MagicMock()
        self.action = MagicMock()
        self.activate_action = MagicMock()
        self.deactivate_action = MagicMock()
        self.model_change_handler = MagicMock()
        self.signal = MagicMock()

        self.conditional_action = ConditionalAction(
            self.conditions,
            self.control,
            self.signal,
            self.action,
            self.activate_action,
            self.deactivate_action,
            self.model_change_handler
        )

    def test_is_fulfilled(self):
        c1 = MagicMock()
        c2 = MagicMock()
        c3 = MagicMock()
        c1.is_fulfilled.return_value = True
        c2.is_fulfilled.return_value = True
        c3.is_fulfilled.return_value = False
        self.conditions.append(c1)
        self.conditions.append(c2)
        self.assertTrue(self.conditional_action.is_fulfilled())
        self.conditions.append(c3)
        self.assertFalse(self.conditional_action.is_fulfilled())

    def test_update_selection(self):
        c1 = MagicMock()
        c2 = MagicMock()
        c3 = MagicMock()
        c1.is_fulfilled.return_value = True
        c2.is_fulfilled.return_value = True
        c3.is_fulfilled.return_value = True
        selection = MagicMock()
        self.conditions.append(c1)
        self.conditions.append(c2)
        self.conditions.append(c3)

        self.conditional_action.update_selection(selection)
        c1.update_selection.assert_called_once_with(selection)
        c2.update_selection.assert_called_once_with(selection)
        c3.update_selection.assert_called_once_with(selection)
        self.activate_action.assert_called()
        self.deactivate_action.assert_not_called()

        c1.is_fulfilled.return_value = False
        c2.is_fulfilled.return_value = False
        c3.is_fulfilled.return_value = False
        self.conditional_action.update_selection(selection)
        self.deactivate_action.assert_called_once()

    def test_handle_model_change(self):
        event = MagicMock()
        self.conditional_action.handle_model_change(event)
        self.model_change_handler.assert_called_once_with([], event)
