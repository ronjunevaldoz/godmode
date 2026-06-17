"""Skills package for the godmode agent system."""

__version__ = "1.0.0"
__author__ = "Agent System"

# Import all skills from submodules
try:
    from .godmode-runtime.skills.core import *
    from .godmode-runtime.skills.utilities import *
    from .godmode-runtime.skills.analysis import *
    from .godmode-runtime.skills.communication import *
    from .godmode-runtime.skills.tools import *
    from .godmode-runtime.skills.helpers import *
except ImportError:
    # Handle cases where modules might not exist yet
    pass

