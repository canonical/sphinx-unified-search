# How to set up the preview proxy for local builds

When you preview your docs locally, for example at `http://127.0.0.1:8000`,
remote result previews may fail to load. Browsers block access to remote
responses unless allowed by Cross-Origin Resource Sharing (CORS) headers.
Private sites may also require a login.

This guide shows how to run an optional local proxy to load these previews,
including for private projects. It is for local development only and doesn't
change published sites.

For background, see {doc}`The preview proxy </explanation/preview-proxy>`.
For options, see the
{doc}`preview proxy CLI reference </reference/preview-proxy-cli>`.

## Set up the proxy

Configure the proxy address, add cookies if you need private project previews,
then start the docs and proxy and check that previews load.

### Step 1. Enable the proxy in `conf.py`

```{code-block} python
import os

# Local builds only. Read the Docs sets READTHEDOCS, so the setting is skipped
# there. The browser also ignores it unless the docs are viewed from localhost.
if not os.environ.get("READTHEDOCS"):
    unified_search_preview_proxy = "http://127.0.0.1:8010/"
```

The address is where the proxy listens and should be different from the address
serving your local docs / running live rebuilds. The proxy reads it from
`conf.py`, so you configure it only once.

### Step 2. Add cookies for private RTD projects

Skip this step if all your projects are public.

In `unified_search_projects`, add `preview_cookie_env` to each private project.
This is the _name_ of an environment variable, not the cookie itself:

```{code-block} python
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

Put the cookie value in a file that _is not_ committed, for example
`_dev/proxy.env`, and add that file to your `.gitignore`. Use single quotes,
because cookies contain `;`:

```{code-block} shell
PROJECTA_COOKIE='betasessionid=<value copied from browser>'
```

To get the value:

1. Sign in to the private docs in your browser.
1. Open the developer tools and select the Network / Storage tab.
1. Click a page request and copy its `Cookie` request header.

Treat it like a password. Cookies expire, so refresh the value when previews
show a login page again.

Each project has its own cookies, and a project's cookies are only ever sent
to that project. `preview_cookie_env` also accepts a list of variables or a
dict of one variable per cookie. See the
{ref}`configuration reference <ref-configuration-preview-cookie-env>`.

For several private projects on different domains, give each project its own
`preview_cookie_env` with its own variable names. The proxy picks the project
whose `base_url` matches each page.

### Step 3. Start the docs and the proxy in two separate terminals

Run both from the directory that contains `conf.py`.

Terminal 1, serve or build the docs:

```{code-block} shell
make run
```

Terminal 2, the proxy:

```{code-block} shell
set -a; . _dev/proxy.env; set +a    # load the cookie variables (private projects only)
sphinx-unified-search-proxy
```

If the command isn't found, run it from a virtual environment, for example
`.venv/bin/sphinx-unified-search-proxy`. Leave both terminals open. You can
start them in either order.

The proxy prints the address it listens on, and one line per project showing
which cookie variables it will use. It warns about variables that aren't set,
and it never prints the cookie values:

```{code-block} text
unified-search preview proxy on http://127.0.0.1:8010/
  https://ubuntu.com/kernel/docs/  (Kernel; no cookie)
  https://documentation.ubuntu.com/projecta/  (ProjectA; cookie from $PROJECTA_COOKIE)
```

### Step 4. Verify that the proxy works

Open the search page, for example `http://127.0.0.1:8000/search/?q=kernel`,
and hard-refresh with `Ctrl+Shift+R` so the browser picks up the new setting.
Remote results now show previews. For each one, the proxy prints a line such
as `[200] https://ubuntu.com/kernel/docs/...`.

If you changed `conf.py` while `make run` was already running, restart
`make run` first.

## Start both with one command (optional)

You can keep running the docs and proxy in separate terminals. If you prefer
to start both with one command, you can add a Makefile target instead.

Add the target below to the Makefile and add `run-with-proxy` to `.PHONY`. It
uses variables defined by the Sphinx Stack's Makefile:

```{code-block} make
run-with-proxy: install
	@set -a; test ! -f $(DEV_DIR)/proxy.env || . $(DEV_DIR)/proxy.env; set +a; \
	$(DOCS_VENVDIR)/bin/sphinx-unified-search-proxy --conf-dir "$(DOCS_SOURCEDIR)" & \
	PROXY=$$!; trap 'kill $$PROXY 2>/dev/null' EXIT; \
	$(MAKE) --no-print-directory run
```

`make run-with-proxy` starts the proxy, runs `make run`, and stops the proxy
when you press `Ctrl+C`.

## Proxy a site that is not in your project list

To proxy a site that's not in `unified_search_projects`, or to accept requests
from a non-loopback origin, use `--allow` and `--allow-origin`. See the
{doc}`CLI reference </reference/preview-proxy-cli>`.

## Troubleshooting

(how-to-preview-proxy-troubleshooting)=

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

### When a cookie variable isn't set

- **Locally:** the proxy still starts, and prints a warning for each variable
  that isn't set. For that project it sends no cookie, so the site returns its
  login page, and the preview shows the login text (for example "Log in to
  view this documentation"). Public projects and the build aren't affected.
- **On Read the Docs or in CI:** nothing changes. The proxy doesn't run there,
  and the extension ignores `preview_cookie_env` during the build. Only
  `auth_token_env` is read at build time, and that variable must be set.

Don't commit your cookies, and don't run the proxy on a shared or public
machine.
