console.log("[unified-search] file loaded");

window.addEventListener("DOMContentLoaded", async () => {

  console.log(
    "[unified-search] DOMContentLoaded fired"
  );

  let lookupIndex = new Map();

  //
  // Resolve the docs root. Sphinx >= 7 exposes it as
  // <html data-content_root="...">; older versions used
  // DOCUMENTATION_OPTIONS.URL_ROOT. The last-resort "../" guess only
  // holds for dirhtml builds, so it must not be the first choice.
  //
  const contentRoot =
    document.documentElement.dataset.content_root
    ?? (
      typeof DOCUMENTATION_OPTIONS !== "undefined"
        ? DOCUMENTATION_OPTIONS.URL_ROOT
        : undefined
    )
    ?? "../";

  const staticUrl =
    new URL(
      contentRoot + "_static/unified_search_projects.json",
      window.location.href
    ).href;

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
      /^(\.{1,2}\/)+/,
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

  //
  // If the mapping cannot be loaded we still carry on with an empty
  // lookup table. Returning here would leave every remote result
  // pointing at its raw "__unified__/..." URL; with an empty table
  // those results are hidden instead (see patchSearchResultsInner).
  //
  try {

    const response = await fetch(staticUrl);

    if (!response.ok) {
      console.warn(
        "[unified-search] mapping fetch failed:",
        response.status,
        staticUrl
      );
    } else {

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
    }

  } catch (err) {

    console.error(
      "[unified-search] failed to load mapping",
      err
    );
  }

  //
  // Client-side settings written by the extension at build time
  // (project filter on/off, name of the local project). A missing or
  // unreadable file means "defaults", i.e. no filter.
  //
  let config = { filter: false, local_project: "" };

  try {

    const configUrl =
      new URL(
        contentRoot + "_static/unified_search_config.json",
        window.location.href
      ).href;

    const response = await fetch(configUrl);

    if (response.ok) {
      config = { ...config, ...(await response.json()) };
    }

  } catch (err) {

    console.warn(
      "[unified-search] failed to load config, using defaults",
      err
    );
  }

  if (!config.local_project) {
    config.local_project = "This project";
  }

  //
  // A result can be hidden for two independent reasons: the extension
  // dropped it (duplicate of a local page, unresolved remote), or the
  // project filter excludes it. Track them separately so one never
  // un-hides the other, and derive the visible state from both.
  //
  // The HTML "hidden" attribute loses to any theme CSS that sets
  // "display" on result items, so hide with an inline style as well.
  //
  function applyVisibility(result) {
    const hide =
      result.dataset.unifiedSearchHidden === "true" ||
      result.dataset.unifiedSearchFiltered === "true";
    result.hidden = hide;
    result.style.display = hide ? "none" : "";
  }

  function setHidden(result, hide) {
    result.dataset.unifiedSearchHidden = hide ? "true" : "false";
    applyVisibility(result);
  }

  // True when the extension itself dropped the result (not the filter).
  function isHidden(result) {
    return result.dataset.unifiedSearchHidden === "true";
  }

  function isNamespaced(href) {
    return normalize(href).startsWith("__unified__/");
  }

  //
  // De-duplication of the SAME page indexed twice: once as a local
  // result and once as a remote one. This only happens when the local
  // site is itself listed in unified_search_projects.
  //
  // A page is identified by project + full docname, never by title or
  // by the last path segment. Pages from different projects are always
  // distinct, even when they share a title and a path (every Diataxis
  // project has its own "tutorials/index" titled "Tutorials").
  //
  // The remote result is hidden only when it belongs to the local
  // project (config.local_project) AND its full normalized docname
  // equals that of a local result. Safe to run repeatedly; results
  // arrive progressively.
  //
  function dedupeResults() {
    const results = [...document.querySelectorAll("ul.search li")];
    const localDocs = new Set();

    for (const result of results) {
      const a = result.querySelector("a");
      if (!a || a.dataset.unifiedSearchRemote) continue;

      const href = a.getAttribute("href");
      if (isNamespaced(href)) continue;

      localDocs.add(normalize(href));
    }

    for (const result of results) {
      const a = result.querySelector("a");
      if (!a || !a.dataset.unifiedSearchRemote) continue;

      const dup =
        result.dataset.unifiedSearchProject === config.local_project &&
        localDocs.has(normalize(a.dataset.unifiedSearchRemote));

      if (dup && !isHidden(result)) {
        console.log(
          "[unified-search] hiding duplicate of local page:",
          a.href
        );
      }
      setHidden(result, dup);
    }
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

  //
  // First pass (synchronous): rewrite remote links, label and tag every
  // result with its project. Kept separate from the snippet fetches so
  // that all results are tagged as soon as Sphinx finishes, without
  // waiting on network requests.
  //
  function patchLinks() {

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
      // A namespaced docname that we could not map back to a project
      // would link to a page that does not exist. Hide it.
      //
      if (!info && isNamespaced(href)) {

        console.warn(
          "[unified-search] unresolved namespaced result, hiding:",
          href
        );

        setHidden(result, true);
        anchor.dataset.unifiedSearchPatched = "true";
        continue;
      }

      //
      // A remote docname that is itself namespaced was merged into the
      // remote project from somewhere else (nested unified search); the
      // URL we would build does not exist. Hide it.
      //
      if (info && info.docname.startsWith("__unified__/")) {

        console.warn(
          "[unified-search] nested namespaced result, hiding:",
          href
        );

        setHidden(result, true);
        anchor.dataset.unifiedSearchPatched = "true";
        continue;
      }

      //
      // Local documentation result.
      //
      if (!info) {

        console.log(
          "[unified-search] local result:",
          href
        );

        result.dataset.unifiedSearchProject =
          config.local_project;

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
      anchor.dataset.unifiedSearchRemote =
        info.docname;

      result.dataset.unifiedSearchProject =
        info.project;

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
    }
  }

  //
  // Second pass (asynchronous): fetch a preview for every visible
  // remote result. Results hidden by the project filter are still
  // fetched, so unhiding them later is instant.
  //
  async function loadSnippets() {

    for (const result of document.querySelectorAll("ul.search li")) {

      const anchor =
        result.querySelector("a");

      if (
        !anchor ||
        !anchor.dataset.unifiedSearchRemote ||
        anchor.dataset.unifiedSearchSnippet ||
        isHidden(result)
      ) {
        continue;
      }

      anchor.dataset.unifiedSearchSnippet = "true";

      const remoteUrl = anchor.href;

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
  // Project filter (unified_search_project_filter).
  //
  // Sphinx streams results in one at a time and only writes the
  // "Search finished" summary once the last one is shown. The filter
  // waits for that, so counts are final and nothing shifts while the
  // list is still filling up. Filtering only hides rows: results are
  // never removed, and their previews are still fetched.
  //
  const filterState = {
    initialised: false,
    selected: new Set(),
  };

  function searchFinished() {
    const status =
      document.querySelector(
        "#search-results .search-summary"
      );

    return (
      Boolean(status) &&
      status.textContent.trim() !== ""
    );
  }

  function projectOf(result) {
    return result.dataset.unifiedSearchProject || "";
  }

  function initFilter() {

    if (
      !config.filter ||
      filterState.initialised ||
      !searchFinished()
    ) {
      return;
    }

    const list =
      document.querySelector("ul.search");

    if (!list) {
      return;
    }

    filterState.initialised = true;

    // Count visible results per project. Results the extension hid
    // (duplicates, unresolved) are not counted.
    const counts = new Map();

    for (const result of list.querySelectorAll("li")) {
      const project = projectOf(result);
      if (!project || isHidden(result)) continue;
      counts.set(project, (counts.get(project) || 0) + 1);
    }

    // Local project first, then remote projects in configured order.
    const projects = [
      config.local_project,
      ...new Set(
        [...lookupIndex.values()].map((info) => info.project)
      ),
      ...counts.keys(),
    ].filter(
      (name, i, all) => counts.has(name) && all.indexOf(name) === i
    );

    // Nothing to filter between.
    if (projects.length < 2) {
      return;
    }

    for (const name of new URLSearchParams(window.location.search).getAll("project")) {
      if (projects.includes(name)) {
        filterState.selected.add(name);
      }
    }

    const bar = document.createElement("div");
    bar.className = "unified-search-filter";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Filter results by project");

    const label = document.createElement("span");
    label.className = "unified-search-filter__label";
    label.textContent = "Filter by project:";
    bar.appendChild(label);

    const chips = new Map();

    function addChip(name, count) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "unified-search-chip";

      const text = document.createElement("span");
      text.textContent = name === null ? "All" : name;

      const num = document.createElement("span");
      num.className = "unified-search-chip__count";
      num.textContent = "(" + count + ")";

      chip.append(text, num);

      chip.addEventListener("click", () => {
        if (name === null) {
          filterState.selected.clear();
        } else if (filterState.selected.has(name)) {
          filterState.selected.delete(name);
        } else {
          filterState.selected.add(name);
        }
        applyFilter();
      });

      chips.set(name, chip);
      bar.appendChild(chip);
    }

    let total = 0;
    for (const n of counts.values()) total += n;

    addChip(null, total);
    for (const name of projects) {
      addChip(name, counts.get(name));
    }

    function applyFilter() {

      const all = filterState.selected.size === 0;

      for (const result of list.querySelectorAll("li")) {
        const project = projectOf(result);
        const filtered =
          !all &&
          project !== "" &&
          !filterState.selected.has(project);

        result.dataset.unifiedSearchFiltered = filtered ? "true" : "false";
        applyVisibility(result);
      }

      for (const [name, chip] of chips) {
        const pressed =
          name === null ? all : filterState.selected.has(name);
        chip.setAttribute("aria-pressed", pressed ? "true" : "false");
      }

      // Keep the selection in the URL so it survives reloads and can
      // be shared. Does not trigger a new search.
      const params = new URLSearchParams(window.location.search);
      params.delete("project");
      for (const name of filterState.selected) {
        params.append("project", name);
      }
      const query = params.toString();
      history.replaceState(
        null,
        "",
        window.location.pathname +
          (query ? "?" + query : "") +
          window.location.hash
      );
    }

    list.parentNode.insertBefore(bar, list);
    applyFilter();
  }

  async function patchSearchResults() {
    patchLinks();
    dedupeResults();
    initFilter();
    await loadSnippets();
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
