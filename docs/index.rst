Sphinx Unified Search documentation
===================================

Sphinx Unified Search (``sphinx-unified-search``) is a Sphinx extension that
merges the search indexes of other Sphinx sites into your host project when you
build.
Site visitors keep the familiar Sphinx search page, and results from other
projects link straight to their original pages. There's no external service to
run and no per-query cost, and private Read the Docs projects can be included
with an access token.

Documentation is often spread across upstream projects, related products, and
public and internal sets, and visitors shouldn't need to know which site holds
the answer. Unified search lets them look in one place.

This extension may be useful for you if your docs build on an upstream project,
if your products or solutions share an audience, or if your team wants private
and public documentation sets to be searchable together.

In this documentation
---------------------

..  domain::

    ..  slice:: Setting up

        :doc:`Configure unified search </how-to/configure-unified-search>`
        :doc:`Configuration options </reference/configuration>`

    ..  slice:: Private projects

        :doc:`Build with private projects </how-to/build-with-private-projects>`

    ..  slice:: Themes and compatibility

        :doc:`Use a different theme </how-to/use-a-different-theme>`
        :doc:`Compatibility reference </reference/compatibility>`

    ..  slice:: Local previews

        :doc:`Set up the preview proxy </how-to/set-up-preview-proxy>`
        :doc:`Preview proxy CLI reference </reference/preview-proxy-cli>`
        :doc:`The preview proxy </explanation/preview-proxy>`

    ..  slice:: Background

        :doc:`How Sphinx unified search works </explanation/how-it-works>`

How this documentation is organized
-----------------------------------

This documentation uses the `Diátaxis documentation structure`_.

- :doc:`How-to guides </how-to/index>` assume you have basic familiarity with
  Sphinx and with building documentation projects and take you through
  configuring unified search.
- :doc:`Reference </reference/index>` provides a guide to the configuration
  settings, the preview proxy command-line options, and the compatibility
  requirements.
- :doc:`Explanation </explanation/index>` includes topic overviews, background
  and context, and detailed discussion of how unified search works and why the
  preview proxy exists.

Get involved
~~~~~~~~~~~~

- `Sphinx Unified Search repository`_

Governance and policies
~~~~~~~~~~~~~~~~~~~~~~~

- `Code of conduct`_


.. toctree::
   :maxdepth: 1
   :hidden:

   how-to/index
   reference/index
   explanation/index

.. LINKS

.. _Sphinx Unified Search repository: https://github.com/canonical/sphinx-unified-search
.. _Code of conduct: https://ubuntu.com/community/ethos/code-of-conduct
.. _Diátaxis documentation structure: https://diataxis.fr/