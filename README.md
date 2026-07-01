# sphinx-unified-search

**THIS PROJECT IS STILL A WORK IN PROGRESS**

Merge search indexes from multiple Sphinx documentation sites.

`sphinx-unified-search` downloads remote Sphinx
`searchindex.js` files during the HTML build and merges
them into the local search index.

The standard Sphinx search UI is preserved, while users
can search across multiple independent documentation
projects from a single search box.

## Features

- Works with existing Sphinx themes
- No JavaScript customization required
- No external search service required
- Preserves the standard Sphinx search UI
- Remote results open on their original site
- Supports any number of remote Sphinx projects
- Supports token-authenticated fetching for private/internal projects

---

## Installation

```bash
pip install sphinx-unified-search
```

## Enable the extension

Add the extension to your `conf.py`:

```python
extensions = [
    "sphinx_unified_search",
]
```

## Configure remote projects

```python
unified_search_projects = [
    {
        "name": "Juju",
        "base_url": "https://juju.is/docs",
        "searchindex_url":
            "https://juju.is/docs/searchindex.js",
    },
    {
        "name": "Pebble",
        "base_url":
            "https://documentation.ubuntu.com/pebble",
        "searchindex_url":
            "https://documentation.ubuntu.com/pebble/searchindex.js",
    },
]
```

## Build

```bash
make html
```

The generated `searchindex.js` will contain:

- pages from the local documentation project
- pages from every configured remote project

No changes to themes or templates are required.

---

## Private / internal projects

Some `searchindex.js` files aren't publicly reachable — for example,
documentation hosted behind SSO, a VPN-only network, or an internal
reverse proxy that requires a bearer token. `sphinx-unified-search`
supports this by resolving a token **from an environment variable**
at build time and sending it as a request header when fetching that
project's `searchindex_url`.

Tokens are never written into `conf.py` or checked into version
control — only the *name* of the environment variable is configured,
and the value is read from the environment at build time.

### Configuring a private project

Add `auth_token_env` to that project's entry:

```python
unified_search_projects = [
    {
        "name": "Juju",
        "base_url": "https://juju.is/docs",
        "searchindex_url":
            "https://juju.is/docs/searchindex.js",
        # public project — no auth fields needed
    },
    {
        "name": "Internal Kernel Docs",
        "base_url":
            "https://docs.internal.example.com/kernel",
        "searchindex_url":
            "https://docs.internal.example.com/kernel/searchindex.js",
        "auth_token_env": "INTERNAL_DOCS_TOKEN",
    },
]
```

At build time, the extension reads `os.environ["INTERNAL_DOCS_TOKEN"]`
and sends it as:

```
Authorization: Bearer <token>
```

If your internal server expects a different header name or scheme
(for example a custom header, or no scheme prefix), override either:

```python
{
    "name": "Internal Kernel Docs",
    "base_url": "https://docs.internal.example.com/kernel",
    "searchindex_url":
        "https://docs.internal.example.com/kernel/searchindex.js",
    "auth_token_env": "INTERNAL_DOCS_TOKEN",
    "auth_header": "Private-Token",
    "auth_scheme": "",
}
```

### Providing the token locally

```bash
export INTERNAL_DOCS_TOKEN="your-token-here"
make html
```

### Providing the token in GitHub Actions

Store the token as a repository or organization secret, then pass it
to the build step as an environment variable:

```yaml
jobs:
  build-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build docs
        env:
          INTERNAL_DOCS_TOKEN: ${{ secrets.INTERNAL_DOCS_TOKEN }}
        run: make html
```

The token only needs read access to the built `searchindex.js`
artifact — scope it as narrowly as your hosting setup allows rather
than granting broader repository or org access.

### Failure behavior

- If `auth_token_env` is set but the environment variable is missing,
  the build fails immediately with a clear error, rather than
  attempting an unauthenticated request.
- If the remote server responds `401`/`403`, the build fails with an
  error identifying the project and the environment variable to check.
- By default, a failed private project **fails the whole build**,
  since a bad or missing token should not silently produce an
  incomplete search index. To instead skip that project and continue
  the build with a warning, mark it as optional:

  ```python
  {
      "name": "Internal Kernel Docs",
      "base_url": "https://docs.internal.example.com/kernel",
      "searchindex_url":
          "https://docs.internal.example.com/kernel/searchindex.js",
      "auth_token_env": "INTERNAL_DOCS_TOKEN",
      "required": False,
  }
  ```

### Notes and caveats

- A valid token only proves *authorization*. If the internal site is
  also only reachable over a VPN or private network, the machine
  running `sphinx-build` (local machine or CI runner) must be able to
  reach it too — a token does not grant network reachability.
- This mechanism authenticates the **build-time fetch** of
  `searchindex.js` only. If your theme's client-side JavaScript
  additionally fetches remote pages at search time (e.g. to build
  result snippets), that request runs in the visiting user's browser
  and is unrelated to `auth_token_env` — it succeeds or fails based on
  whether that user's browser already has access to the internal site.

---

## Configuration reference

### `unified_search_projects`

Type:

```python
list[dict]
```

Default:

```python
[]
```

Example:

```python
unified_search_projects = [
    {
        "name": "Juju",
        "base_url": "https://juju.is/docs",
        "searchindex_url":
            "https://juju.is/docs/searchindex.js",
    }
]
```

Each dictionary accepts the following keys:

| Key | Required | Description |
|------|----------|-------------|
| `name` | Yes | Human-readable project name |
| `base_url` | Yes | Root URL of the documentation |
| `searchindex_url` | Yes | URL of the remote `searchindex.js` |
| `auth_token_env` | No | Name of the environment variable holding a bearer token. If set, its value is sent as a request header when fetching `searchindex_url`. See [Private / internal projects](#private--internal-projects). |
| `auth_header` | No | Header name to send the token in. Default: `Authorization` |
| `auth_scheme` | No | Scheme prefix for the token value, e.g. `Bearer`. Default: `Bearer`. Set to `""` to send the raw token with no prefix. |
| `required` | No | If `True` (default), a failed fetch for this project fails the whole build. If `False`, a failed fetch is logged as a warning and the project is skipped. |

---

## Compatibility

- Sphinx 7+
- HTML builders only

---

## Limitations

- All projects should use compatible Sphinx versions.
- Search ranking uses the standard Sphinx ranking algorithm.
- Very large federations may increase build time.
- Object inventory (`objects.inv`) data is not merged.
- `auth_token_env` authenticates the build-time fetch of a project's
  `searchindex.js` only — it does not grant network reachability to
  VPN- or SSO-gated sites, and does not authenticate any client-side
  requests a theme may make in the visitor's browser.

---

## License

Apache-2.0
