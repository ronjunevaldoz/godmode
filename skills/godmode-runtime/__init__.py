"""Skills package for the godmode runtime."""

__version__ = "1.0.0"
__author__ = "Agent System"

# Import all skills from submodules
try:
    from .skills.core import *
    from .skills.utilities import *
    from .skills.analysis import *
    from .skills.communication import *
    from .skills.tools import *
    from .skills.helpers import *
except ImportError:
    # Handle cases where modules might not exist yet
    pass

