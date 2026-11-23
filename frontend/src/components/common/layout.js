import {esc} from '../../utils/format.js';

export function heading(title, help, actions = '') {
  return `<header class="page-heading"><div><h1>${title}</h1><p>${help}</p></div>${actions}</header>`;
}
export function empty(title, help) {
  return `<div class="empty"><strong>${title}</strong><p>${help}</p></div>`;
}
export function status(label, tone = '') {
  return `<span class="status ${tone}">${esc(label)}</span>`;
}
export function table(headings, rows, minimum = '') {
  return `<div class="table-wrap" tabindex="0" aria-label="可横向滚动的表格"><table class="${minimum}"><thead><tr>${headings.map(heading => `<th scope="col">${heading}</th>`).join('')}</tr></thead><tbody>${rows.join('')}</tbody></table></div>`;
}
