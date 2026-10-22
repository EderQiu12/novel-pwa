const CACHE = 'novel-pwa-v1';
const ASSETS = [
  './',
  './index.html',
  './novels.json',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/favicon-32.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // 页面导航 + 小说数据：网络优先（联网时打开即最新版），离线回退缓存
  if (req.mode === 'navigate' || url.pathname.endsWith('/novels.json')) {
    const fallback = req.mode === 'navigate'
      ? caches.match('./index.html', { ignoreSearch: true })
      : caches.match(req, { ignoreSearch: true });
    e.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
          return res;
        })
        .catch(() => fallback)
    );
    return;
  }

  // 其余静态资源：缓存优先
  e.respondWith(
    caches.match(req, { ignoreSearch: true }).then(hit =>
      hit ||
      fetch(req).then(res => {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
        return res;
      })
    )
  );
});
