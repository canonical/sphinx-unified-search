# How to configure unified search

This guide shows how to install the `sphinx-unified-search` extension, add
public and private projects to the search, filter results by project, and avoid
repeated downloads during live preview (`sphinx autobuild`).

For the full list of settings, see the
{doc}`configuration reference </reference/configuration>`.

## Install the extension

Add `sphinx-unified-search` to the `requirements.txt` file in your Sphinx
project:

```{code-block} text
sphinx-unified-search
```

## Enable the extension

Add `sphinx_unified_search` to the `extensions` list in `conf.py`:

```{code-block} python
extensions = [
    "sphinx_unified_search",
]
```

## Configure remote projects to index

Configure the list of remote documentation projects whose search indexes
should be included in the unified search for your host project. For each
project, specify `name`, `base_url` and `searchindex_url`. For private projects,
also specify `auth_token_env` and `auth_scheme`.

```{code-block} python
unified_search_projects = [
    # Public project - no auth needed, plain HTTP fetch
    {
        "name": "Landscape",
        "base_url": "https://ubuntu.com/landscape/docs/",
        "searchindex_url": "https://ubuntu.com/landscape/docs/searchindex.js",
    },

    # Private project - token-gated fetch
    {
        "name": "ProjectA",
        "base_url": "https://documentation.ubuntu.com/projecta/",
        "searchindex_url": "https://documentation.ubuntu.com/projecta/searchindex.js",
        "auth_token_env": "PROJECTA_DOCS_TOKEN",
        "auth_scheme": "Token",
    },
]
```

For Read the Docs HTTP header tokens, set `auth_scheme` to `"Token"`.

To include a private Read the Docs (RTD) project you must first create the
token. See
{doc}`Build with private projects </how-to/build-with-private-projects>`.

```{note}
Page titles and headings from a private project appear in the search results
of the site that includes it. See
{ref}`Private projects and previews <exp-how-it-works-private-projects-and-previews>`.
```

## Filter search results by project

Add project filter chips to the search results page so visitors can narrow
the results to one or more projects:

```{code-block} python
unified_search_project_filter = True

# Optional: label for the host project's own results in the filter.
# Defaults to Sphinx's `project` setting.
unified_search_local_project_name = "My Docs"
```

When the search has finished, a "Filter by project" row appears above the
results, with one chip per project that has results and the number of results
next to it. Select one or more chips to show only those projects; select
"All" (or deselect every chip) to show everything again.

For more details on the filter behavior, see the
{ref}`configuration reference <ref-configuration-unified-search-project-filter>`.

## Fetch remote indexes once per live-preview session

By default, every build downloads each remote `searchindex.js` again. With
[sphinx-autobuild](https://github.com/sphinx-doc/sphinx-autobuild)
(`make run`), that means triggering a fresh download of every remote index on
each rebuild, which slows down the edit-preview loop.

To download each remote index only once per `sphinx-autobuild` session and
reuse it for later rebuilds, set:

```{code-block} python
unified_search_cache_remote_indexes = True
```

Regular builds (`make html`, Read the Docs, CI) are unaffected and always
fetch fresh indexes. For how the cache is scoped and keyed, see the
{ref}`configuration reference <ref-configuration-unified-search-cache-remote-indexes>`.
