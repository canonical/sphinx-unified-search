/**
 * Compatibility bridge for sphinx-unified-search + Ulwazi theme.
 * 
 * Fixes issues when both sphinx-unified-search and Ulwazi's search-breadcrumbs.js
 * are active simultaneously. The core problem: Ulwazi's breadcrumbs.js injects
 * breadcrumb navigation directly into result items, which breaks layout and
 * creates duplicate/misaligned content when combined with unified-search results.
 * 
 * Strategy:
 * 1. Remove breadcrumb navs from unified-search results (both local and remote)
 * 2. Remove any __unified__/ namespace URLs that escaped unified-search.js
 * 3. Let Ulwazi's breadcrumbs.js only work on non-unified-search results
 * 4. Preserve unified-search data attributes for result organization
 * 
 * This keeps search results clean and properly aligned without needing
 * Ulwazi theme modifications.
 */

(function() {
  'use strict';

  function cleanupResults() {
    var results = document.querySelectorAll('#search-results ul.search li');
    
    results.forEach(function(li) {
      var anchor = li.querySelector('a[data-score]');
      if (!anchor) return;
      
      var href = anchor.getAttribute('href');
      if (!href) return;
      
      // Remove __unified__/ namespace URLs entirely
      // These are internal merged index paths that should never be visible
      if (href.includes('__unified__/')) {
        li.remove();
        return;
      }
      
      // For unified-search results (marked with data attributes), remove breadcrumbs
      // Unified-search handles its own result organization via project filtering
      var hasUnifiedSearchMarkers = (
        anchor.dataset.unifiedSearchPatched ||
        anchor.dataset.unifiedSearchRemote ||
        anchor.dataset.unifiedSearchOriginalDocname ||
        li.dataset.unifiedSearchProject ||
        li.dataset.unifiedSearchFiltered !== undefined
      );
      
      if (hasUnifiedSearchMarkers) {
        // Remove the breadcrumb nav to prevent layout conflicts
        var breadcrumb = li.querySelector('.search-result-breadcrumb');
        if (breadcrumb) {
          breadcrumb.remove();
        }
        
        // If result is hidden/filtered, remove entire item
        if (li.dataset.unifiedSearchFiltered === 'true' || 
            li.dataset.unifiedSearchHidden === 'true') {
          li.remove();
          return;
        }
      }
    });
  }

  // Run cleanup after both unified-search.js and Ulwazi's search-breadcrumbs.js finish
  // 500ms is sufficient to allow script execution to complete
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(cleanupResults, 500);
    });
  } else {
    setTimeout(cleanupResults, 500);
  }

  // Re-run periodically to catch dynamically rendered results (infinite scroll, etc.)
  var cleanupInterval = setInterval(cleanupResults, 1000);
  
  // Stop cleanup after 30 seconds (search results shouldn't update after that)
  setTimeout(function() {
    clearInterval(cleanupInterval);
  }, 30000);
})();
