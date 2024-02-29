# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1].joinpath("src").absolute()))
# -- Project information -----------------------------------------------------

project = "EnhancedWebdriver"
copyright = "2024, Tesla200 (fratajczak124@gmail.com)"
author = "Tesla200 (fratajczak124@gmail.com)"
release = re.findall(
    r"version = ([\d.]+)", Path(__file__).parents[1].joinpath("setup.cfg").read_text()
)[0]

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
