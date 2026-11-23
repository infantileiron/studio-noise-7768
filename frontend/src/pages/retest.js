import {field, form} from '../components/common/forms.js';
import {empty, heading, status} from '../components/common/layout.js';
import {state} from '../stores/studio.js';
import {dateTime, esc, signed} from '../utils/format.js';

export function retest() {
  const candidates = state.diagnostics.filter(run => run.state === 'complete');
  const run = state.detail;
  const detail = run?.state === 'complete' ? `<div class="retest-detail"><h2>${esc(run.title)}</h2><p>${status(run.reviewed_at ? '已发布' : '待复核', 'signal')}</p>
    <dl class="metadata"><div><dt>变量版本</dt><dd>${esc(run.version)}</dd></div><div><dt>配对样本</dt><dd>${run.result.n} 条</dd></div><div><dt>原始 r</dt><dd>${signed(run.result.raw)}</dd></div><div><dt>控制后 r</dt><dd>${signed(run.result.partial)}</dd></div></dl>
    ${run.reviewed_at ? `<div class="decision"><h3>隔音复测安排</h3><p>${esc(run.decision)}</p><small>${esc(run.reviewer)} · ${dateTime(run.reviewed_at)}</small></div><button class="secondary" data-download>导出发布清单</button>` :
      state.account.role === 'admin' ? form('publish', field('隔音复测安排', '<textarea name="text" rows="4" minlength="8" maxlength="500" placeholder="记录复测时间、固定的风机档位和测点，以及需复验的现场条件。" required></textarea>'), '发布复测清单') : '<p class="notice">等待业务负责人记录复测安排并发布。</p>'}
    <a class="text-link" href="#diagnostics/${run.id}">返回计算证据 →</a></div>` : empty('请选择一张诊断单', '计算完成后，业务负责人可记录隔音复测安排并发布。');
  return `${heading('隔音复测清单', '复核关联变化，安排固定时段、风机与测点的复测。')}
    <div class="split"><section class="bound"><div class="section-label"><h2>复测安排</h2></div>${detail}</section>
    <aside class="inset"><h2>可复核诊断</h2>${candidates.length ? `<div class="run-list">${candidates.map(item => `<a href="#retest/${item.id}" ${item.id === run?.id ? 'aria-current="page"' : ''}><strong>${esc(item.title)}</strong><small>${item.reviewed_at ? '已发布' : '待复核'} · ${esc(item.version)}</small></a>`).join('')}</div>` : '<p>当前没有可阅的复测安排。</p>'}</aside></div>`;
}
