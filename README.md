# sphinx-unified-search

**THIS PROJECT IS STILL A WORK IN PROGRESS**

Merge search indexes from multiple Sphinx documentation sites.

`sphinx-unified-search` downloads remote Sphinx `searchindex.js` files during
the HTML build and merges them into the local search index.

The standard Sphinx search UI is preserved, while users can search across
multiple independent documentation projects from a single search box.

## Features

- Works with existing Sphinx themes
- No JavaScript customization required
- No external search service required
- Preserves the standard Sphinx search UI
- Remote results open on their original site
- Supports any number of remote Sphinx projects
- Supports token-authenticated fetching for private/internal projects

---

## Use the extension

The `sphinx-unified-search` extension may need to access two types of private
resources during a documentation build:

- the private GitHub repository that hosts the extension itself
- any private Read the Docs projects whose search indexes should be included

Complete the following setup before installing and configuring the extension.

### Configure access to sphinx-unified-search extension

Since the `sphinx-unified-search` extension is currently internal and
accessible only within the organization, you must configure access to the
private GitHub repository before Read the Docs (RTD) can install it during a
documentation build.

1. Create a GitHub personal access token (PAT) with read access to the
   `canonical/sphinx-unified-search` repository.
   - This can be a dedicated bot account if preferred.
   - Copy the generated token, as GitHub will not display it again.
1. Add the token as a secret environment variable in the Read the Docs project
   that will use the extension.
   - Go to **https://app.readthedocs.com/dashboard/<project>/edit/** \>
   **Building** \> **Environment variables**.
   - Add a new variable, for example, "SPHINX_UNIFIED_SEARCH_TOKEN", and paste the PAT
     as its value.
   - Enable "Expose this environment variable in PR builds" if pull request
     builds also need to install the extension.
1. If your documentation is also built in GitHub Actions, add the same token as
   a GitHub Actions secret named `SPHINX_UNIFIED_SEARCH_TOKEN`.

Once the environment variable is configured, RTD can authenticate with GitHub
and install the extension without storing credentials in your repository.

### Configure access to private documentation projects

If you want to include a private RTD project in the unified search, you must
create an HTTP header token that can be used to download its `searchindex.js`.

For each private project:

1. Open the project's Read the Docs settings.
1. Go to "Sharing" and "Add share".
1. Select "HTTP header token" for the "Access type", and a suitable expiry date.
1. Select the "Allow access to all versions?" option if you intend to use the
   `searchindex.js` for all versions of the docs set.
   Otherwise, unselect that option and add the versions that will be used for
   `sphinx-unified-search` extension. 

Copy the generated token and store it as a secret environment variable in
the Read the Docs project that is building the unified search.

For example, `KFACTORY_DOCS_TOKEN=<generated HTTP header token>`.

### Install the extension

Add `sphinx-unified-search` to the `requirements.txt` file in your Sphinx
project:

```
git+https://x-access-token:${SPHINX_UNIFIED_SEARCH_TOKEN}@github.com/canonical/sphinx-unified-search.git@main
```

### Enable the extension

Add `sphinx_unified_search` to the `extensions` list in `conf.py`:

```python
extensions = [
    "sphinx_unified_search",
]
```

### Configure projects to index

Configure the list of documentation projects whose search indexes should be
included in the unified search.

For each project, specify:

- `name`: a unique identifier for the project. For search results from projects
  other than the host project, this value is appended to the page title.
- `base_url`: the base URL of the documentation, used as the destination when a
  user clicks a search result.
- `searchindex_url`: the URL of the project's `searchindex.js`.

For private projects, also specify:

- `auth_token_env`: the name of the environment variable containing the Read the
  Docs HTTP header token.
- `auth_scheme`: the authorization scheme to use in the HTTP `Authorization`
  header. For Read the Docs HTTP header tokens, set this to "Token".

```python
unified_search_projects = [
    # Public project — no auth needed, plain HTTP fetch
    {
        "name": "Landscape",
        "base_url": "https://documentation.ubuntu.com/landscape/",
        "searchindex_url": "https://documentation.ubuntu.com/landscape/searchindex.js",
    },

    # Private project — token-gated fetch
    {
        "name": "KernelFactory",
        "base_url": "https://documentation.ubuntu.com/kernelfactory/latest/",
        "searchindex_url": "https://documentation.ubuntu.com/kernelfactory/latest/searchindex.js",
        "auth_token_env": "KFACTORY_DOCS_TOKEN",
        "auth_scheme": "Token",
    },
]
```

### Build the docs locally

When building the documentation locally, you must set the environment variables
referenced by the `auth_token_env` entries in `unified_search_projects`.

For example, if a project uses:

```python
{
    "auth_token_env": "KFACTORY_DOCS_TOKEN",
    ...
}
```

Export the corresponding token before building:

```shell
export KFACTORY_DOCS_TOKEN="<token>"
```

Repeat this for each private project included in `unified_search_projects`.

Once the required environment variables are set, build or serve the
documentation as usual with `make html` or `make run`.