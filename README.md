# sphinx-unified-search

![Status: Work in Progress][status-badge]
![Feedback Welcome][feedback-badge]
![Config may change][config-badge]
![No release yet][release-badge]

> **⚠️ Work in progress.** This project is under active development.
> Configuration options and behavior may change without notice. It is not yet
> recommended for production use, but early testers and feedback are very
> welcome. Please [open an issue][issues] if you hit problems or have
> suggestions.

## Cross-project search for Sphinx documentation

`sphinx-unified-search` is a Sphinx extension that lets you search across
multiple Sphinx documentation sites from a single search box. It works by
merging remote `searchindex.js` files into your project's local search index
at build time.

The standard Sphinx search UI is preserved: no new search box, no external
service, and no per-query cost.

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

Installing and configuring `sphinx-unified-search` is straightforward. If you
also want to include a private Read the Docs project in the unified search,
complete the extra setup below first.

### Configure access to private documentation projects

If you want to include a private RTD project in the unified search, you must
create an HTTP header token that can be used to download its `searchindex.js`.

For each private project:

1. Open the project's Read the Docs settings.
1. Go to "Sharing" and "Add share".
1. Select "HTTP header token" for the "Access type", and a suitable expiry
   date.
1. Select "Allow access to all versions?" if you intend to use
   `searchindex.js` for all versions of the docs set. Otherwise, unselect that
   option and add the versions that will be used by
   `sphinx-unified-search`.

Copy the generated token and store it as a secret environment variable in the
Read the Docs project that is building the unified search.

For example, `PROJECTA_DOCS_TOKEN=<generated HTTP header token>`.

### Install the extension

Add `sphinx-unified-search` to the `requirements.txt` file in your Sphinx
project:

```text
git+https://github.com/canonical/sphinx-unified-search.git@main
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

- `name`: A unique identifier for the project. For search results from
  projects other than the host project, this value is appended to the page
  title.
- `base_url`: The base URL of the documentation, used as the destination when
  a user clicks a search result.
- `searchindex_url`: The URL of the project's `searchindex.js`.

For private projects, also specify:

- `auth_token_env`: The name of the environment variable containing the Read
  the Docs HTTP header token.
- `auth_scheme`: The authorization scheme to use in the HTTP `Authorization`
  header. For Read the Docs HTTP header tokens, set this to `"Token"`.

```python
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

### Build the docs locally

When building the documentation locally, you must set the environment variables
referenced by the `auth_token_env` entries in `unified_search_projects`.

For example, if a project uses:

```python
{
    "auth_token_env": "PROJECTA_DOCS_TOKEN",
    ...
}
```

Export the corresponding token before building:

```shell
export PROJECTA_DOCS_TOKEN="<token>"
```

Repeat this for each private project included in `unified_search_projects`.

Once the required environment variables are set, build or serve the
documentation as usual with `make html` or `make run`.

### Build the docs in CI (GitHub Actions)

Adding a secret to a repository does not automatically expose it to a workflow
run. Each job that needs it must reference it explicitly.

This matters in particular if the docs build happens inside a reusable
workflow (for example, `uses: ./.github/workflows/build-docs.yml`). Secrets
are not inherited by the called workflow by default, so a token that works
when docs are built locally can silently be missing in CI.

This means a private-project build that works fine with a manually exported
token on your machine can fail, or quietly skip the private index, when it
runs in GitHub Actions, unless the calling workflow is explicitly set up to
pass its secrets through.

[status-badge]: https://img.shields.io/badge/status-work%20in%20progress-yellow
[feedback-badge]: https://img.shields.io/badge/feedback-welcome-blue
[config-badge]: https://img.shields.io/badge/config-subject%20to%20change-orange
[release-badge]: https://img.shields.io/badge/PyPI-not%20published-lightgrey
[issues]: https://github.com/canonical/sphinx-unified-search/issues
