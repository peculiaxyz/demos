import os
import sys

# Dont wanna expose all modules to clients using __all__
# Todo, rather import private modules here and alias them?
WORKING_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(WORKING_DIR)

# Set working dir, before main script executes
os.chdir(WORKING_DIR)
