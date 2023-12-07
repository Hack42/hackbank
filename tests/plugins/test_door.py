from unittest import TestCase
from unittest.mock import patch, MagicMock
from plugins.door import door

class TestDoor(TestCase):
    def setUp(self):
        self.master_mock = MagicMock()
        self.door_instance = door("SID", self.master_mock)

    def test_help(self):
        with patch('builtins.print') as mock_print:
            result = self.door_instance.help()
            mock_print.assert_called_with("Help")
            self.assertEqual(result, {"dooropen": "Door open"})

    def test_input_dooropen(self):
        with patch('paho.mqtt.client.Client') as mock_client:
            client_instance = mock_client.return_value
            self.assertTrue(self.door_instance.input("dooropen"))
            client_instance.connect.assert_called_with("mqtt.space.hack42.nl", 1883, 60)
            client_instance.publish.assert_any_call("hack42/brandhok/deuropen", "closed", 1, True)
            client_instance.publish.assert_any_call("hack42/brandhok/deuropen", "open", 1, True)
            client_instance.disconnect.assert_called()

    def test_input_invalid_command(self):
        self.assertIsNone(self.door_instance.input("invalid_command"))

    def test_startup(self):
        self.door_instance.startup()  # Just to cover startup if no action is required


