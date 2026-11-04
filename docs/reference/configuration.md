# Configuration reference

All settings go in your project's `conf.py`. For task-oriented guidance, see
{doc}`Configure unified search </how-to/configure-unified-search>`.

```{note}
Types and defaults on this page are drawn from the behavior described in the
project documentation. Verify them against the source before publishing.
```

## Summary

| Setting | Type | Default | Purpose |
| --- | --- | --- | --- |
| `unified_search_projects` | list of dict | none | Remote projects to include in the search |
| `unified_search_project_filter` | bool | `False` | Show project filter chips on the results page |
| `unified_search_local_project_name` | str | Sphinx's `project` setting | Label for this project's results in the filter |
| `unified_search_cache_remote_indexes` | bool | `False` | Download each remote index once per `sphinx-autobuild` session |
| `unified_search_preview_proxy` | str (URL) | unset | Address of the local preview proxy |

## `unified_search_projects`

A list of dictionaries, one per project.

| Key | Required | Description |
| --- | --- | --- |
| `name` | Yes | Unique identifier for the project. For results from projects other than the host project, this value is appended to the page title in the search results. |
| `base_url` | Yes | Base URL of the documentation. Used as the destination when a user clicks a result, and (with the preview proxy) as the allowlist for fetched pages. |
| `searchindex_url` | Yes | URL of the project's `searchindex.js`. |
| `auth_token_env` | Private projects | Name of the environment variable containing the RTD HTTP header token. Read at build time. |
| `auth_scheme` | Private projects | Authorization scheme used in the HTTP `Authorization` header. For RTD HTTP header tokens, use `"Token"`. |
| `preview_cookie_env` | No | Name(s) of environment variable(s) holding cookies for local previews through the preview proxy. See {ref}`below <ref-configuration-preview-cookie-env>`. |

```python
unified_search_projects = [
    {
        "name": "ProjectA",
        "base_url": "https://documentation.ubuntu.com/projecta/",
        "searchindex_url": "https://documentation.ubuntu.com/projecta/searchindex.js",
        "auth_token_env": "PROJECTA_DOCS_TOKEN",
        "auth_scheme": "Token",
        "preview_cookie_env": "PROJECTA_COOKIE",
    },
]
```

### `preview_cookie_env`

(ref-configuration-preview-cookie-env)=


Holds environment variable _names_, never cookie values, so no secrets end up
in `conf.py`. It is only used by the preview proxy during local development.
The extension ignores it during the build. It accepts three forms:

```python
# 1. One variable holding the whole Cookie header value
"preview_cookie_env": "PROJECTA_COOKIE",            # PROJECTA_COOKIE="sessionid=abc; csrftoken=def"

# 2. Several variables, each holding a Cookie header value. They're joined
#    with "; ". Variables that are unset are skipped, with a warning at startup.
"preview_cookie_env": ["PROJECTA_SESSION", "PROJECTA_EXTRA"],

# 3. One variable per cookie, each holding only that cookie's value
"preview_cookie_env": {"sessionid": "PROJECTA_SESSION", "csrftoken": "PROJECTA_CSRF"},
```

A pasted `Cookie:` prefix in a value is ignored. A project's cookies are only
sent to that project.

## `unified_search_project_filter`

When `True`, a "Filter by project" row of chips appears above the search
results. Off by default. Not shown when results come from only one project.
See {ref}`Search page reference <ref-compatibility-css-classes>` for the CSS classes
and URL parameter.

## `unified_search_local_project_name`

Label for this project's own results in the filter. Defaults to Sphinx's
`project` setting.

## `unified_search_cache_remote_indexes`

(ref-configuration-unified-search-cache-remote-indexes)=


When `True`, each remote `searchindex.js` is downloaded once per
`sphinx-autobuild` session and reused for later rebuilds.

- The cache is scoped to the running `sphinx-autobuild` process and stored
  under the Sphinx doctree directory, so it is discarded when you restart the
  preview.
- Regular builds (`make html`, Read the Docs, CI) are unaffected and always
  fetch fresh indexes.
- Only successfully parsed downloads are cached.
- The cache key covers the index URL and its resolved authentication, so a
  changed token or header forces a new download.
- Tokens themselves are never written to disk.

## `unified_search_preview_proxy`

Address where the local preview proxy listens, for example
`"http://127.0.0.1:8010/"`. The proxy reads this value from `conf.py`. The
browser only uses it when the docs are viewed from `localhost`, `127.0.0.1` or
`[::1]`. See {doc}`Set up the preview proxy </how-to/set-up-preview-proxy>`.
