export const payload = {
  sessions: form => Object.fromEntries(form),
  readings: form => ({...Object.fromEntries(form),
    session_id: Number(form.get('session_id')), traffic: Number(form.get('traffic')), noise: Number(form.get('noise')),
  }),
  methods: form => ({...Object.fromEntries(form), controls: form.getAll('controls')}),
  diagnostics: form => ({title: form.get('title'), method_id: Number(form.get('method_id')),
    session_ids: form.getAll('session_ids').map(Number),
  }),
  acceptances: form => ({title: form.get('title'),
    pre_session_ids: form.getAll('pre_session_ids').map(Number),
    post_session_ids: form.getAll('post_session_ids').map(Number),
  }),
};
