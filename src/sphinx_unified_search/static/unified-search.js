console.log("[unified-search] file loaded");

window.addEventListener("DOMContentLoaded", async () => {

  //
  // Only run on the Sphinx search page.
  //
  const isSearchPage =
    window.location.pathname.endsWith("/search/") ||
    window.location.pathname.endsWith("/search/index.html") ||
    window.location.pathname.endsWith("/search.html");

  if (!isSearchPage) {
    console.log(
      "[unified-search] not on search page, skipping"
    );
    return;
  }

  console.log(
    "[unified-search] DOMContentLoaded fired"
  );

  let lookupIndex = new Map();

  let staticUrl;

  if (
    typeof DOCUMENTATION_OPTIONS !== "undefined"
    && DOCUMENTATION_OPTIONS.URL_ROOT !== undefined
  ) {
    staticUrl =
      DOCUMENTATION_OPTIONS.URL_ROOT +
      "_static/unified_search_projects.json";
  } else {
    staticUrl =
      new URL(
        "../_static/unified_search_projects.json",
        window.location.href
      ).href;
  }

  console.log(
    "[unified-search] loading mapping from:",
    staticUrl
  );

  function normalize(path) {

    if (!path) {
      return "";
    }

    let normalized = path;

    normalized = normalized.split("#")[0];
    normalized = normalized.split("?")[0];

    normalized = normalized.replace(
      window.location.origin,
      ""
    );

    normalized = normalized.replace(
      /^(\.\.\/)+/,
      ""
    );

    normalized = normalized.replace(
      /^\/+/,
      ""
    );

    normalized = normalized.replace(
      /\.html$/,
      ""
    );

    normalized = normalized.replace(
      /\/$/,
      ""
    );

    normalized = normalized.replace(
      /\/index$/,
      ""
    );

    return normalized;
  }

  try {

    const response = await fetch(staticUrl);

    if (!response.ok) {
      console.warn(
        "[unified-search] mapping fetch failed:",
        response.status
      );
      return;
    }

    const mapping = await response.json();

    console.log(
      "[unified-search] loaded mapping with",
      Object.keys(mapping).length,
      "entries"
    );

    for (const [namespacedDocname, info] of Object.entries(mapping)) {
      lookupIndex.set(
        normalize(namespacedDocname),
        info
      );
    }

  } catch (err) {

    console.error(
      "[unified-search] failed to load mapping",
      err
    );

    return;
  }

  function lookupProject(href) {

    const normalizedHref =
      normalize(href);

    console.log(
      "[unified-search] looking up:",
      normalizedHref
    );

    const info =
      lookupIndex.get(normalizedHref);

    if (info) {
      console.log(
        "[unified-search] MATCH FOUND:",
        normalizedHref
      );
      return info;
    }

    return null;
  }

  function buildSnippet(text, keywords) {

    if (!text) {
      return "";
    }

    const lower =
      text.toLowerCase();

    for (const keyword of keywords) {

      const idx =
        lower.indexOf(
          keyword.toLowerCase()
        );

      if (idx !== -1) {

        const start =
          Math.max(0, idx - 120);

        const end =
          Math.min(
            text.length,
            idx + 200
          );

        return (
          "..." +
          text.substring(start, end).trim() +
          "..."
        );
      }
    }

    return (
      text.substring(0, 250) +
      "..."
    );
  }

  function setContext(result, message) {

    let context =
      result.querySelector(".context");

    if (!context) {

      context =
        document.createElement("p");

      context.className =
        "context";

      result.appendChild(context);
    }

    context.textContent = message;
  }

  async function patchSearchResults() {

    const searchResults =
      document.querySelectorAll(
        "ul.search li"
      );

    console.log(
      "[unified-search] found",
      searchResults.length,
      "search result(s)"
    );

    for (const result of searchResults) {

      const anchor =
        result.querySelector("a");

      if (!anchor) {
        continue;
      }

      if (
        anchor.dataset.unifiedSearchPatched
      ) {
        continue;
      }

      const href =
        anchor.getAttribute("href");

      console.log(
        "[unified-search] processing:",
        href
      );

      const info =
        lookupProject(href);

      //
      // Local documentation result.
      //
      if (!info) {

        console.log(
          "[unified-search] local result:",
          href
        );

        continue;
      }

      const remoteUrl =
        info.base_url.replace(/\/$/, "") +
        "/" +
        normalize(info.docname) +
        "/";

      console.log(
        "[unified-search] rewriting",
        href,
        "->",
        remoteUrl
      );

      anchor.href = remoteUrl;
      anchor.target = "_blank";
      anchor.rel =
        "noopener noreferrer";

      anchor.dataset.unifiedSearchPatched =
        "true";

      if (
        !anchor.textContent.startsWith(
          "[" + info.project + "]"
        )
      ) {

        anchor.innerHTML =
          "[" +
          info.project +
          "] " +
          anchor.innerHTML;
      }

      //
      // Always attempt the snippet fetch, even for projects marked
      // skip_snippet. Some visitors may already have a valid session
      // for the target site (e.g. same-origin requests carry cookies
      // automatically) and will get a real preview; the fallback
      // message below is only shown when the fetch genuinely fails —
      // never preemptively based on project config alone.
      //
      try {

        const response =
          await fetch(remoteUrl);

        if (!response.ok) {
          throw new Error(
            "HTTP " + response.status
          );
        }

        const html =
          await response.text();

        const parser =
          new DOMParser();

        const doc =
          parser.parseFromString(
            html,
            "text/html"
          );

        const content =
          doc.querySelector("main") ||
          doc.querySelector(
            '[role="main"]'
          ) ||
          doc.body;

        const text =
          content.textContent || "";

        const keywords =
          (
            new URLSearchParams(
              window.location.search
            ).get("q") || ""
          ).split(/\s+/);

        const snippet =
          buildSnippet(
            text,
            keywords
          );

        setContext(result, snippet);

      } catch (err) {

        console.warn(
          "[unified-search] snippet generation failed for",
          remoteUrl,
          err
        );

        setContext(
          result,
          "Unable to load preview. Click on results to view the full page."
        );
      }
    }
  }

  //
  // Initial patch.
  //
  patchSearchResults();

  //
  // Re-run whenever Sphinx updates results.
  //
  const observer =
    new MutationObserver(() => {
      patchSearchResults();
    });

  observer.observe(
    document.body,
    {
      childList: true,
      subtree: true,
    }
  );

  console.log(
    "[unified-search] observer registered"
  );
});
