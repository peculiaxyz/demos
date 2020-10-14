import os
import sys

# Doing it manually because it doesnt work without this
# Not sure if the problem is me or...
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name)
