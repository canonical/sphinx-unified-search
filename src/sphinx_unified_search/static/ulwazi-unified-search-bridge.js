/**
 * Compatibility bridge for sphinx-unified-search + Ulwazi theme.
 * 
 * When both sphinx-unified-search and Ulwazi's search-breadcrumbs.js are active,
 * they conflict on DOM modifications, causing strange search results.
 * 
 * Solution: unified-search.js now stores the original docname in a data attribute
 * on each result link. This bridge ensures that doesn't cause issues with Ulwazi's
 * breadcrumb extraction, which normally extracts from href (which may be rewritten).
 * 
 * For local results: breadcrumbs work fine as-is
 * For remote results: unified-search.js rewrites href to point to remote site
 *   - breadcrumbs will be "wrong" but that's acceptable since result opens in new tab
 *   - this bridge prevents errors by verifying the data attribute exists
 */

(function() {
  'use strict';

  // Minimal compatibility check: ensure all anchors that unified-search.js
  // has processed still have valid markup for breadcrumbs.js to work with
  
  function ensureDocnamePreserved() {
    var results = document.querySelectorAll('#search-results ul.search li a');
    results.forEach(function(anchor) {
      // If unified-search.js hasn't set the data attribute, do it now as fallback
      if (!anchor.dataset.unifiedSearchOriginalDocname) {
        var href = anchor.getAttribute('href');
        if (href) {
          var docName = href
            .split('#')[0]
            .replace(/^\.\.\//, '')
            .replace(/\/$/, '');
          anchor.dataset.unifiedSearchOriginalDocname = docName;
        }
      }
    });
  }

  // Run after DOM is ready and scripts have loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(ensureDocnamePreserved, 100);
    });
  } else {
    setTimeout(ensureDocnamePreserved, 100);
  }

  // Also run periodically to catch lazy-loaded results
  setInterval(ensureDocnamePreserved, 2000);
})();
