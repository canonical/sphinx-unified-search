# How Sphinx unified search works

`sphinx-unified-search` lets users search several Sphinx sites from one
search box, without a separate search service.

```{figure} /_assets/sphinx-unified-search-how-it-works.png
:alt: Diagram showing how local and remote search indexes feed into browser search results. Unified search at build time and in the browser.
```

## Build time: merging indexes

Every Sphinx HTML build produces a `searchindex.js` file that powers the
site's search page. At build time, the extension downloads the
`searchindex.js` of each project in `unified_search_projects` and merges it
into your project's local index. Other builders (such as `latex` or `epub`)
are skipped.

Because the merge happens at build time, there's no external search service
and no per-query cost. The standard Sphinx search page is preserved, and
results from remote projects link directly to their original pages, so
traffic stays on the source sites.

During `sphinx-autobuild`, re-downloading every remote index on each rebuild
is slow. With `unified_search_cache_remote_indexes`, each index is fetched
once per session. The cache is deliberately scoped to the running process so
that normal builds, Read the Docs and CI always get fresh indexes. Tokens are
never written to disk.

## Browser time: results and previews

The extension adjusts the standard search results page in the browser. It
reads the result list, adds the project filter if enabled (updating its chips
as results load), and loads a short preview for each remote result by fetching
the remote page.

## Private projects and previews

(exp-how-it-works-private-projects-and-previews)=

Private projects involve two separate kinds of access:

- **Build time.** The extension downloads the private `searchindex.js` using
  an HTTP header token (`auth_token_env`). This happens on the machine doing
  the build, so it can use secrets.
- **Browser time.** The preview is fetched by the visitor's browser. The
  build-time token isn't available there, and the request is subject to the
  browser's same-origin policy.

The preview loads only if the remote page is same-origin or allows
cross-origin requests with CORS headers. Otherwise the extension shows a
placeholder message. The search results and their links work normally in all
cases.

For local builds, the {doc}`preview proxy </explanation/preview-proxy>` works around this
during development.

### Beware of headings

If you add a private project as a remote of a public docs set, page titles and
headings from the private project appear in the public search results, even
though the page _content_ itself won't load. Don't include private projects
whose titles or headings contain confidential information.

## Why other themes can differ

(exp-how-it-works-why-other-themes-can-differ)=

The extension adds cross-project behavior to Sphinx's standard search page; it
doesn't provide a separate search page or search engine. As a result, it
depends on the markup and JavaScript that the standard page provides. It reads
results from Sphinx's `ul.search` list, treating only the direct children of
that list as results. Themes can add their own elements inside each result. For
example, Ulwazi adds a breadcrumb trail with its own links, which the extension
rewrites to point at the remote project but never counts as results. Search
results arrive gradually and themes can rewrite the summary line while they do,
so the project filter doesn't wait for a "finished" signal; it recounts and
rebuilds its chips whenever the results change. If a theme changes the result
list or its direct children, the extension may not be able to read the results
or build the filter. The extension also adds
its scoring behavior to `window.Scorer`, the interface used by Sphinx's search
scripts. If a theme replaces those scripts with a different search interface,
the extension's scoring behavior may not integrate with it.

Other dependencies affect only particular parts of the experience. The project
filter uses CSS variables from the Canonical Sphinx theme, so a different theme
can leave the filter chips with incorrect colors or poor contrast even when
search works. For Ulwazi, set `unified_search_theme = "ulwazi"` so the
extension loads its Ulwazi script and stylesheet; they keep remote results
visually consistent with the theme's own. Remote result links assume the `dirhtml` URL format
(`<base_url><docname>/`); if a remote project uses the default `html` builder,
its `page.html` URLs don't match that format. For previews, the extension reads
text from a remote page's `<main>` element (or `[role="main"]`). If neither is
present, it falls back to `<body>`, which can include navigation text.

These are separate integration points, so a theme or remote site's changes can
affect search, filter styling, links, or previews independently. The extension
also runs only with HTML builders; builders such as `latex` and `epub` are
skipped.

The {ref}`compatibility reference <ref-compatibility-what-the-extension-depends-on>`
lists each dependency. {doc}`Use a different theme </how-to/use-a-different-theme>`
shows how to diagnose and fix common issues.
