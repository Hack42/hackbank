from unittest.mock import Mock, patch, call
import json
import plugins.deposit as deposit_module


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

    with patch("plugins.deposit.traceback.print_exc") as mock_traceback:
        assert deposit.value("not_a_number") == True
        mock_traceback.assert_called()
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
