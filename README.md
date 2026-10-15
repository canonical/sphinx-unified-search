# sphinx-unified-search

![Status: Work in Progress][status-badge]
![Feedback Welcome][feedback-badge]
![Config may change][config-badge]
![PyPI release][release-badge]

> **⚠️ Work in progress.** This project is under active development.
> Configuration options and behavior may change without notice. It has not
> been fully tested for production use, but early testers and feedback are
> very welcome. Please [open an issue][issues] if you hit problems or have
> suggestions.

## Cross-project search for Sphinx documentation

`sphinx-unified-search` is a Sphinx extension that lets you search across
multiple Sphinx documentation sites from a single search box. It works by
merging remote `searchindex.js` files into your project's local search index
at build time.

The standard [Sphinx] search UI is preserved: no new search box, no external
service, and no per-query cost.

## Features

- Works with existing Sphinx themes
- No JavaScript customization required
- No external search service required
- Preserves the standard Sphinx search UI
- Remote search results link directly to their original documentation pages,
  keeping traffic on the source sites
- Supports any number of remote Sphinx projects
- Supports token-authenticated fetching for private/internal projects

## Who might find this useful

- **Upstream / downstream content**- if your (product and) docs build on top of
  an upstream project maintained elsewhere, your users can search the upstream
  or related (Sphinx) docs without leaving your site.
- **Multi-product teams** - separate Sphinx sites that share an audience, where
  users shouldn’t have to know which exact site to search. Or products that are
  part of a larger ecosystem.
- **Internal platform teams** - private doc sets that (may) need to be
  searchable alongside public ones without setting up new infrastructure.

---

## How to use the extension

Installing and configuring `sphinx-unified-search` is straightforward. If you
also want to include a private [Read the Docs (RTD)] project in the unified
search results, complete the extra setup below first.

### Configure access to private documentation projects

If you want to include a private RTD project in the unified search, you must
create an HTTP header token that can be used to download its `searchindex.js`.

For each private project:

1. Open the project's Read the Docs settings.
1. Go to "Sharing" and "Add share".
1. Select "HTTP header token" for the "Access type", and a suitable expiry
   date.
1. Select "Allow access to all versions?" if you intend to use `searchindex.js`
   for all versions of the docs set. Otherwise, unselect that option and add the
   versions that will be used by `sphinx-unified-search`.

Copy the generated token and store it as a secret environment variable in the
RTD project that is _building_ the unified search.

For example, if "PROJECT B" wants to the `searchindex.js` from "PROJECT A" to
its search results, generate the HTTP header token in PROJECT A, and add that as
an environment variable in PROJECT B
(e.g. `PROJECTA_DOCS_TOKEN=<generated HTTP header token>`).

### Install the extension

Add `sphinx-unified-search` to the `requirements.txt` file in your Sphinx
project:

```text
sphinx-unified-search
```

### Enable the extension

Add `sphinx_unified_search` to the `extensions` list in `conf.py`:

```python
extensions = [
    "sphinx_unified_search",
]
```

### Configure projects to index for unified search

Configure the list of documentation projects whose search indexes should be
included in the unified search.

For each project, specify:

- `name`: A unique identifier for the project. For search results from
  projects other than the host project, this value is appended to the page
  title in the search results.
- `base_url`: The base URL of the documentation, used as the destination when
  a user clicks a search result.
- `searchindex_url`: The URL of the project's `searchindex.js`.

For private projects, also specify:

- `auth_token_env`: The name of the environment variable containing the RTD HTTP
  header token.
- `auth_scheme`: The authorization scheme to use in the HTTP `Authorization`
  header. For RTD HTTP header tokens, set this to `"Token"`.

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

For example, if your remote project uses this config:

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

Repeat this for each private project included in `unified_search_projects` set.

Once the required environment variables are set, build or serve the
documentation as usual with `make html` or `make run`.

## Some things to note

A few behaviors and limitations to be aware of before you publish a unified
search, especially if you include private projects.

### Private docs: result previews

On the search results page, each result shows a short preview of the matching
content, fetched from the remote project’s page. This request is made
client-side in the visitor’s browser, so it can’t use the build-time token, and
it is subject to the browser’s same-origin policy.

The preview loads only if the remote page is same-origin or allows cross-origin
requests via CORS headers. Otherwise, the extension shows a placeholder message
instead. The search results and their links work normally in all cases.

### Beware of headings

If you add a private project as a remote of a public docs set, page titles and
headings from the private project will appear in the public search results, even
though the page _content_ itself won't load. Don't include private projects
whose titles or headings contain confidential information.

### Build the docs in CI (GitHub Actions)

Adding a secret to a repository doesn't automatically expose it to every
workflow run. Each job that needs it must reference it explicitly.

This matters most when the docs build runs in a reusable workflow (for example, `uses: ./.github/workflows/build-docs.yml`). Secrets aren't inherited by the
called workflow by default. A build that works locally with an exported token
can therefore fail in CI, or silently skip the private index.

To fix this, pass the secret through in the calling workflow:

```yaml
jobs:
  build-docs:
    uses: ./.github/workflows/build-docs.yml
    secrets:
      PROJECTA_DOCS_TOKEN: ${{ secrets.PROJECTA_DOCS_TOKEN }}
    # or, to pass all secrets: `secrets: inherit`
```

The reusable workflow must also declare the secret under
`on.workflow_call.secrets`, and the build step should expose it as an
environment variable named in `auth_token_env`.


[status-badge]: https://img.shields.io/badge/status-work%20in%20progress-yellow
[feedback-badge]: https://img.shields.io/badge/feedback-welcome-blue
[config-badge]: https://img.shields.io/badge/config-subject%20to%20change-orange
[release-badge]: https://img.shields.io/pypi/v/sphinx-unified-search
[issues]: https://github.com/canonical/sphinx-unified-search/issues
[Sphinx]: https://www.sphinx-doc.org/en/master/
[Read the Docs (RTD)]: https://about.readthedocs.com/