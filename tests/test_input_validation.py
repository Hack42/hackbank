from unittest.mock import Mock

from input_validation import (
    filter_reserved_aliases,
    is_reserved_input,
    is_valid_alias,
    is_valid_input_token,
    is_valid_product_name,
    reserved_inputs,
)


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


def test_input_token_validation_is_ascii_alnum_only():
    assert is_valid_input_token("abc123", min_length=4)
    assert not is_valid_input_token("abc_123", min_length=4)
    assert not is_valid_input_token("abc-123", min_length=4)
    assert not is_valid_input_token("abc", min_length=4)
    assert not is_valid_input_token(None, min_length=4)


def test_product_and_alias_validation_lengths():
    assert is_valid_product_name("prod")
    assert not is_valid_product_name("pro")
    assert is_valid_alias("alias1")
    assert not is_valid_alias("abcde")
