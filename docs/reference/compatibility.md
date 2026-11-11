# Compatibility

This page lists supported setups and the search page, styling, and remote
site requirements for `sphinx-unified-search`.

## Support matrix

```{list-table}
:header-rows: 1

* - Your setup
  - Status
* - Sphinx Stack 2.0 (Canonical Sphinx theme)
  - Supported. Works without changes.
* - Sphinx Stack 3.0 (Ulwazi theme)
  - Supported. Set `unified_search_theme = "ulwazi"`. See
    {ref}`the Ulwazi theme <ref-compatibility-ulwazi>`.
* - Other Sphinx Stack versions
  - Not tested. May need changes.
* - Any other Sphinx theme
  - Not tested. May fail, or need custom CSS.
```

`sphinx-unified-search` is developed and tested against documentation projects
based on [Canonical's Sphinx Stack 2.0], which uses the Canonical Sphinx theme
(loaded through the `canonical_sphinx` extension), and against Sphinx Stack
3.0 with the Ulwazi theme.

## What the extension depends on

(ref-compatibility-what-the-extension-depends-on)=

A theme that changes any of these can break search, or part of it. For the
reasoning, see
{ref}`How it works <exp-how-it-works-why-other-themes-can-differ>`.

```{list-table}
:header-rows: 1

* - Dependency
  - Details
* - Standard search page markup
  - Results are the direct children of the `ul.search` list (one `li` per
    result). Each result has a title link and a `.context` paragraph as direct
    children. Links or lists nested inside a result, such as Ulwazi's
    breadcrumbs, aren't treated as results. The project filter rebuilds as
    results appear, so it doesn't depend on a "search finished" summary.
* - Sphinx's `Scorer` object
  - The extension extends `window.Scorer`, which comes from Sphinx's stock
    search scripts.
* - Theme colors for the project filter
  - Chips use the Canonical Sphinx theme's CSS variables
    (`--color-brand-primary` and similar), with plain fallbacks. With
    `unified_search_theme = "ulwazi"`, chips use fixed colors from the Ulwazi
    stylesheet instead.
* - `dirhtml` URLs on remote projects
  - Links to remote results are built as `<base_url><docname>/`. Remote
    projects built with the default `html` builder (`page.html`) get
    incorrect result links.
* - `<main>` element on remote pages
  - Previews take their text from `<main>` (or `[role="main"]`), falling back
    to the whole `<body>`, which can include navigation text.
* - HTML builders only
  - Other builders (such as `latex` or `epub`) are skipped.
```

## The Ulwazi theme

(ref-compatibility-ulwazi)=

Set `unified_search_theme = "ulwazi"` in `conf.py` to enable the Ulwazi
integration. It adds two files to the search page, after the default scripts
and styles:

```{list-table}
:header-rows: 1

* - File
  - Purpose
* - `unified-search-ulwazi.js`
  - Tidies each result's breadcrumbs: removes crumbs that have no remote page,
    removes the project prefix from crumb labels, and keeps the snippet
    directly under the title.
* - `unified-search-ulwazi.css`
  - Styles the filter chips and hides filtered results and unmapped crumbs. It
    leaves result typography, spacing, and colors to Ulwazi's own
    `search.css`.
```

The core script (`unified-search.js`) rewrites remote links in both the result
title and the breadcrumbs (`.search-breadcrumb-item a`), and keeps any
`#fragment` from the original link.

## CSS classes

(ref-compatibility-css-classes)=

Classes for the project filter (shown when `conf.py` sets
`unified_search_project_filter = True`):

```{list-table}
:header-rows: 1

* - Selector
  - Element
* - `.unified-search-filter`
  - Filter row container
* - `.unified-search-filter__label`
  - "Filter by project" label
* - `.unified-search-chip`
  - A project chip
* - `.unified-search-chip__count`
  - Result count inside a chip
* - `.unified-search-chip[aria-pressed="true"]`
  - A selected chip
```

## Console messages

Messages prefixed with `[unified-search]` are written to the browser console
and show what the extension found on the page.

% LINKS

[Canonical's Sphinx Stack 2.0]: https://github.com/canonical/sphinx-stack/releases#release-2.0