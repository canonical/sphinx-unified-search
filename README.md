# sphinx-unified-search

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

---

## License

Apache-2.0