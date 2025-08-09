const API_BASE = process.env.REACT_APP_API_URL;

export async function api(path, init) {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const contentType = res.headers.get('content-type') || '';
  return contentType.includes('application/json') ? res.json() : res.text();
}