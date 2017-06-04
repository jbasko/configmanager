from .base import BaseSection


class SimpleSection(BaseSection):
    """
    Core section functionality.

    Keep as light as possible.
    No persistence, hooks or other fancy features here.
    Add those on Config if at all.

    No customisation (section classes, item classes etc.) allowed here.
    An instance of SimpleSection is used internally to store customisation of configmanager itself.
    """
    pass
