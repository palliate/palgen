import importlib

def get_command(package_name):
    module_name = f"palgen.commands.{package_name}"
    module = importlib.import_module(module_name)
    return getattr(module, package_name)
