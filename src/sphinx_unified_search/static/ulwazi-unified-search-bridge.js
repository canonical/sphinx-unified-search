/**
 * Compatibility bridge for sphinx-unified-search + Ulwazi theme.
 * 
 * Fixes issues when both sphinx-unified-search and Ulwazi's search-breadcrumbs.js
 * are active simultaneously. Primary issues:
 * 1. Breadcrumbs.js injects breadcrumbs into __unified__ namespace results
 *    (internal merged index paths that should never be visible)
 * 2. Breadcrumbs.js doesn't respect unified-search.js hidden/filtered state
 * 3. Layout becomes messy with breadcrumbs + filter chips + snippets competing
 * 
 * This bridge:
 * 1. Removes ALL breadcrumbs from results with __unified__ in any URL
 * 2. Removes breadcrumbs from results hidden/filtered by unified-search.js
 * 3. Removes entire result items that are __unified__ namespaced
 * 4. Preserves docname data attribute for valid results
 */

(function() {
  'use strict';

  function cleanupMessyResults() {
    var results = document.querySelectorAll('#search-results ul.search li');
    
    results.forEach(function(li) {
      var anchor = li.querySelector('a');
      if (!anchor) return;
      
      var href = anchor.getAttribute('href');
      if (!href) return;
      
      // Check for __unified__ namespace anywhere in the result
      // This includes:
      // - href itself: __unified__/...
      // - breadcrumb links: pointing to __unified__/...
      var hasUnifiedNamespace = href.includes('__unified__');
      
      // Check if result is marked as hidden/filtered by unified-search.js
      var isFiltered = li.dataset.unifiedSearchFiltered === 'true';
      
      // If result contains __unified__ namespace, remove it entirely
      // These are internal merged index paths that should never be shown
      if (hasUnifiedNamespace) {
        li.remove();
        return;
      }
      
      // If result is filtered/hidden by unified-search, clean up breadcrumbs
      if (isFiltered) {
        var breadcrumb = li.querySelector('.search-result-breadcrumb');
        if (breadcrumb) {
          breadcrumb.remove();
        }
        return;
      }
      
      // For valid results, ensure docname is preserved
      if (!anchor.dataset.unifiedSearchOriginalDocname) {
        var docName = href
          .split('#')[0]
          .replace(/^\.\.\//, '')
          .replace(/\/$/, '');
        anchor.dataset.unifiedSearchOriginalDocname = docName;
      }
    });
  }

  // Run cleanup after both unified-search.js and search-breadcrumbs.js have finished
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(cleanupMessyResults, 500);
    });
  } else {
    setTimeout(cleanupMessyResults, 500);
  }

  // Re-run periodically to catch dynamically added results
  var cleanupInterval = setInterval(cleanupMessyResults, 1000);
  
  // Stop after 30 seconds
  setTimeout(function() {
    clearInterval(cleanupInterval);
  }, 30000);
})();
