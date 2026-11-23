import {checks, field, form, select} from '../components/common/forms.js';
import {empty, heading, status, table} from '../components/common/layout.js';
import {acceptPhase, exclusion, groupFlag, hvac, inclusion, phase, position, warnings} from '../constants/labels.js';
import {state, writable} from '../stores/studio.js';
import {dateTime, decibel, esc, signedDb} from '../utils/format.js';

function groupTable(groups) {
  const rows = groups.map(group => {
    const combo = `${hvac[group.hvac]} · ${position[group.position]}`;
    const overlap = group.overlap ? `${group.overlap[0]}–${group.overlap[1]}` : '—';
    const bins = group.bins.map(bin =>
      `<small>${bin.lo}–${bin.hi}：前 ${bin.pre_n} · 后 ${bin.post_n} · 权重 ${(bin.weight * 100).toFixed(0)}%</small>`).join('');
    const flags = group.flags.map(code => status(groupFlag[code], 'alert')).join('') || status('两期可比', 'signal');
    return `<tr><td><strong>${combo}</strong></td><td class="numeric">${group.pre_count} / ${group.post_count}</td>
      <td class="numeric">${overlap}</td><td class="bins">${bins || '—'}</td>
      <td class="numeric">${decibel(group.level_pre)}</td><td class="numeric">${decibel(group.level_post)}</td>
      <td class="numeric reading-level">${signedDb(group.reduction)}</td><td>${flags}</td></tr>`;
  });
  return table(['组合', '样本 前/后', '车流重叠', '归一车流档（辆/分钟）', '前等效 dB(A)', '后等效 dB(A)', '降噪 dB', '标记'],
    rows, 'groups-table');
}

function ledger(readings) {
  const filter = state.ledgerFilter;
  const visible = readings.filter(row => !filter || row.status === filter);
  const included = readings.filter(row => row.status === 'included').length;
  const rows = visible.map(row => `<tr>
    <td><strong class="mono">${esc(row.reference)}</strong><small>${esc(row.session)}</small></td>
    <td>${acceptPhase[row.phase]}</td><td>${hvac[row.hvac]} · ${position[row.position]}</td>
    <td class="numeric">${row.traffic}</td><td class="numeric reading-level">${decibel(row.noise)}</td>
    <td class="numeric">${row.bin ? `${row.bin[0]}–${row.bin[1]}` : '—'}</td>
    <td>${row.status === 'included' ? status(inclusion.included, 'signal') :
      status(`${inclusion.excluded} · ${exclusion[row.reason]}`, 'alert')}</td></tr>`);
  const summary = `纳入 ${included} 条，排除 ${readings.length - included} 条`;
  const picker = `<label class="select-inline"><span>对账</span>${select('ledger',
    {'': `全部 ${readings.length} 条`, included: '仅纳入', excluded: '仅排除'}, filter)}</label>`;
  return `<div class="section-label"><h2>逐条对账 <small>${summary}</small></h2>${picker}</div>
    ${visible.length ? table(['声测编号', '期', '组合', '车流／辆', 'LAeq／dB(A)', '车流档', '对账结果'], rows, 'readings-table')
    : empty('当前筛选没有读数', '调整对账筛选，或查看全部声测。')}`;
}

