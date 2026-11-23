import {esc} from '../../utils/format.js';

export const field = (label, input) => `<label><span>${label}</span>${input}</label>`;
export function options(values, current) {
  return Object.entries(values).map(([value, label]) => `<option value="${esc(value)}" ${String(current) === value ? 'selected' : ''}>${esc(label)}</option>`).join('');
}
export const select = (name, values, selected, placeholder = '') => `<select name="${name}" required>${placeholder ? `<option value="">${placeholder}</option>` : ''}${options(values, selected)}</select>`;
export const checks = (name, values, selected = []) => Object.entries(values).map(([value, label]) =>
  `<label class="check"><input type="checkbox" name="${name}" value="${esc(value)}" ${selected.includes(value) ? 'checked' : ''}><span>${esc(label)}</span></label>`).join('');
export function form(resource, content, button) {
  return `<form data-resource="${resource}" class="stack">${content}<p class="form-error" role="alert" hidden></p><button type="submit" class="primary">${button}</button></form>`;
}
