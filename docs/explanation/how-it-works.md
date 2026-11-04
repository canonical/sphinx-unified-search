# How unified search works

`sphinx-unified-search` lets visitors search several Sphinx sites from one
search box, without a separate search service.

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
reads the result list, adds the project filter if enabled, and loads a short
preview for each remote result by fetching the remote page.

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


The extension doesn't replace Sphinx's search. It hooks into the standard
search page, so it relies on that page's markup, on Sphinx's `Scorer`, and on
a few conventions of the remote sites (`dirhtml` URLs, a `<main>` element).
It also styles the filter using Canonical Sphinx theme colors. A theme that
replaces the search page or its JavaScript with its own search UI isn't
compatible. The specific dependencies are listed in the
{ref}`compatibility reference <ref-compatibility-what-the-extension-depends-on>`,
and {doc}`Use a different theme </how-to/use-a-different-theme>` shows how to
diagnose and fix issues.
