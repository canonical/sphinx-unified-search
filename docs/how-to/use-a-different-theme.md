# How to use a different theme

`sphinx-unified-search` is tested with two setups:

- Sphinx Stack 2.0 (Canonical Sphinx theme), the default integration.
- Sphinx Stack 3.0 with the Ulwazi theme, which you enable with
  `unified_search_theme`.

Other themes and Sphinx Stack versions aren't tested or supported yet. Search
can fail, or the results page can look wrong, unless you make changes.

This guide shows how to switch to the Ulwazi integration, check what's wrong,
and fix the most common issue, the look of the (optional) project filter.

```{seealso}
- To check a theme's integration requirements, see the
{doc}`compatibility reference </reference/compatibility>`.
- For the reasons behind the extension's compatibility requirements, see
{doc}`How unified search works </explanation/how-it-works>`.
- To enable or configure the project filter, see
{doc}`Configure unified search </how-to/configure-unified-search>`.
```

## Use the Ulwazi theme

Ulwazi renders a breadcrumb trail inside each search result. Without the
Ulwazi integration, remote results can have broken links or snippets, and the
results can look different from Ulwazi's own.

Add this to `conf.py`:

```{code-block} python
unified_search_theme = "ulwazi"
```

The extension doesn't read `html_theme`, so this setting is required even when
your project already uses Ulwazi. Rebuild the docs and search for a term that
appears in a remote project. Remote results should link to the remote site,
including their breadcrumbs, and look like local results.

## Check what the extension found

1. Build the docs and open the search page.
1. Check the browser console. Messages starting with `[unified-search]` show
   what the extension found.

## Restyle the project filter

The filter chips only appear when `unified_search_project_filter = True`. If
they look wrong in your theme, override their styles in your own CSS file. With
`unified_search_theme = "ulwazi"`, the extension's Ulwazi stylesheet sets the
chip colors (Ubuntu orange for the selected chip) with `!important`, so your
rules need `!important` as well.

Add a stylesheet to your docs:

```{code-block} python
# conf.py
html_static_path = ["_static"]
html_css_files = ["unified-search-custom.css"]
```

```{code-block} css
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
