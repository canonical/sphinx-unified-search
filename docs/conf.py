import datetime
import os
import textwrap

# Configuration for the Sphinx documentation builder.
# Project-specific configuration is defined below.
#
# A complete list of built-in Sphinx configuration values:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# The Sphinx Stack uses the Canonical Sphinx theme to keep all documentation consistent
# and on brand:
# https://github.com/canonical/canonical-sphinx

#######################
# Project information #
#######################

project = "Sphinx Unified Search"

# Author name; used in the default copyright statement in the page footer
author = "Canonical"

# The year in the copyright statement
copyright = f"{datetime.date.today().year}"

# Sidebar documentation title
# To disable the title, set it to an empty string.
html_title = project + " documentation"

# Documentation website URL
ogp_site_url = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

# Preview name of the documentation website
ogp_site_name = project

# Canonical Sphinx Stack preview image
ogp_image = "https://assets.ubuntu.com/v1/cc828679-docs_illustration.svg"

# Dictionary of values to pass into the Sphinx context for all pages:
# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-html_context
html_context = {
    # This project has no separate product website.
    "product_page": "github.com/canonical/sphinx-unified-search",
    # Community channels are not configured for this project.
    "discourse": "",
    "mattermost": "",
    "matrix": "",
    # Links to the documentation source and issue tracker.
    "github_url": "https://github.com/canonical/sphinx-unified-search",
    # Docs branch in the repo; used in links for viewing the source files
    "repo_default_branch": "main",
    # Docs location in the repo; used in links for viewing the source files
    "repo_folder": "/docs/",
    # Valid options: none, prev, next, both
    # "sequential_nav": "",
    "display_contributors": False,
    # Required for feedback button
    "github_issues": "enabled",
    # Passes the top-level 'author' value to the theme
    "author": author,
    # Documentation license information
    "license": {
        "name": "GPL-3.0-or-later",
        "url": "https://github.com/canonical/sphinx-unified-search/blob/main/LICENSE",
    },
}

html_theme_options = {
    "source_edit_link": "https://github.com/canonical/sphinx-unified-search",
}

#######################
# Sitemap configuration: https://sphinx-sitemap.readthedocs.io/
#######################

# Use RTD canonical URL to ensure duplicate pages have a specific canonical URL
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "/")

# sphinx-sitemap uses html_baseurl to generate the full URL for each page:
sitemap_url_scheme = "{link}"

# Include `lastmod` dates in the sitemap:
sitemap_show_lastmod = True

# Exclude non-user-facing Sphinx pages from the sitemap.
sitemap_excludes = [
    "404/",
    "genindex/",
    "search/",
]

################################
# Template and asset locations #
################################

html_static_path = ["_dev/_static"]
# templates_path = ["_templates"]

#############
# Redirects #
#############

# Add redirects to the 'redirects.txt' file
# https://sphinxext-rediraffe.readthedocs.io/en/latest/

# To set up redirects in the Read the Docs project dashboard:
# https://docs.readthedocs.io/en/stable/guides/redirects.html

rediraffe_redirects = "redirects.txt"

# Strips '/index.html' from destination URLs when building with 'dirhtml'
rediraffe_dir_only = True


############################
# sphinx-llm configuration #
############################

# This description is included in llms.txt to provide context for the documentation.
llms_txt_description = textwrap.dedent(
    """\
    This is the documentation for Sphinx Unified Search, a Sphinx extension that
    combines search results from multiple Sphinx documentation sites.
    """
)

# The base URL for references built by sphinx-markdown-builder.
if os.environ.get("READTHEDOCS"):
    markdown_http_base = html_baseurl

###########################
# Link checker exceptions #
###########################

# A regex list of URLs that are ignored by 'make linkcheck'
linkcheck_ignore = [
    "http://127.0.0.1:8000",
    "https://github.com",
    r"https://matrix\.to/.*",
    # SourceForge domains often block linkcheck
    r"https://.*\.sourceforge\.(net|io)/.*",
]

# A regex list of URLs where anchors are ignored by 'make linkcheck'
linkcheck_anchors_ignore_for_url = [r"https://github\.com/.*"]

# How long the link checker will wait for a response for each request
# linkcheck_timeout = 30

# Give linkcheck multiple tries on failure
linkcheck_retries = 3

########################
# Configuration extras #
########################

# Custom MyST syntax extensions; see
# https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
# NOTE: By default, the following MyST extensions are enabled:
#   - substitution
#   - deflist
#   - linkify
# myst_enable_extensions = set()

# Custom Sphinx extensions; see
# https://www.sphinx-doc.org/en/master/usage/extensions/index.html
extensions = [
    "canonical_sphinx",
    "notfound.extension",
    "sphinx_design",
    "sphinx_rerediraffe",
    "sphinx_reredirects",
    "sphinx_tabs.tabs",
    "sphinxcontrib.jquery",
    "sphinxext.opengraph",
    "sphinx_config_options",
    "sphinx_contributor_listing",
    "sphinx_filtered_toctree",
    "sphinx_llm.txt",
    "sphinx_related_links",
    "sphinx_roles",
    "sphinx_terminal",
    "sphinx_ubuntu_images",
    "sphinx_youtube_links",
    "sphinxcontrib.cairosvgconverter",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
    "sphinx_sitemap",
    "sphinx_structured_toc",
]

# Excludes files or directories from processing
exclude_patterns = [
    "doc-cheat-sheet*",
    ".venv*",
    "_dev/*",
]

# Adds custom CSS files, located remotely or in 'html_static_path'.
html_css_files = [
    "domain-list-override.css",
]

# Adds custom JavaScript files, located remotely or in 'html_static_path'.
# html_js_files = [
#     "https://assets.ubuntu.com/v1/287a5e8f-bundle.js",
# ]

# Appends extra markup to the end of every document written in reST
# rst_epilog = """
# """

# Feedback is enabled for this public GitHub project.
# disable_feedback_button = True

# Specifies a reST snippet to be prepended to each .rst file
# This defines a :center: role that centers table cell content.
# This defines a :h2: role that styles content for use with PDF generation.
rst_prolog = """
.. role:: center
   :class: align-center
.. role:: h2
    :class: hclass2
.. role:: woke-ignore
    :class: woke-ignore
.. role:: vale-ignore
    :class: vale-ignore
"""

# Configuration for Intersphinx projects
#
# intersphinx_mapping = {
#     "snap": ("https://snapcraft.io/docs/", None),
# }