function resultPanel(run) {
  const result = run.result;
  if (!result) return '<div class="empty" role="status"><strong>已进入后台队列</strong><p>计算完成后会自动更新。两期声测快照已按同一时点锁定。</p></div>';
  if (!result.algorithm) return `<div class="notice" role="status">${warnings.CALCULATION_FAILED}</div>`;
  const overall = result.overall;
  const summary = !overall ? '当前两期样本找不到可比较的车流范围，降噪幅度无法给出。' :
    `按风机×测点分组并把两期归一到同一车流分布后，棚内等效声级${overall.reduction >= 0 ? '下降' : '反升'} ${Math.abs(overall.reduction).toFixed(2)} dB(A)，覆盖 ${overall.groups_used}／${overall.groups_total} 个组合。`;
  const headline = overall ? `<div class="coefficients">
    <div><span>降噪幅度</span><strong>${signedDb(overall.reduction)}<small> dB(A)</small></strong></div>
    <div><span>改造前等效声级</span><strong>${decibel(overall.level_pre)}<small> dB(A)</small></strong></div>
    <div><span>改造后等效声级</span><strong>${decibel(overall.level_post)}<small> dB(A)</small></strong></div>
    </div>` : '';
  return `<div class="result-body">${headline}<p class="interpretation">${summary}</p>
    ${result.warnings.map(code => `<p class="notice" data-warning="${code}">${warnings[code]}</p>`).join('')}
    <h3 class="subheading">分组归一结果</h3>${groupTable(result.groups)}
    <dl class="metadata"><div><dt>取数时点</dt><dd>${dateTime(result.taken_at)}</dd></div>
    <div><dt>两期样本</dt><dd>前 ${result.n_pre} 条 · 后 ${result.n_post} 条</dd></div>
    <div><dt>车流分档</dt><dd>${result.bin_width} 辆/分钟</dd></div>
    <div><dt>算法</dt><dd class="mono">${esc(result.algorithm)}</dd></div>
    <div class="digest"><dt>样本指纹</dt><dd class="mono">${esc(run.fingerprint)}</dd></div></dl></div>
    ${ledger(result.readings)}`;
}

export function acceptance() {
  const run = state.detail;
  const sessions = Object.fromEntries(state.sessions.map(s => [s.id, `${s.code} · ${s.title}（${s.reading_count} 条）`]));
  const sidebar = `<aside class="inset"><h2>验收单</h2>${state.acceptances.length ? `<div class="run-list">${state.acceptances.map(item => `<a href="#acceptance/${item.id}" ${item.id === run?.id ? 'aria-current="page"' : ''}><strong>${esc(item.title)}</strong><small>${phase[item.state]}${item.reviewed_at ? ' · 已发布' : ''}</small></a>`).join('')}</div>` : '<p>提交验收后，可在这里查看排队状态和降噪结果。</p>'}</aside>`;
  let main;
  if (run) {
    const actions = `${['complete', 'blocked'].includes(run.state) ? '<button class="secondary" data-download="acceptances">导出验收 JSON</button>' : ''}`;
    const decision = run.reviewed_at ? `<div class="decision"><h3>验收结论</h3><p>${esc(run.decision)}</p><small>${esc(run.reviewer)} · ${dateTime(run.reviewed_at)}</small></div>` :
      run.state === 'complete' && state.account.role === 'admin' ? form('publish-acceptance',
        field('验收结论', '<textarea name="text" rows="3" minlength="8" maxlength="500" placeholder="记录降噪是否达标、复验条件与签核意见。" required></textarea>'), '发布验收结论') :
        run.state === 'complete' ? '<p class="notice">等待业务负责人记录验收结论并发布。</p>' : '';
    main = `<section class="bound"><div class="section-label"><div><h2>${esc(run.title)}</h2><p class="mono">${esc(run.owner)} · ${dateTime(run.created_at)}</p></div>${status(phase[run.state], run.state === 'blocked' ? 'alert' : 'signal')}</div>${resultPanel(run)}<div class="panel-actions">${actions}</div>${decision ? `<div class="queue-form">${decision}</div>` : ''}</section>`;
  } else {
    const picker = name => `<fieldset><legend>${acceptPhase[name === 'pre_session_ids' ? 'pre' : 'post']}时段</legend>${checks(name, sessions)}</fieldset>`;
    main = `<section class="bound"><div class="section-label"><h2>提交验收计算</h2></div><div class="queue-form">${writable() && state.sessions.length ? form('acceptances',
      field('验收名称', '<input name="title" maxlength="80" placeholder="A 棚隔音改造 · 11 月验收" required>') +
      picker('pre_session_ids') + picker('post_session_ids') +
      '<p class="muted">同一时段不能算进两期；两期按提交时点同事务取数，补录可同时进行。</p>', '提交验收') :
      empty('等待可用验收', writable() ? '先登记测量时段并录入声测，再提交验收。' : '负责人发布后，可打开相应验收单。')}</div></section>`;
  }
  return `${heading('隔音改造验收', '改造前后各选一批时段，归一到同一车流分布后比较等效声级。', run && writable() ? '<a class="secondary" href="#acceptance">新建验收</a>': '')}<div class="split diagnostic-split">${main}${sidebar}</div>`;
}
