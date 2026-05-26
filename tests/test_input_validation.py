from unittest.mock import Mock

from input_validation import filter_reserved_aliases, is_reserved_input, reserved_inputs


def test_reserved_inputs_include_core_plugin_and_master_commands():
    master = Mock(help={"deposit": "Deposit Money"})

    assert reserved_inputs(master=master, plugin_help={"addproduct": "Add"}) == {
        "abort",
        "ok",
        "addproduct",
        "deposit",
    }


def test_is_reserved_input():
    master = Mock(help={"deposit": "Deposit Money"})

    assert is_reserved_input("deposit", master=master)
    assert is_reserved_input("abort", master=master)
    assert not is_reserved_input("cola", master=master)


def test_filter_reserved_aliases_preserves_non_reserved_order():
    master = Mock(help={"deposit": "Deposit Money"})

    assert filter_reserved_aliases(
        ["alias1", "deposit", "ok", "alias2"], master=master
    ) == ["alias1", "alias2"]
