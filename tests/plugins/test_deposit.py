from unittest.mock import Mock, patch, call
import json
import plugins.deposit as deposit_module
import pytest


def test_deposit_help():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)
    assert deposit.help() == {"deposit": "Deposit Money"}


def test_deposit_input_not_matching():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    assert deposit.input("not_deposit") is None


def test_deposit_input_matching():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    assert deposit.input("deposit") == True
    master_mock.donext.assert_called_with(deposit, "value")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "How much do you want to deposit?"),
            call(True, "buttons", json.dumps({"special": "numbers"})),
        ]
    )


def test_deposit_value_valid_amount():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    deposit.master.receipt = Mock()

    assert deposit.value("50") == True
    deposit.master.receipt.add.assert_called_with(
        False, 50.0, "Deposit", 1, None, "deposit"
    )


def test_deposit_value_invalid_amount():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    assert deposit.value("1000") == True
    master_mock.donext.assert_called_with(deposit, "value")
    master_mock.send_message.assert_has_calls(
        [
            call(True, "message", "Enter an amount between 0.01 and 999.99:"),
            call(True, "buttons", json.dumps({"special": "numbers"})),
        ]
    )


def test_deposit_value_abort():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    assert deposit.value("abort") == True
    master_mock.callhook.assert_called_with("abort", None)


def test_deposit_value_non_numeric():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)

    assert deposit.value("not_a_number") == True
    master_mock.donext.assert_called_with(deposit, "value")
    master_mock.send_message.assert_has_calls(
        [
            call(
                True,
                "message",
                "Not a valid number! How much do you want to deposit?",
            ),
            call(True, "buttons", json.dumps({"special": "numbers"})),
        ]
    )


def test_deposit_startup():
    master_mock = Mock()
    deposit = deposit_module.deposit("SID", master_mock)
    # Assuming startup is a placeholder with no functional code
    deposit.startup()
    # No assertion needed, just checking if method exists and runs without error


@pytest.mark.parametrize("value", ["0.001", "1.234", "NaN", "Infinity", "-1"])
def test_deposit_rejects_fractional_cents_and_nonfinite_values(value):
    master = Mock()
    plugin = deposit_module.deposit("SID", master)
    plugin.value(value)
    master.receipt.add.assert_not_called()


def test_checkout_aggregates_deposits_by_user_and_clears_on_next_input():
    master = Mock()
    master.receipt.receipt = [
        {
            "beni": "test_user",
            "product": "deposit",
            "Lose": False,
            "value": 25,
            "count": 2,
        },
        {
            "beni": "test_user",
            "product": "deposit",
            "Lose": False,
            "value": 5,
            "count": 1,
        },
        {
            "beni": "test_user",
            "product": "drink",
            "Lose": True,
            "value": 10,
            "count": 1,
        },
        {"beni": "cash", "product": "deposit", "Lose": False, "value": 2, "count": 1},
    ]
    plugin = deposit_module.deposit("SID", master)
    plugin.hook_post_checkout("test_user")
    retain, topic, payload = master.send_message.call_args.args
    assert retain and topic == "deposit_payment"
    payments = json.loads(payload)["payments"]
    assert len(payments) == 1
    assert payments[0]["amount"] == "55.00"
    assert payments[0]["reference"] == "test_user"
    plugin.pre_input("ok")
    master.send_message.assert_called_with(True, "deposit_payment", "{}")
    master.send_message.reset_mock()
    plugin.pre_input("next")
    master.send_message.assert_not_called()


def test_normal_checkout_does_not_offer_payment():
    master = Mock()
    master.receipt.receipt = []
    deposit_module.deposit("SID", master).hook_post_checkout("test_user")
    master.send_message.assert_not_called()
