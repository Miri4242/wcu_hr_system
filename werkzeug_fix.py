#!/usr/bin/env python3
# Werkzeug compatibility fix

import werkzeug

# Add __version__ attribute if it doesn't exist
if not hasattr(werkzeug, '__version__'):
    try:
        import importlib.metadata
        werkzeug.__version__ = importlib.metadata.version('werkzeug')
    except ImportError:
        # Fallback for older Python versions
        import pkg_resources
        werkzeug.__version__ = pkg_resources.get_distribution('werkzeug').version
    except:
        # Ultimate fallback
        werkzeug.__version__ = '3.0.0'

print(f"Werkzeug version set to: {werkzeug.__version__}")