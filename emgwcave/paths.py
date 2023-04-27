"""
Module for defining paths to data directories.
"""
import os
from pathlib import Path

base_output_dir = os.getenv("EMGWCAVE_DIR", Path.home().joinpath("Data/emgwcave/"))