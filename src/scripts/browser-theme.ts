// Shared by the parser-time bootstrap and the live theme controller.
export function syncBrowserTheme() {
  const root = document.documentElement;
  const values = {
    'theme-color': getComputedStyle(root).getPropertyValue('--surface').trim(),
    'color-scheme': root.dataset.theme === 'dark' ? 'dark' : 'light',
  };
  for (const [name, value] of Object.entries(values)) {
    const metas = [...document.head.querySelectorAll<HTMLMetaElement>(`meta[name="${name}"]`)];
    const meta = metas.shift() ?? document.createElement('meta');
    meta.name = name;
    meta.removeAttribute('media');
    meta.content = value;
    if (!meta.parentNode) document.head.append(meta);
    for (const extra of metas) extra.remove();
  }
}
