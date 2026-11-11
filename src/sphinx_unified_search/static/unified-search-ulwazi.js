/**
 * Ulwazi integration for sphinx-unified-search (High-Performance Debounced Version).
 */
(function () {
  'use strict';

  let isMutating = false;
  let debounceTimer = null;

  function processResults() {
    const listItems = document.querySelectorAll('ul.search > li:not([data-ulwazi-ready="true"])');
    if (listItems.length === 0) {
      updateSummaryCount();
      return;
    }

    // Disconnect observer during batch update to prevent infinite loops
    observer.disconnect();

    listItems.forEach(li => {
      // 1. Wait until unified-search.js has rewritten this result.
      // Remote links (and their breadcrumbs) are patched there; here we
      // only tidy up. Results it never patches stay untouched/hidden.
      const mainLink = li.querySelector(':scope > a[data-score]') || li.querySelector(':scope > a');
      if (
        mainLink &&
        !mainLink.dataset.unifiedSearchPatched &&
        /(^|\/)__unified__\//.test(mainLink.getAttribute('href') || '') &&
        li.getAttribute('data-unified-search-hidden') !== 'true'
      ) {
        return;
      }

      // 2. Clean breadcrumb list
      const breadcrumbList = li.querySelector('.search-breadcrumb-list');
      if (breadcrumbList) {
        const items = breadcrumbList.querySelectorAll('.search-breadcrumb-item');
        items.forEach(item => {
          const a = item.querySelector('a');
          const text = (a ? a.textContent : item.textContent || '').trim();
          const href = a ? a.getAttribute('href') || '' : '';

          if (
            text === '__unified__' ||
            href.includes('__unified__/index.html') ||
            href.endsWith('__unified__') ||
            item.hasAttribute('hidden') ||
            item.style.display === 'none'
          ) {
            item.remove();
            return;
          }

          if (a && text.startsWith('[')) {
            a.textContent = text.replace(/^\[[^\]]+\]\s*/, '');
          }

          // Anything still pointing into __unified__/ has no remote page.
          if (a && /(^|\/)__unified__\//.test(href)) {
            item.remove();
          }
        });

        li.querySelectorAll('.search-breadcrumb-separator-final').forEach(sep => sep.remove());
      }

      // 3. Keep snippet below title
      const context = li.querySelector(':scope > .context');
      if (mainLink && context && mainLink.nextSibling !== context) {
        mainLink.insertAdjacentElement('afterend', context);
      }

      li.setAttribute('data-ulwazi-ready', 'true');
    });

    updateSummaryCount();

    // Re-attach observer
    const target = document.getElementById('search-results') || document.body;
    observer.observe(target, { childList: true, subtree: true });
  }

  function updateSummaryCount() {
    const summary = document.querySelector('.search-summary');
    if (!summary) return;

    const visibleItems = document.querySelectorAll('ul.search > li:not([style*="display: none"]):not([hidden])');
    const totalItems = document.querySelectorAll('ul.search > li');
    if (totalItems.length === 0) return;

    const match = summary.textContent.match(/for [“"'](.+?)[”"']/);
    const term = match ? match[1] : '';

    summary.textContent = 'Showing ' + visibleItems.length + ' result' +
                          (visibleItems.length === 1 ? '' : 's') +
                          (term ? ' for “' + term + '”' : '');
  }

  function scheduleRun() {
    if (debounceTimer) cancelAnimationFrame(debounceTimer);
    debounceTimer = requestAnimationFrame(() => {
      processResults();
    });
  }

  const observer = new MutationObserver(() => {
    scheduleRun();
  });

  document.addEventListener('click', e => {
    if (e.target.closest('.unified-search-chip')) {
      setTimeout(updateSummaryCount, 30);
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      const target = document.getElementById('search-results') || document.body;
      observer.observe(target, { childList: true, subtree: true });
      scheduleRun();
    });
  } else {
    const target = document.getElementById('search-results') || document.body;
    observer.observe(target, { childList: true, subtree: true });
    scheduleRun();
  }
})();