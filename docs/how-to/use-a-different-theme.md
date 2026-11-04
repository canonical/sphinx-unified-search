# How to use a different theme

`sphinx-unified-search` is tested with Sphinx Stack 2.0 (Canonical Sphinx
theme). Other themes and Sphinx Stack versions aren't tested or supported yet.
Search can fail, or the results page can look wrong, unless you make changes.
This guide shows how to check what's wrong and fix the most common issue,
the look of the project filter.

To understand what the extension depends on, see
{doc}`Compatibility </reference/compatibility>` and
{doc}`How it works </explanation/how-it-works>`.

## Check what the extension found

1. Build the docs and open the search page.
1. Check the browser console. Messages starting with `[unified-search]` show
   what the extension found.

## Restyle the project filter

The filter chips only appear when `unified_search_project_filter = True`. If
they look wrong in your theme, override their styles in your own CSS file.

Add a stylesheet to your docs:

```python
# conf.py
html_static_path = ["_static"]
html_css_files = ["unified-search-custom.css"]
```

```css
/* _static/unified-search-custom.css */
body .unified-search-chip {
  border: 1px solid #888;
  background: transparent;
  color: inherit;
}

body .unified-search-chip[aria-pressed="true"] {
  background: #0e8420;
  border-color: #0e8420;
  color: #fff;
}
```

The extension adds its own stylesheet to the search page after yours. The
`body` prefix gives your rules higher priority, so they win over the
extension's defaults.

The available classes are listed in the
{ref}`compatibility reference <ref-compatibility-css-classes>`.

## Report what failed

[Open an issue](https://github.com/canonical/sphinx-unified-search/issues)
with your theme name and version, and what failed.
