import {checks, field, form, select} from '../components/common/forms.js';
import {empty, heading, status} from '../components/common/layout.js';
import {controls, predictor} from '../constants/labels.js';
import {state, writable} from '../stores/studio.js';
import {esc} from '../utils/format.js';

export function methods() {
  return `${heading('变量版本', '固定解释量与控制组，用相同口径复算底噪关联。', '<a class="secondary" href="#diagnostics">前往底噪诊断 →</a>')}
    <div class="split"><section class="bound"><div class="section-label"><h2>已登记版本</h2><span>${state.methods.length} 个版本</span></div>
    ${state.methods.map(item => `<article class="method-line"><span class="mono method-code">${esc(item.version)}</span><div><h3>${esc(item.title)}</h3><p>${esc(item.note)}</p><div class="chips">${status(`解释量 · ${predictor[item.predictor]}`, 'signal')}${item.controls.map(key => status(controls[key])).join('') || status('无控制量')}</div></div></article>`).join('') || empty('还没有变量版本', '选定解释量后保存一组可复用的控制变量。')}</section>
    <aside class="inset"><h2>${writable() ? '新建变量版本' : '控制口径'}</h2>${writable() ? form('methods',
    field('版本号', '<input name="version" placeholder="TRF-02" pattern="[A-Z0-9][A-Z0-9.\\-]{0,31}" required>') +
    field('版本标题', '<input name="title" maxlength="80" placeholder="同一时带比较车流" required>') +
    field('解释量', select('predictor', predictor)) + `<fieldset><legend>控制量</legend>${checks('controls', controls, ['band','hvac','position'])}</fieldset>` +
    field('使用说明', '<textarea name="note" rows="2" maxlength="350"></textarea>'), '保存变量版本') : '<p>控制量用分类哑变量编码。运行时检查控制矩阵秩及剩余自由度。</p>'}</aside></div>`;
}
