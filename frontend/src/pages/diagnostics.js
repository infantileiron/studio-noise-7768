import {checks, field, form, select} from '../components/common/forms.js';
import {empty, heading, status} from '../components/common/layout.js';
import {resultPanel} from '../components/correlation.js';
import {phase} from '../constants/labels.js';
import {state, writable} from '../stores/studio.js';
import {dateTime, esc} from '../utils/format.js';

export function diagnostics() {
  const run = state.detail;
  const methods = Object.fromEntries(state.methods.map(m => [m.id, `${m.version} · ${m.title}`]));
  const sessions = Object.fromEntries(state.sessions.map(s => [s.id, `${s.code} · ${s.title}（${s.reading_count} 条）`]));
  const queue = writable() && state.sessions.length && state.methods.length;
  const sidebar = `<aside class="inset"><h2>诊断单</h2>${state.diagnostics.length ? `<div class="run-list">${state.diagnostics.map(item => `<a href="#diagnostics/${item.id}" ${item.id === run?.id ? 'aria-current="page"' : ''}><strong>${esc(item.title)}</strong><small>${esc(item.version)} · ${phase[item.state]}</small></a>`).join('')}</div>` : '<p>提交诊断后，可在这里查看排队状态和计算结果。</p>'}</aside>`;
  let main;
  if (run) {
    const actions = `${['complete','blocked'].includes(run.state) ? '<button class="secondary" data-download>导出诊断 JSON</button>' : ''}${run.state === 'complete' ? `<a class="secondary" href="#retest/${run.id}">查看复测清单 →</a>` : ''}`;
    main = `<section class="bound"><div class="section-label"><div><h2>${esc(run.title)}</h2><p class="mono">${esc(run.version)} · ${dateTime(run.created_at)}</p></div>${status(phase[run.state], run.state === 'blocked' ? 'alert' : 'signal')}</div>${resultPanel(run)}<div class="panel-actions">${actions}</div></section>`;
  } else {
    main = `<section class="bound"><div class="section-label"><h2>提交后台计算</h2></div><div class="queue-form">${queue ? form('diagnostics',
      field('诊断名称', '<input name="title" maxlength="80" placeholder="A 棚车流与底噪 · 11 月复核" required>') +
      field('变量版本', select('method_id', methods, state.methods.find(m => m.version === 'TRF-01')?.id)) +
      `<fieldset><legend>纳入时段</legend>${checks('session_ids', sessions, Object.keys(sessions).filter(id => state.sessions.find(s => s.id === Number(id)).reading_count))}</fieldset>`, '提交诊断') :
      empty('等待可用诊断', writable() ? '先登记测量时段和变量版本，再提交诊断。' : '负责人发布后，可打开相应诊断单。')}</div></section>`;
  }
  return `${heading('底噪诊断', '对比同一组配对数据的原始相关和残差偏相关。', run && writable() ? '<a class="secondary" href="#diagnostics">新建诊断</a>' : '')}<div class="split diagnostic-split">${main}${sidebar}</div>`;
}
