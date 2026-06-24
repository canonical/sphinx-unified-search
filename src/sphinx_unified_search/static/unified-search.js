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

  console.log("[unified-search] DOMContentLoaded fired");

  let mapping = {};

  //
  // Load the mapping file.
  //
  const staticUrl =
    window.location.origin +
    "/_static/unified_search_projects.json";

  console.log(
    "[unified-search] loading mapping from:",
    staticUrl
  );

  try {
    const response = await fetch(staticUrl);

    if (!response.ok) {
      console.warn(
        "[unified-search] mapping fetch failed:",
        response.status
      );
      return;
    }

    mapping = await response.json();

    console.log(
      "[unified-search] loaded mapping",
      mapping
    );

  } catch (err) {
    console.error(
      "[unified-search] failed to load mapping",
      err
    );
    return;
  }

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

  function lookupProject(docname) {
    const normalized = normalize(docname);

    for (const info of Object.values(mapping)) {
      if (
        normalize(info.docname) === normalized
      ) {
        return info;
      }
    }

    return null;
  }

  function buildSnippet(text, keywords) {
    if (!text) {
      return "";
    }

    const lower = text.toLowerCase();

    for (const keyword of keywords) {

      const idx =
        lower.indexOf(keyword.toLowerCase());

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

    return text.substring(0, 250) + "...";
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

      const info =
        lookupProject(href);

      //
      // Skip local docs.
      //
      if (!info) {
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
      anchor.rel = "noopener noreferrer";

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
      // Generate snippet from remote page.
      //
      try {

        const response =
          await fetch(remoteUrl);

        const html =
          await response.text();

        const parser =
          new DOMParser();

        const doc =
          parser.parseFromString(
            html,
            "text/html"
          );

        //
        // Prefer the main content area.
        //
        const content =
          doc.querySelector("main") ||
          doc.querySelector('[role="main"]') ||
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

        let context =
          result.querySelector(".context");

        if (!context) {

          context =
            document.createElement("p");

          context.className =
            "context";

          result.appendChild(context);
        }

        context.textContent =
          snippet;

      } catch (err) {

        console.warn(
          "[unified-search] snippet generation failed for",
          remoteUrl,
          err
        );
      }
    }
  }

  //
  // Patch immediately.
  //
  patchSearchResults();

  //
  // Patch again whenever Sphinx updates results.
  //
  const observer =
    new MutationObserver(() => {
      patchSearchResults();
    });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  console.log(
    "[unified-search] observer registered"
  );
});
