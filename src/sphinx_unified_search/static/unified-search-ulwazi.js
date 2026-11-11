/**
 * Ulwazi integration for sphinx-unified-search (High-Performance Debounced Version).
 */
(function () {
  'use strict';

  let metadataCache = null;
  let metadataPromise = null;
  let isMutating = false;
  let debounceTimer = null;

  function getMetadata() {
    if (metadataCache) return Promise.resolve(metadataCache);
    if (metadataPromise) return metadataPromise;

    const root = (window.DOCUMENTATION_OPTIONS && window.DOCUMENTATION_OPTIONS.URL_ROOT) || '../';
    const metaUrl = root + '_static/unified-search-metadata.json';

    metadataPromise = fetch(metaUrl)
      .then(r => r.ok ? r.json() : {})
      .then(data => {
        metadataCache = data;
        return data;
      })
      .catch(() => {
        metadataCache = {};
        return {};
      });

    return metadataPromise;
  }

  function resolveRemoteUrl(href, project, meta) {
    if (!href || href.startsWith('http://') || href.startsWith('https://')) return href;
    const match = href.match(/__unified__\/([^/]+)\/(.*)/);
    if (match && meta && meta[match[1]] && meta[match[1]].url) {
      let base = meta[match[1]].url;
      if (!base.endsWith('/')) base += '/';
      return base + match[2];
    }
    return href;
  }

  function processResults(meta) {
    const listItems = document.querySelectorAll('ul.search > li:not([data-ulwazi-ready="true"])');
    if (listItems.length === 0) {
      updateSummaryCount();
      return;
    }

    // Disconnect observer during batch update to prevent infinite loops
    observer.disconnect();

    listItems.forEach(li => {
      const project = li.getAttribute('data-unified-search-project') || '';

      // 1. Fix main link
      const mainLink = li.querySelector('a[data-score]') || li.querySelector(':scope > a');
      if (mainLink) {
        const origHref = mainLink.getAttribute('href');
        const realHref = resolveRemoteUrl(origHref, project, meta);
        if (realHref !== origHref) {
          mainLink.setAttribute('href', realHref);
          if (realHref.startsWith('http')) {
            mainLink.setAttribute('target', '_blank');
            mainLink.setAttribute('rel', 'noopener noreferrer');
          }
        }
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

          if (a) {
            const realA = resolveRemoteUrl(a.getAttribute('href'), project, meta);
            a.setAttribute('href', realA);
          }
        });

        li.querySelectorAll('.search-breadcrumb-separator-final').forEach(sep => sep.remove());
      }

      // 3. Keep snippet below title
      const context = li.querySelector('.context');
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
      getMetadata().then(meta => processResults(meta));
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