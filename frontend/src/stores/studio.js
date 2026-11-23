import {request} from '../api/studio.js';

export const state = {account: null, sessions: [], readings: [], methods: [], diagnostics: [], acceptances: [], filter: '', ledgerFilter: '', detail: null};
export const writable = () => ['admin', 'analyst'].includes(state.account?.role);

export async function refresh() {
  const resources = ['sessions', 'readings', 'methods', 'diagnostics', 'acceptances'];
  const records = await Promise.all(resources.map(resource => request('/' + resource)));
  resources.forEach((resource, index) => { state[resource] = records[index]; });
}

export function signOut() {
  sessionStorage.removeItem('studio.token');
  Object.assign(state, {account: null, filter: '', ledgerFilter: '', detail: null, sessions: [], readings: [], methods: [], diagnostics: [], acceptances: []});
}
