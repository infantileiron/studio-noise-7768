export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, mark => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[mark]));
}
export const signed = value => value == null ? '—' : `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(3)}`;
export const level = value => Number(value).toFixed(2);
export const dateTime = value => value ? value.replace('T', ' ').slice(0, 16) : '—';
