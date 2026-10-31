# sphinx-unified-search

![Status: Work in Progress][status-badge]
![Feedback Welcome][feedback-badge]
![Config may change][config-badge]
![PyPI release][release-badge]

> **⚠️ Work in progress.** This project is under active development.
> Configuration options and behavior may change without notice. It has not
> been fully tested for production use, but early testers and feedback are
> very welcome. Please [open an issue][issues] if you hit problems or have
> suggestions.

## Cross-project search for Sphinx documentation

`sphinx-unified-search` is a Sphinx extension that lets you search across
multiple Sphinx documentation sites from a single search box. It works by
merging remote `searchindex.js` files into your project's local search index
at build time.

The standard [Sphinx] search UI is preserved: no new search box, no external
service, and no per-query cost.

## Features

- Builds on the standard Sphinx search page. Supported and tested with
  [Sphinx Stack 2.0][sphinx-stack-2]; other themes may need changes (see
  [Compatibility](#compatibility))
- No JavaScript customization required on supported setups
- No external search service required
- Preserves the standard Sphinx search UI
- Remote search results link directly to their original documentation pages,
  keeping traffic on the source sites
- Supports any number of remote Sphinx projects
- Supports token-authenticated fetching for private/internal projects

## Who might find this useful

- **Upstream / downstream content**- if your (product and) docs build on top of
  an upstream project maintained elsewhere, your users can search the upstream
  or related (Sphinx) docs without leaving your site.
- **Multi-product teams** - separate Sphinx sites that share an audience, where
  users shouldn’t have to know which exact site to search. Or products that are
  part of a larger ecosystem.
- **Internal platform teams** - private doc sets that (may) need to be
  searchable alongside public ones without setting up new infrastructure.

---

## Compatibility

> **Supported: Sphinx Stack 2.0.** `sphinx-unified-search` is currently
> developed and tested against documentation projects based on
> [Canonical's Sphinx Stack 2.0][sphinx-stack-2], which uses the Canonical
> Sphinx theme (loaded through the `canonical_sphinx` extension). On that setup
> the extension works without any extra changes.
>
> **Other themes and Sphinx Stack versions aren't tested or supported yet.**
> Search can fail, or the results page can look wrong, unless you add custom CSS
> or other changes.

| Your setup | Status |
| --- | --- |
| Sphinx Stack 2.0 (Canonical Sphinx theme) | Supported. Works without changes. |
| Other Sphinx Stack versions, including 3.0 and its default Ulwazi theme | Not tested. May need changes. |
| Any other Sphinx theme | Not tested. May fail, or need custom CSS. |

### Why other themes can differ

The extension doesn't replace Sphinx's search. It adjusts the standard search
results page in the browser, so it depends on the following. A theme that
changes any of these can break search, or part of it:

- **Standard search page markup.** Results are read from the `ul.search` list
  (one `li` per result, each with a link and a `.context` paragraph), and the
  extension waits for `#search-results .search-summary` to know that the search
  has finished. Themes that replace the search page or its JavaScript with
  their own search UI aren't compatible.
- **Sphinx's `Scorer` object.** The extension extends `window.Scorer`, which
  comes from Sphinx's stock search scripts.
- **Theme colors for the project filter.** The filter chips use the Canonical
  Sphinx theme's CSS variables (`--color-brand-primary` and similar), with
  plain fallbacks. In other themes the chips can look wrong or have poor
  contrast.
- **Remote URLs in `dirhtml` style.** Links to remote results are built as
  `<base_url><docname>/`, as the Sphinx Stack's `dirhtml` builds produce.
  Remote projects built with the default `html` builder (`page.html`) get
  incorrect result links.
- **A `<main>` element on remote pages.** Result previews take their text from
  the remote page's `<main>` (or `[role="main"]`) element, and fall back to the
  whole `<body>`, which can include navigation text.
- **HTML builders only.** Other builders (such as `latex` or `epub`) are
  skipped.

### If you use a different theme

1. Build the docs, open the search page, and check the browser console. Messages
   starting with `[unified-search]` show what the extension found.
2. If the filter chips look wrong (they only appear when
   `unified_search_project_filter = True`), override their styles in your own
   CSS file. The classes are `.unified-search-filter`, `.unified-search-filter__label`,
   `.unified-search-chip`, `.unified-search-chip__count`, and
   `.unified-search-chip[aria-pressed="true"]` for the selected state.
3. [Open an issue][issues] with your theme name and version, and what failed.

For example, add a stylesheet to your docs:

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
`body` prefix gives your rules higher priority, so they win over the extension's
defaults.

---

## How to use the extension

Installing and configuring `sphinx-unified-search` is straightforward. If you
also want to include a private [Read the Docs (RTD)] project in the unified
search results, complete the extra setup below first.

### Configure access to private documentation projects

If you want to include a private RTD project in the unified search, you must
create an HTTP header token that can be used to download its `searchindex.js`.

For each private project:

1. Open the project's Read the Docs settings.
1. Go to "Sharing" and "Add share".
1. Select "HTTP header token" for the "Access type", and a suitable expiry
   date.
1. Select "Allow access to all versions?" if you intend to use `searchindex.js`
   for all versions of the docs set. Otherwise, unselect that option and add the
   versions that will be used by `sphinx-unified-search`.

Copy the generated token and store it as a secret environment variable in the
RTD project that is _building_ the unified search.

For example, if "PROJECT B" wants to the `searchindex.js` from "PROJECT A" to
its search results, generate the HTTP header token in PROJECT A, and add that as
an environment variable in PROJECT B
(e.g. `PROJECTA_DOCS_TOKEN=<generated HTTP header token>`).

### Install the extension

Add `sphinx-unified-search` to the `requirements.txt` file in your Sphinx
project:

```text
sphinx-unified-search
```

### Enable the extension

Add `sphinx_unified_search` to the `extensions` list in `conf.py`:

```python
extensions = [
    "sphinx_unified_search",
]
```

### Configure projects to index for unified search

Configure the list of documentation projects whose search indexes should be
included in the unified search.

For each project, specify:

- `name`: A unique identifier for the project. For search results from
  projects other than the host project, this value is appended to the page
  title in the search results.
- `base_url`: The base URL of the documentation, used as the destination when
  a user clicks a search result.
- `searchindex_url`: The URL of the project's `searchindex.js`.

For private projects, also specify:

- `auth_token_env`: The name of the environment variable containing the RTD HTTP
  header token.
- `auth_scheme`: The authorization scheme to use in the HTTP `Authorization`
  header. For RTD HTTP header tokens, set this to `"Token"`.

```python
unified_search_projects = [
    # Public project - no auth needed, plain HTTP fetch
    {
        "name": "Landscape",
        "base_url": "https://ubuntu.com/landscape/docs/",
        "searchindex_url": "https://ubuntu.com/landscape/docs/searchindex.js",
    },

    # Private project - token-gated fetch
    {
        "name": "ProjectA",
        "base_url": "https://documentation.ubuntu.com/projecta/",
        "searchindex_url": "https://documentation.ubuntu.com/projecta/searchindex.js",
        "auth_token_env": "PROJECTA_DOCS_TOKEN",
        "auth_scheme": "Token",
    },
]
```

### Build the docs locally

When building the documentation locally, you must set the environment variables
referenced by the `auth_token_env` entries in `unified_search_projects`.

For example, if your remote project uses this config:

```python
{
    "auth_token_env": "PROJECTA_DOCS_TOKEN",
    ...
}
```

Export the corresponding token before building:

```shell
export PROJECTA_DOCS_TOKEN="<token>"
```

Repeat this for each private project included in `unified_search_projects` set.

Once the required environment variables are set, build or serve the
documentation as usual with `make html` or `make run`.

### Filter search results by project

Add project filter chips to the search results page so visitors can narrow
the results to one or more projects:

```python
unified_search_project_filter = True

# Optional: label for this project's own results in the filter.
# Defaults to Sphinx's `project` setting.
unified_search_local_project_name = "My Docs"
```

When the search has finished, a "Filter by project" row appears above the
results, with one chip per project that has results and the number of results
next to it. Select one or more chips to show only those projects; select
"All" (or deselect every chip) to show everything again. The filter only hides
rows: results are not removed, and previews are still loaded for all of them.
The selection is stored in the URL (`?q=term&project=ProjectA`), so it survives
a reload and can be shared. The filter is off by default, and isn't shown when
results come from only one project.

### Fetch remote indexes once per live-preview session

By default, every build downloads each remote `searchindex.js` again. With
[sphinx-autobuild] (`make run`), that means a fresh download of every remote
index on each rebuild, which slows down the edit-preview loop.

Set the following in `conf.py` to download each remote index only once per
`sphinx-autobuild` session and reuse it for later rebuilds:

```python
unified_search_cache_remote_indexes = True
```

The cache is scoped to the running `sphinx-autobuild` process and stored under
the Sphinx doctree directory, so it is discarded when you restart the preview.
Regular builds (`make html`, Read the Docs, CI) are unaffected and always fetch
fresh indexes. Only successfully parsed downloads are cached, and the cache key
covers the index URL and its resolved authentication, so a changed token or
header forces a new download. Tokens themselves are never written to disk.

## Some things to note

A few behaviors and limitations to be aware of before you publish a unified
search, especially if you include private projects.

### Private docs: result previews

On the search results page, each result shows a short preview of the matching
content, fetched from the remote project’s page. This request is made
client-side in the visitor’s browser, so it can’t use the build-time token, and
it is subject to the browser’s same-origin policy.

The preview loads only if the remote page is same-origin or allows cross-origin
requests via CORS headers. Otherwise, the extension shows a placeholder message
instead. The search results and their links work normally in all cases. For
local builds, see [Preview proxy for local builds](#preview-proxy-for-local-builds-optional).

### Preview proxy for local builds (optional)

When you preview your docs locally, for example at `http://127.0.0.1:8000`,
result previews usually fail to load. The browser fetches each preview straight
from the remote site, and that cross-origin request is blocked unless the remote
site allows it with CORS headers. Previews from private projects fail for a
second reason: the browser has no login for them, so the site returns a login
page.

For local development only, you can run a small proxy on your machine. The
browser asks the proxy for the remote page, the proxy fetches it for you (with
your cookies, if the project is private), and the proxy answers with the CORS
header the browser needs:

```text
browser (127.0.0.1:8000) --> proxy (127.0.0.1:8010) --> remote docs site
                         <-- page + CORS header   <--
```

The proxy is optional and does nothing unless you both set
`unified_search_preview_proxy` in `conf.py` and start the proxy yourself. To
turn it off, remove the setting or don't start the proxy. It has no effect on
published sites. For what it does and doesn't change there, see
[Private docs: result previews](#private-docs-result-previews).

#### Set up the proxy

**Step 1. Enable it in `conf.py`.**

```python
import os

# Local builds only. Read the Docs sets READTHEDOCS, so the setting is skipped
# there. The browser also ignores it unless the docs are viewed from localhost.
if not os.environ.get("READTHEDOCS"):
    unified_search_preview_proxy = "http://127.0.0.1:8010/"
```

The address is where the proxy listens. The proxy reads it from `conf.py`, so
you configure it only once.

**Step 2. Add cookies for private projects (skip this for public projects).**

In `unified_search_projects`, add `preview_cookie_env` to each private project.
This is the _name_ of an environment variable, not the cookie itself:

```python
unified_search_projects = [
    # Public project: nothing to add. The proxy fetches it without a cookie.
    {
        "name": "Kernel",
        "base_url": "https://ubuntu.com/kernel/docs/",
        "searchindex_url": "https://ubuntu.com/kernel/docs/searchindex.js",
    },

    # Private project
    {
        "name": "ProjectA",
        "base_url": "https://documentation.ubuntu.com/projecta/",
        "searchindex_url": "https://documentation.ubuntu.com/projecta/searchindex.js",
        "auth_token_env": "PROJECTA_DOCS_TOKEN",   # build time: download searchindex.js
        "auth_scheme": "Token",
        "preview_cookie_env": "PROJECTA_COOKIE",   # local previews: cookie variable name
    },
]
```

Put the cookie value in a file that isn't committed, for example
`_dev/proxy.env`, and add that file to your `.gitignore`. Use single quotes,
because cookies contain `;`:

```shell
PROJECTA_COOKIE='sessionid=...; csrftoken=...'
```

To get the value, sign in to the private docs in your browser, open the
developer tools, select the Network tab, click a page request, and copy its
`Cookie` request header. Treat it like a password. Cookies expire, so refresh
the value when previews show a login page again.

**Step 3. Start the docs and the proxy in two terminals.**

Run both from the directory that contains `conf.py`.

Terminal 1, the docs:

```shell
make run
```

Terminal 2, the proxy:

```shell
set -a; . _dev/proxy.env; set +a    # load the cookie variables (private projects only)
sphinx-unified-search-proxy
```

If the command isn't found, run it from your docs virtual environment, for
example `.venv/bin/sphinx-unified-search-proxy`. Leave both terminals open. You
can start them in either order. The proxy prints the address it listens on,
and one line per project showing which cookie variables it will use. It
warns about variables that aren't set, and it never prints the cookie values:

```text
unified-search preview proxy on http://127.0.0.1:8010/
  https://ubuntu.com/kernel/docs/  (Kernel; no cookie)
  https://documentation.ubuntu.com/projecta/  (ProjectA; cookie from $PROJECTA_COOKIE)
```

**Step 4. Check that it works.**

Open the search page, for example `http://127.0.0.1:8000/search/?q=kernel`, and
hard-refresh with Ctrl+Shift+R so the browser picks up the new setting. Remote
results now show previews. For each one, the proxy prints a line such as
`[200] https://ubuntu.com/kernel/docs/...`.

If you changed `conf.py` while `make run` was already running, restart
`make run` first.

#### Start both with one command

Add a target like this to the Makefile where you keep your own targets (not one
that the Sphinx Stack overwrites when you update), and add `run-with-proxy` to
`.PHONY`. It uses variables defined by the Sphinx Stack's Makefile:

```make
run-with-proxy: install
	@set -a; test ! -f $(DEV_DIR)/proxy.env || . $(DEV_DIR)/proxy.env; set +a; \
	$(DOCS_VENVDIR)/bin/sphinx-unified-search-proxy --conf-dir "$(DOCS_SOURCEDIR)" & \
	PROXY=$$!; trap 'kill $$PROXY 2>/dev/null' EXIT; \
	$(MAKE) --no-print-directory run
```

`make run-with-proxy` starts the proxy, runs `make run`, and stops the proxy
when you press Ctrl+C.

#### Cookies for private projects

Each project has its own cookies, and a project's cookies are only ever sent to
that project. Because `preview_cookie_env` only names environment variables, no
secrets end up in `conf.py`. It accepts three forms:

```python
# 1. One variable holding the whole Cookie header value
"preview_cookie_env": "PROJECTA_COOKIE",            # PROJECTA_COOKIE="sessionid=abc; csrftoken=def"

# 2. Several variables, each holding a Cookie header value. They're joined
#    with "; ". Variables that are unset are skipped, with a warning at startup.
"preview_cookie_env": ["PROJECTA_SESSION", "PROJECTA_EXTRA"],

# 3. One variable per cookie, each holding only that cookie's value
"preview_cookie_env": {"sessionid": "PROJECTA_SESSION", "csrftoken": "PROJECTA_CSRF"},
```

A pasted `Cookie:` prefix in a value is ignored.

For several private projects on different domains, give each project its own
`preview_cookie_env` with its own variable names. The proxy picks the project
whose `base_url` matches each page.

#### What happens when a cookie variable isn't set

- **Locally:** the proxy still starts, and prints a warning for each variable
  that isn't set. For that project it sends no cookie, so the site returns its
  login page, and the preview shows the login text (for example "Log in to view
  this documentation"). Public projects and the build aren't affected.
- **On Read the Docs or in CI:** nothing changes. The proxy doesn't run there,
  and the extension ignores `preview_cookie_env` during the build. Only
  `auth_token_env` is read at build time, and that variable must be set.

#### Troubleshooting

| What you see | Likely cause and fix |
| --- | --- |
| Previews fail, and the proxy terminal prints nothing | `unified_search_preview_proxy` isn't set, the page wasn't hard-refreshed, or you opened the docs from a non-localhost address. The proxy is only used on `localhost`, `127.0.0.1` and `[::1]`. |
| Browser console shows a connection error to `127.0.0.1:8010` | The proxy isn't running, or it's on a different port than the setting. |
| Proxy prints `[blocked] <url>` | The URL isn't under a project's `base_url`. Check that `base_url` matches the site and path, including `https`. |
| Preview shows login text for a private project | The cookie is missing or expired. Check the startup line for `WARNING not set`, then refresh the cookie value. |
| Proxy prints `[403]` or `[401]` from the remote site | The remote site rejected the cookie. Copy a fresh one. |
| Proxy prints `[502]` | The proxy couldn't reach the remote site. Check your network or VPN. |
| Proxy replies "origin not allowed" | The docs are served from a non-loopback address. Start the proxy with `--allow-origin <origin>`. |
| `error: no conf.py in ...` | Run the proxy from the directory that contains `conf.py`, or pass `--conf-dir`. |
| `cannot listen on 127.0.0.1:8010` | The port is in use. Change the port in `unified_search_preview_proxy`. |
| `refusing to listen on ...` | The proxy only listens on loopback. Use `127.0.0.1` or `localhost`. |

#### Command-line options

- `--conf-dir DIR`: Directory containing `conf.py` (default: current directory).
- `--no-conf`: Don't read `conf.py`; use only `--allow`.
- `--listen URL`: Address to listen on (default: `unified_search_preview_proxy`,
  else `http://127.0.0.1:8010/`).
- `--allow URL[=ENV_VAR]`: Also proxy a site that's not in
  `unified_search_projects`. To send cookies, append `=ENV_VAR` (or several,
  separated by commas) after the trailing slash, for example
  `https://example.com/docs/=DOCS_COOKIE` or
  `https://example.com/docs/=DOCS_SESSION,DOCS_CSRF`.
- `--allow-origin ORIGIN`: Also accept requests from this non-loopback web
  origin.

#### Safety measures

- The proxy only listens on loopback and refuses other addresses.
- It only fetches pages under the `base_url` of a configured project (or an
  `--allow` URL), so it can't be used to fetch arbitrary sites.
- It only answers requests from pages served from loopback addresses, and
  checks the `Host` header. A website you happen to have open can't use the
  proxy to read private docs with your cookie.
- A cookie is only sent to the project it belongs to, and is dropped if the
  site redirects to a different origin.

Don't commit your cookies, and don't run the proxy on a shared or public
machine. It's a development tool, not a way to make previews work on a
deployed site.

### Beware of headings

If you add a private project as a remote of a public docs set, page titles and
headings from the private project will appear in the public search results, even
though the page _content_ itself won't load. Don't include private projects
whose titles or headings contain confidential information.

### Build the docs in CI (GitHub Actions)

Adding a secret to a repository doesn't automatically expose it to every
workflow run. Each job that needs it must reference it explicitly.

This matters most when the docs build runs in a reusable workflow (for example, `uses: ./.github/workflows/build-docs.yml`). Secrets aren't inherited by the
called workflow by default. A build that works locally with an exported token
can therefore fail in CI, or silently skip the private index.

To fix this, pass the secret through in the calling workflow:

```yaml
jobs:
  build-docs:
    uses: ./.github/workflows/build-docs.yml
    secrets:
      PROJECTA_DOCS_TOKEN: ${{ secrets.PROJECTA_DOCS_TOKEN }}
    # or, to pass all secrets: `secrets: inherit`
```

The reusable workflow must also declare the secret under
`on.workflow_call.secrets`, and the build step should expose it as an
environment variable named in `auth_token_env`.


[status-badge]: https://img.shields.io/badge/status-work%20in%20progress-yellow
[feedback-badge]: https://img.shields.io/badge/feedback-welcome-blue
[config-badge]: https://img.shields.io/badge/config-subject%20to%20change-orange
[release-badge]: https://img.shields.io/pypi/v/sphinx-unified-search
[issues]: https://github.com/canonical/sphinx-unified-search/issues
[Sphinx]: https://www.sphinx-doc.org/en/master/
[sphinx-stack-2]: https://github.com/canonical/sphinx-stack/releases#release-2.0
[Read the Docs (RTD)]: https://about.readthedocs.com/
[sphinx-autobuild]: https://github.com/sphinx-doc/sphinx-autobuild