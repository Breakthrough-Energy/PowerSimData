import os
import sys

# This ensures that we can always test, no matter the installation method.
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import powersimdata