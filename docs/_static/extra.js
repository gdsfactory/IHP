function syncViewerBg() {
  const color = getComputedStyle(document.body)
    .getPropertyValue('--md-code-bg-color').trim();
  document.querySelectorAll('iframe.viewer-3d').forEach(f => {
    // Send message to iframe's origin only
    f.contentWindow?.postMessage({ bg: color }, f.src.split('?')[0]);
  });
}

// reply to iframes that request the color on load
window.addEventListener('message', (e) => {
  // Validate origin before processing iframe requests
  if (e.origin === window.location.origin && e.data?.requestBg) {
    syncViewerBg();
  }
});

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(syncViewerBg, 100);
  new MutationObserver((mutations) => {
    for (const m of mutations) {
      if (m.attributeName === 'data-md-color-switching'
          && !document.body.hasAttribute('data-md-color-switching')) {
        syncViewerBg();
      }
    }
  }).observe(document.body, { attributes: true });
});
