# Annotated Registry
# A wrapper to make the IOTile component registry accessible in the iotile
# tool.  Since the registry is used internally in the type system it cannot
# itself make use of typedargs annotations
from iotile.core.utilities.typedargs import annotated, param, return_type, context
from iotile.core.exceptions import ExternalError
from .registry import ComponentRegistry

_name_ = "Developer"


@annotated
def registry():
    return AnnotatedRegistry()

@context()
class AnnotatedRegistry(object):
    """
    AnnotatedRegistry

    A mapping of all of the installed components on this system that can
    be used as build dependencies and where they are located.  Also used
    to manage iotile plugins.
    """

    def __init__(self):
        self.reg = ComponentRegistry()

    @param("component", "path", "exists", desc="folder containing component to register")
    def add_component(self, component):
        """
        Register a component with ComponentRegistry.

        Component must be a buildable object with a module_settings.json file that
        describes its name and the domain that it is part of.
        """

        self.reg.add_component(component)

    @return_type("map(string, string)")
    def list_plugins(self):
        """
        List all of the plugins that have been registerd for the iotile program on this computer
        """

        return self.reg.list_plugins()

    def find_component(self, key, domain=""):
        return self.reg.find_component(key, domain)

    @param("key", "string", desc="iotile component to find")
    def remove_component(self, key):
        """
        Remove component from registry
        """

        return self.reg.remove_component(key)

    @annotated
    def clear_components(self):
        """
        Clear all of the registered components
        """

        self.reg.clear_components()

    @return_type("list(string)")
    def list_components(self):
        """
        List all of the registered component names
        """

        return self.reg.list_components()

    @return_type("list(string)")
    def list_config(self):
        """
        List all of the registered component names
        """

        return self.reg.list_config()

    @param("key", "string")
    @param("value", "string")
    def set(self, key, value):
        self.reg.set_config(key, value)

    @param("key", "string")
    @return_type("string")
    def get(self, key):
        return self.reg.get_config(key)

    @param("key", "string")
    @return_type("string")
    def clear(self, key):
        self.reg.clear_config(key)

    @annotated
    def freeze(self):
        """Freeze the current list of extensions to a single file.

        This speeds up the extension loading process but does not check for
        new extensions each time the program is run. You should only use this
        method in situations where you know the extension list is static
        and you need the speedup benefits.

        You can undo this by calling unfreeze().
        """

        self.reg.freeze_extensions()

    @annotated
    def unfreeze(self):
        """Remove any frozen extension list."""

        try:
            self.reg.unfreeze_extensions()
        except ExternalError:
            pass  # This means there was no frozen list of extensions
