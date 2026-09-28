/*
 * sphinx-unified-search: ranking boost.
 *
 * Sphinx search is bag-of-words AND and scores a page by its single
 * best term, so a page matching one word in its title ties with a page
 * matching every word in its title. This hook adds a bonus for each
 * query word found in the result's title, so titles like
 * "24.04 LTS release notes" outrank pages that merely mention
 * "release" and "note" in body text for the query "release notes".
 *
 * It only re-orders results; it never adds or removes any.
 *
 * Works regardless of script load order relative to searchtools.js:
 *  - loaded first: defines Scorer with Sphinx's default weights
 *  - loaded after: attaches score() to the existing Scorer
 */
(function () {
  const BONUS_PER_TITLE_WORD = 10;
  const BONUS_ALL_WORDS_IN_TITLE = 10;

  // Crude English suffix strip ("notes" -> "not", "release" -> "releas")
  // so "notes" matches a title containing "note". Matching is by prefix
  // on title words, so over-stripping is harmless.
  function stem(word) {
    const s = word.replace(/(es|s|e)$/, "");
    return s.length >= 3 ? s : word;
  }

  function queryStems() {
    const q = new URLSearchParams(window.location.search).get("q") || "";
    return (q.toLowerCase().match(/\w+/g) || [])
      .filter((w) => w.length > 2)
      .map(stem);
  }

  function score(result) {
    const base = result[4];
    const stems = queryStems();
    if (!stems.length) return base;

    const titleWords = String(result[1] || "").toLowerCase().match(/\w+/g) || [];
    const hits = stems.filter((s) => titleWords.some((t) => t.startsWith(s)));

    let bonus = hits.length * BONUS_PER_TITLE_WORD;
    if (hits.length === stems.length) bonus += BONUS_ALL_WORDS_IN_TITLE;
    return base + bonus;
  }

  if (typeof window.Scorer === "undefined") {
    window.Scorer = {
      objNameMatch: 11,
      objPartialMatch: 6,
      objPrio: { 0: 15, 1: 5, 2: -5 },
      objPrioDefault: 0,
      title: 15,
      partialTitle: 7,
      term: 5,
      partialTerm: 2,
    };
  }

  // Don't clobber a score() the project already defined.
  if (!window.Scorer.score) {
    window.Scorer.score = score;
  }
})();
