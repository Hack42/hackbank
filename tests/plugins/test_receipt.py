from unittest import TestCase
from unittest.mock import patch, Mock
import json
from plugins.receipt import receipt


class TestReceipt(TestCase):
    def setUp(self):
        self.master_mock = Mock()
        self.receipt_instance = receipt("SID", self.master_mock)

    def test_is_empty_with_empty_receipt(self):
        self.receipt_instance.receipt = []
        self.assertTrue(self.receipt_instance.is_empty())

    def test_is_empty_with_non_empty_receipt(self):
        self.receipt_instance.receipt = []
        self.receipt_instance.receipt.append({})
        self.assertFalse(self.receipt_instance.is_empty())

    def test_updatetotals(self):
        self.receipt_instance.receipt = [
            {"beni": "user1", "count": 2, "value": 5.0, "Lose": True}
        ]
        with patch.object(self.receipt_instance.master, "send_message"):
            self.receipt_instance.updatetotals()
            self.assertEqual(self.receipt_instance.totals, {"user1": -10.0})

    def test_updatetotals_combines_gain_and_loss(self):
        self.receipt_instance.receipt = [
            {"beni": "user1", "count": 2, "value": 5.0, "Lose": True},
            {"beni": "user1", "count": 1, "value": 3.0, "Lose": True},
            {"beni": "user2", "count": 2, "value": 4.0, "Lose": False},
            {"beni": "user2", "count": 1, "value": 1.5, "Lose": False},
        ]

        self.receipt_instance.updatetotals()

        self.assertEqual(self.receipt_instance.totals, {"user1": -13.0, "user2": 9.5})

    def test_hook_checkout(self):
        self.receipt_instance.receipt = [
            {"beni": None, "description": "desc -you-", "value": 5.0}
        ]
        with patch.object(self.receipt_instance, "updatetotals") as mock_updatetotals:
            self.receipt_instance.hook_checkout("user1")
            self.assertEqual(self.receipt_instance.receipt[0]["beni"], "user1")
            self.assertEqual(
                self.receipt_instance.receipt[0]["description"], "desc user1"
            )
            mock_updatetotals.assert_called_once()

    def test_hook_checkout_keeps_existing_beneficiary(self):
        self.receipt_instance.receipt = [
            {
                "beni": "other",
                "description": "desc -you-",
                "count": 1,
                "value": 5.0,
                "Lose": False,
            }
        ]

        self.receipt_instance.hook_checkout("user1")

        self.assertEqual(self.receipt_instance.receipt[0]["beni"], "other")
        self.assertEqual(self.receipt_instance.receipt[0]["description"], "desc user1")

    def test_hook_endsession(self):
        self.receipt_instance.receipt = [{"beni": "user1"}]
        self.receipt_instance.hook_endsession(None)
        self.assertEqual(self.receipt_instance.receipt, [])

    def test_hook_ok(self):
        self.receipt_instance.receipt = [{"beni": "user1"}]
        with patch.object(self.receipt_instance, "updatetotals") as mock_updatetotals:
            self.receipt_instance.hook_ok(None)
            self.assertEqual(self.receipt_instance.receipt, [])
            mock_updatetotals.assert_called_once()

    def test_hook_abort(self):
        self.receipt_instance.receipt = [{"beni": "user1"}]
        with patch.object(self.receipt_instance, "updatetotals") as mock_updatetotals:
            self.receipt_instance.hook_abort(None)
            self.assertEqual(self.receipt_instance.receipt, [])
            mock_updatetotals.assert_called_once()

    def test_add_new_item(self):
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(
                self.receipt_instance.add(True, 5.0, "desc", 1, "user1", "prod1")
            )
            self.assertEqual(len(self.receipt_instance.receipt), 1)

    def test_add_existing_item(self):
        self.receipt_instance.receipt = [
            {
                "description": "desc",
                "value": 5.0,
                "beni": "user1",
                "Lose": True,
                "count": 1,
                "product": "prod1",
            }
        ]
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(
                self.receipt_instance.add(True, 5.0, "desc", 1, "user1", "prod1")
            )
            self.assertEqual(self.receipt_instance.receipt[0]["count"], 2)

    def test_add_same_description_different_product_keeps_separate_lines(self):
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(
                self.receipt_instance.add(True, 5.0, "desc", 1, "user1", "prod1")
            )
            self.assertTrue(
                self.receipt_instance.add(True, 5.0, "desc", 1, "user1", "prod2")
            )

        self.assertEqual(len(self.receipt_instance.receipt), 2)
        self.assertEqual(
            [line["product"] for line in self.receipt_instance.receipt],
            ["prod1", "prod2"],
        )

    def test_input_remove(self):
        self.receipt_instance.receipt = [
            {"description": "item1"},
            {"description": "item2"},
        ]
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(self.receipt_instance.input("remove"))

    def test_help_and_input_other(self):
        self.assertEqual(self.receipt_instance.help(), {"remove": "Remove Item"})
        self.assertIsNone(self.receipt_instance.input("other"))

    def test_remove_valid_index(self):
        self.receipt_instance.receipt = [
            {
                "description": "item1",
                "beni": "user1",
                "count": 1,
                "value": 1.0,
                "Lose": False,
            },
            {
                "description": "item2",
                "beni": "user1",
                "count": 1,
                "value": 1.0,
                "Lose": False,
            },
        ]
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(self.receipt_instance.remove("0"))
            self.assertEqual(len(self.receipt_instance.receipt), 1)
            self.receipt_instance.master.callhook.assert_called_with("addremove", ())

    def test_remove_invalid_index(self):
        self.receipt_instance.receipt = [
            {"description": "item1"},
            {"description": "item2"},
        ]
        with patch.object(self.receipt_instance.master, "send_message"):
            self.assertTrue(self.receipt_instance.remove("invalid"))

    def test_startup(self):
        with patch.object(self.receipt_instance, "updatetotals") as mock_updatetotals:
            self.receipt_instance.startup()
            mock_updatetotals.assert_called_once()
