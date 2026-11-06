# Compatibility

This page lists supported setups and the search page, styling, and remote
site requirements for `sphinx-unified-search`.

## Support matrix

```{list-table}
:header-rows: 1

* - Your setup
  - Status
* - Sphinx Stack 2.0 (Canonical Sphinx theme)
  - Supported out of the box (`unified_search_theme = "sphinx-stack-2.0"`).
* - Sphinx Stack 3.0
  - Supported out of the box (`unified_search_theme = "sphinx-stack-3.0"`).
* - Ulwazi theme
  - Supported out of the box (`unified_search_theme = "ulwazi"`).
* - Any other Sphinx theme
  - Not tested. May fail, or need custom CSS.
```

`sphinx-unified-search` is developed and tested against documentation projects
based on [Canonical's Sphinx Stack 2.0], which uses the Canonical Sphinx theme
(loaded through the `canonical_sphinx` extension), Sphinx Stack 3.0, and the
Ulwazi theme.

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
  - Results are read from the `ul.search` list (one `li` per result, each with
    a link and a `.context` paragraph). The extension waits for
    `#search-results .search-summary` to know the search has finished.
* - Sphinx's `Scorer` object
  - The extension extends `window.Scorer`, which comes from Sphinx's stock
    search scripts.
* - Theme colors for the project filter
  - Chips use the Canonical Sphinx theme's CSS variables
    (`--color-brand-primary` and similar), with plain fallbacks.
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