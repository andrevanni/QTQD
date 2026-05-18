const CACHE = 'qtqd-v11';
const STATIC = [
  '/cliente',
  '/cliente/styles.css',
  '/cliente/script.js',
  '/cliente/chart_builder.js',
  '/cliente/manifest.json',
  '/cliente/assets/logo_alta.jpg',
  '/shared/app_config.js',
  '/shared/api_client.js',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  // API: sempre rede
  if (e.request.url.includes('/api/')) {
    e.respondWith(fetch(e.request));
    return;
  }
  // Network-first: busca da rede, atualiza cache, cai no cache só se offline
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok && e.request.method === 'GET') {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }).catch(() => caches.match(e.request))
  );
});
