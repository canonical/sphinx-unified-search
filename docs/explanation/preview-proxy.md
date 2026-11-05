# The preview proxy

The preview proxy lets your browser load remote search result previews during
local development. This page explains why it is needed and its limitations.

## Why it exists

When you preview your docs locally, for example at `http://127.0.0.1:8000`,
result previews usually fail to load. The browser fetches each preview
straight from the remote site, and that cross-origin request is blocked unless
the remote site allows it with CORS headers. Previews from private projects
fail for a second reason: the browser has no login for them, so the site
returns a login page.

The preview proxy is a small server on your machine that solves both problems
for local development. The browser asks the proxy for the remote page, the
proxy fetches it for you (with your cookies, if the project is private), and
the proxy answers with the CORS header the browser needs:

```{code-block} text
browser (127.0.0.1:8000) --> proxy (127.0.0.1:8010) --> remote docs site
                         <-- page + CORS header   <--
```

## What it does and doesn't change

The proxy is optional and does nothing unless you both set
`unified_search_preview_proxy` in `conf.py` and start the proxy yourself. It
has no effect on published sites: on a deployed site, previews for private
projects still depend on same-origin access or CORS headers (see
{ref}`How it works <exp-how-it-works-private-projects-and-previews>`).

It is a development tool, not a way to make previews work on a deployed
site.

## Safety measures

- **Loopback only.** The proxy only listens on loopback and refuses other
  addresses.
- **Restricted fetches.** It only fetches pages under the `base_url` of a
  configured project (or an `--allow` URL), so it can't be used to fetch
  arbitrary sites.
- **Local origins only.** It only answers requests from pages served from
  loopback addresses, and checks the `Host` header. A website you happen to
  have open can't use the proxy to read private docs with your cookie.
- **Scoped cookies.** A cookie is only sent to the project it belongs to, and
  is dropped if the site redirects to a different origin.
- **No secrets in config.** `preview_cookie_env` holds only variable names,
  so cookie values never appear in `conf.py`.

Even so, treat the cookie like a password: don't commit it, and don't run the
proxy on a shared or public machine.

## Related

- {doc}`Set up the preview proxy </how-to/set-up-preview-proxy>`
- {doc}`Preview proxy CLI reference </reference/preview-proxy-cli>`
