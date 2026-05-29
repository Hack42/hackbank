import re


RESERVED_INPUTS = {"abort", "ok"}
INPUT_TOKEN_RE = re.compile(r"^[A-Za-z0-9]+$")


def reserved_inputs(master=None, plugin_help=None):
    reserved = set(RESERVED_INPUTS)
    if isinstance(plugin_help, dict):
        reserved.update(plugin_help.keys())
    master_help = getattr(master, "help", {})
    if isinstance(master_help, dict):
        reserved.update(master_help.keys())
    return reserved


def is_reserved_input(text, master=None, plugin_help=None):
    return text in reserved_inputs(master=master, plugin_help=plugin_help)


def filter_reserved_aliases(aliases, master=None, plugin_help=None):
    return [
        alias
        for alias in aliases
        if not is_reserved_input(alias, master=master, plugin_help=plugin_help)
    ]


def is_valid_input_token(text, min_length):
    return (
        isinstance(text, str)
        and len(text) >= min_length
        and INPUT_TOKEN_RE.fullmatch(text) is not None
    )


def is_valid_alias(text):
    return is_valid_input_token(text, min_length=6)


def is_valid_product_name(text):
    return is_valid_input_token(text, min_length=4)
