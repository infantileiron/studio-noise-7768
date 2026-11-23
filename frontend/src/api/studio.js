export async function request(path, {body, raw = false} = {}) {
  const token = sessionStorage.getItem('studio.token');
  const headers = token ? {Authorization: `Bearer ${token}`} : {};
  if (body) headers['Content-Type'] = 'application/json';
  const response = await fetch(`/api${path}`, {
    method: body ? 'POST' : 'GET', headers, body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = Array.isArray(data.detail) ? data.detail.map(item => `${item.loc.at(-1)}：${item.msg}`).join('；') : data.detail;
    const error = new Error(detail || '请求未成功，请检查连接后重试');
    error.status = response.status;
    throw error;
  }
  return raw ? response : response.json();
}
