/**
 * Compatibility bridge for sphinx-unified-search + Ulwazi theme.
 * 
 * Fixes issues when both sphinx-unified-search and Ulwazi's search-breadcrumbs.js
 * are active simultaneously. The main problem: breadcrumbs.js injects breadcrumbs
 * into results that contain __unified__ namespace URLs (internal merged index paths),
 * which should never be visible to users.
 * 
 * This bridge:
 * 1. Removes breadcrumbs from results containing __unified__ namespace
 * 2. Removes breadcrumbs from results unified-search.js has hidden
 * 3. Ensures docname data attribute is preserved for remaining breadcrumbs
 */

(function() {
  'use strict';

  function cleanupProblematicBreadcrumbs() {
    var results = document.querySelectorAll('#search-results ul.search li');
    
    results.forEach(function(li) {
      var anchor = li.querySelector('a');
      if (!anchor) return;
      
      var href = anchor.getAttribute('href');
      if (!href) return;
      
      // Remove breadcrumbs from results that:
      // 1. Contain __unified__ namespace (internal merged index paths)
      // 2. Are marked as hidden/filtered by unified-search.js
      var isNamespaced = href.includes('__unified__');
      var isFiltered = li.dataset.unifiedSearchFiltered === 'true';
      
      if (isNamespaced || isFiltered) {
        // Remove any breadcrumb nav from this result
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

  // Run cleanup after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      // Wait for both unified-search.js and search-breadcrumbs.js to run
      setTimeout(cleanupProblematicBreadcrumbs, 500);
    });
  } else {
    setTimeout(cleanupProblematicBreadcrumbs, 500);
  }

  // Re-run periodically to catch lazy-loaded or dynamically added results
  var cleanupInterval = setInterval(cleanupProblematicBreadcrumbs, 1000);
  
  // Stop after 30 seconds to avoid unnecessary overhead
  setTimeout(function() {
    clearInterval(cleanupInterval);
  }, 30000);
})();
