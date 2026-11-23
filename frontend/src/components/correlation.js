import {band, controls, predictor, warnings} from '../constants/labels.js';
import {esc, signed} from '../utils/format.js';

export function resultPanel(run) {
  const result = run.result;
  if (!result) return '<div class="empty" role="status"><strong>已进入后台队列</strong><p>计算完成后会自动更新。声测快照已锁定。</p></div>';
  if (!result.columns) return `<div class="notice" role="status">${warnings.CALCULATION_FAILED}</div>`;
  const summary = result.partial == null ? '当前样本和控制量组合无法得到有效偏相关。' :
    `控制后关联绝对值${result.absolute_drop >= 0 ? '下降' : '上升'} ${Math.abs(result.absolute_drop).toFixed(3)}。系数反映样本中的线性关联，复测需固定现场条件。`;
  const charts = `<div class="plot-grid">
    <section><h3>原始配对</h3><canvas data-plot="raw" role="img" aria-label="原始${predictor[run.predictor]}与底噪散点图"></canvas><p>${predictor[run.predictor]} × LAeq</p></section>
    ${result.partial == null ? '' : '<section><h3>控制后的残差</h3><canvas data-plot="partial" role="img" aria-label="控制后两变量残差散点图"></canvas><p>解释量残差 × LAeq 残差</p></section>'}</div>`;
  return `<div class="result-body"><div class="coefficients">
    <div><span>原始 Pearson r</span><strong data-coef="raw">${signed(result.raw)}</strong></div>
    <div><span>残差偏相关 r</span><strong data-coef="partial">${signed(result.partial)}</strong></div>
    <div><span>配对样本</span><strong>${result.n}<small> 条</small></strong></div>
    </div><p class="interpretation">${summary}</p>${result.warnings.map(code => `<p class="notice" data-warning="${code}">${warnings[code]}</p>`).join('')}
    ${result.rows.length ? charts : ''}
    ${result.rows.length ? `<div class="legend">${Object.entries(band).map(([key,label]) => `<span><i class="${key}"></i>${label}</span>`).join('')}</div>` : ''}
    <dl class="metadata"><div><dt>解释量</dt><dd>${predictor[run.predictor]}</dd></div><div><dt>控制组</dt><dd>${Object.keys(result.levels).map(key => controls[key]).join('、') || '无'}</dd></div><div><dt>矩阵秩／列数</dt><dd data-rank>${result.rank} / ${result.columns.length}</dd></div><div><dt>残差自由度</dt><dd>${result.df ?? '—'}</dd></div><div class="digest"><dt>样本指纹</dt><dd class="mono">${esc(run.fingerprint)}</dd></div></dl></div>`;
}

export function drawPlots(run) {
  if (!run?.result?.rows?.length) return;
  const colors = {early: '#a36638', day: '#405946', late: '#9a493b'};
  for (const canvas of document.querySelectorAll('canvas[data-plot]')) {
    const residual = canvas.dataset.plot === 'partial';
    const rows = run.result.rows.map(row => ({x: residual ? row.rx : row.x, y: residual ? row.ry : row.y, band: row.band}));
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (width < 60 || height < 60) continue;
    const density = window.devicePixelRatio;
    canvas.width = width * density;
    canvas.height = height * density;
    const ctx = canvas.getContext('2d');
    ctx.scale(density, density);
    const pad = {left: 42, right: 16, top: 12, bottom: 27};
    const plotWidth = width - pad.left - pad.right;
    const plotHeight = height - pad.top - pad.bottom;
    const bounds = measure => {
      const values = rows.map(row => row[measure]);
      const min = Math.min(...values), max = Math.max(...values);
      const margin = Math.max((max - min) * 0.08, 0.25);
      return [min - margin, max + margin];
    };
    const [xmin, xmax] = bounds('x'), [ymin, ymax] = bounds('y');
    ctx.font = '11px "IBM Plex Mono", monospace';
    ctx.fillStyle = '#665a47';
    ctx.strokeStyle = '#d6c9ad';
    for (let index = 0; index <= 4; index++) {
      const ratio = index / 4;
      const x = pad.left + plotWidth * ratio, y = pad.top + plotHeight * (1 - ratio);
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();
      ctx.textAlign = 'right';
      ctx.fillText((ymin + ratio * (ymax - ymin)).toFixed(1), pad.left - 6, y + 4);
      ctx.textAlign = 'center';
      ctx.fillText((xmin + ratio * (xmax - xmin)).toFixed(1), x, height - 9);
    }
    for (const row of rows) {
      const x = pad.left + plotWidth * (row.x - xmin) / (xmax - xmin);
      const y = pad.top + plotHeight * (ymax - row.y) / (ymax - ymin);
      ctx.beginPath();
      ctx.fillStyle = colors[row.band];
      ctx.globalAlpha = 0.7;
      ctx.arc(x, y, 3.7, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}
