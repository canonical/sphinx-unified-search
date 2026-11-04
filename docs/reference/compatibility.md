# Compatibility reference

## Support matrix

| Your setup | Status |
| --- | --- |
| Sphinx Stack 2.0 (Canonical Sphinx theme) | Supported. Works without changes. |
| Other Sphinx Stack versions, including 3.0 and its default Ulwazi theme | Not tested. May need changes. |
| Any other Sphinx theme | Not tested. May fail, or need custom CSS. |

`sphinx-unified-search` is developed and tested against documentation projects
based on [Canonical's Sphinx Stack 2.0](https://github.com/canonical/sphinx-stack/releases#release-2.0),
which uses the Canonical Sphinx theme (loaded through the `canonical_sphinx`
extension).

## What the extension depends on

(ref-compatibility-what-the-extension-depends-on)=


A theme that changes any of these can break search, or part of it. For the
reasoning, see
{ref}`How it works <exp-how-it-works-why-other-themes-can-differ>`.

| Dependency | Details |
| --- | --- |
| Standard search page markup | Results are read from the `ul.search` list (one `li` per result, each with a link and a `.context` paragraph). The extension waits for `#search-results .search-summary` to know the search has finished. |
| Sphinx's `Scorer` object | The extension extends `window.Scorer`, which comes from Sphinx's stock search scripts. |
| Theme colors for the project filter | Chips use the Canonical Sphinx theme's CSS variables (`--color-brand-primary` and similar), with plain fallbacks. |
| `dirhtml` URLs on remote projects | Links to remote results are built as `<base_url><docname>/`. Remote projects built with the default `html` builder (`page.html`) get incorrect result links. |
| `<main>` element on remote pages | Previews take their text from `<main>` (or `[role="main"]`), falling back to the whole `<body>`, which can include navigation text. |
| HTML builders only | Other builders (such as `latex` or `epub`) are skipped. |

## CSS classes

(ref-compatibility-css-classes)=


Classes for the project filter (shown when
`unified_search_project_filter = True`):

| Selector | Element |
| --- | --- |
| `.unified-search-filter` | Filter row container |
| `.unified-search-filter__label` | "Filter by project" label |
| `.unified-search-chip` | A project chip |
| `.unified-search-chip__count` | Result count inside a chip |
| `.unified-search-chip[aria-pressed="true"]` | A selected chip |

## URL parameters

| Parameter | Description |
| --- | --- |
| `q` | The search query |
| `project` | Selected project filter, for example `?q=term&project=ProjectA` |

## Console messages

Messages prefixed with `[unified-search]` are written to the browser console
and show what the extension found on the page.
