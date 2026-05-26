RESERVED_INPUTS = {"abort", "ok"}


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
