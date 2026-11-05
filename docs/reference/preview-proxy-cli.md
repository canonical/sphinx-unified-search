# Preview proxy CLI

```{code-block} shell
sphinx-unified-search-proxy [options]
```

The proxy is a local development tool. For setup, see
{doc}`Set up the preview proxy </how-to/set-up-preview-proxy>`. For how it
works, see {doc}`Preview proxy </explanation/preview-proxy>`.

Run the command from the directory that contains `conf.py`, or pass
`--conf-dir`. If the command isn't found, run it from your docs virtual
environment, for example `.venv/bin/sphinx-unified-search-proxy`.

## Options

```{list-table}
:header-rows: 1

* - Option
  - Description
* - `--conf-dir DIR`
  - Directory containing `conf.py`. Default: current directory.
* - `--no-conf`
  - Don't read `conf.py`. Use only `--allow`.
* - `--listen URL`
  - Address to listen on. Default: `unified_search_preview_proxy`, else
    `http://127.0.0.1:8010/`.
* - `--allow URL[=ENV_VAR]`
  - Also proxy a site that's not in `unified_search_projects`. To send cookies,
    append `=ENV_VAR` (or several, separated by commas) after the trailing slash.
* - `--allow-origin ORIGIN`
  - Also accept requests from this non-loopback web origin.
```

Examples of `--allow`:

```{code-block} shell
--allow https://example.com/docs/=DOCS_COOKIE
--allow https://example.com/docs/=DOCS_SESSION,DOCS_CSRF
```

## Startup output

The proxy prints the address it listens on, then one line per project showing
which cookie variables it uses. It warns about variables that aren't set and
never prints cookie values.

```{code-block} text
unified-search preview proxy on http://127.0.0.1:8010/
  https://ubuntu.com/kernel/docs/  (Kernel; no cookie)
  https://documentation.ubuntu.com/projecta/  (ProjectA; cookie from $PROJECTA_COOKIE)
```

## Request log lines

```{list-table}
:header-rows: 1

* - Line
  - Meaning
* - `[200] <url>`
  - Page fetched and returned.
* - `[blocked] <url>`
  - The URL isn't under a configured `base_url` or `--allow` URL.
* - `[401]` / `[403]`
  - The remote site rejected the request, usually an expired cookie.
* - `[502]`
  - The proxy couldn't reach the remote site.
```

## Errors

```{list-table}
:header-rows: 1

* - Message
  - Cause
* - `error: no conf.py in ...`
  - No `conf.py` in the current or `--conf-dir` directory.
* - `cannot listen on 127.0.0.1:8010`
  - The port is in use.
* - `refusing to listen on ...`
  - The proxy only listens on loopback addresses.
* - `origin not allowed` (HTTP reply)
  - The request came from a non-loopback origin. Use `--allow-origin`.
```

For causes and fixes, see the troubleshooting section of
{ref}`Set up the preview proxy <how-to-preview-proxy-troubleshooting>`.
