# How to build with private projects

This guide shows how to create an access token for a private Read the Docs
(RTD) project and make it available to local builds and to GitHub Actions.

Before you start, add the private project to `unified_search_projects` with
`auth_token_env` and `auth_scheme`. See
{doc}`Configure unified search </how-to/configure-unified-search>`.

## Create an HTTP header token

For each private project:

1. Open the project's Read the Docs settings.
1. Go to "Sharing" and "Add share".
1. Select "HTTP header token" for the "Access type", and a suitable expiry
   date.
1. Select "Allow access to all versions?" if you intend to use `searchindex.js`
   for all versions of the docs set. Otherwise, deselect that option and add the
   versions that will be used by `sphinx-unified-search`.

Copy the generated token and store it as a secret environment variable in the
RTD project that is _building_ the unified search.

For example, if "PROJECT B" wants to add the `searchindex.js` from "PROJECT A"
to its search results, generate the HTTP header token in PROJECT A, and add it
as an environment variable in PROJECT B (for example
`PROJECTA_DOCS_TOKEN=<generated HTTP header token>`).

## Build the docs locally

When building the documentation locally, you must set the environment
variables named by the `auth_token_env` entries in `unified_search_projects`.

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

Repeat this for each private project in `unified_search_projects`.

Once the variables are set, build or serve the documentation as usual with
`make html` or `make run`.

## Build the docs in GitHub Actions

Adding a secret to a repository doesn't automatically expose it to every
workflow run. Each job that needs it must reference it explicitly.

This matters most when the docs build runs in a reusable workflow (for
example, `uses: ./.github/workflows/build-docs.yml`). Secrets aren't inherited
by the called workflow by default. A build that works locally with an exported
token can therefore fail in CI, or silently skip the private index.

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
