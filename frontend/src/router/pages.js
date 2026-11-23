export const pages = {
  calendar: '测量日历', readings: '声测记录', methods: '变量版本', diagnostics: '底噪诊断', retest: '复测清单',
};
export function location() {
  const [key, id] = window.location.hash.slice(1).split('/');
  return {key: Object.hasOwn(pages, key) ? key : 'calendar', id: /^\d+$/.test(id ?? '') ? Number(id) : null};
}
