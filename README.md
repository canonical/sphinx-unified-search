# sphinx-unified-search

![Status: Work in Progress][status-badge]
![Feedback Welcome][feedback-badge]
![Config may change][config-badge]
![PyPI release][release-badge]

> **Work in progress.** This project is under active development. Configuration
> options and behavior may change without notice. It has not been fully tested
> for production use, but early testers and feedback are very welcome. Please
> [open an issue][issues] if you hit problems or have suggestions.

## Cross-project search for Sphinx documentation

`sphinx-unified-search` is a Sphinx extension that lets you search across
multiple Sphinx documentation sites from a single search box. It works by
merging remote `searchindex.js` files into your project's local search index
at build time.

The standard [Sphinx] search UI is preserved: no new search box, no external
service, and no per-query cost.

## Features

- Builds on the standard Sphinx search page. Supported and tested with
  Sphinx Stack 2.0 (the default integration) and Sphinx Stack 3.0 with the
  Ulwazi theme (opt in with `unified_search_theme = "ulwazi"`)
- No JavaScript customization required on supported setups
- No external search service required
- Preserves the standard Sphinx search UI
- Remote search results link directly to their original documentation pages,
  keeping traffic on the source sites
- Supports any number of remote Sphinx projects
- Supports token-authenticated fetching for private/internal projects

## Who might find this useful

- **Upstream / downstream content** - if your product and documentation build
  on an upstream project maintained elsewhere, your users can search the
  upstream or related Sphinx documentation without leaving your site.
- **Multi-product teams or solutions** - separate Sphinx sites that share an
  audience, where users shouldn't have to know which exact site to search, or
  products that are part of a larger ecosystem.
- **Internal platform teams** - private documentation sets that need to be
  searchable alongside public ones without setting up new infrastructure.

For installation, configuration, compatibility, and usage details, see the
[Sphinx Unified Search documentation](https://canonical-sphinx-unified-search.readthedocs-hosted.com/).

[status-badge]: https://img.shields.io/badge/status-work%20in%20progress-yellow
[feedback-badge]: https://img.shields.io/badge/feedback-welcome-blue
[config-badge]: https://img.shields.io/badge/config-subject%20to%20change-orange
[release-badge]: https://img.shields.io/pypi/v/sphinx-unified-search
[issues]: https://github.com/canonical/sphinx-unified-search/issues
[Sphinx]: https://www.sphinx-doc.org/en/master/
