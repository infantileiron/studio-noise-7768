import {field, form, select} from '../components/common/forms.js';
import {empty, heading, status} from '../components/common/layout.js';
import {band} from '../constants/labels.js';
import {state, writable} from '../stores/studio.js';
import {esc} from '../utils/format.js';

export function calendar() {
  const days = Object.groupBy(state.sessions, item => item.recorded_on);
  const schedule = Object.entries(days).map(([day, items]) => `<section class="day-line"><h2><span>${esc(day.slice(5).replace('-', ' / '))}</span><small>${esc(day.slice(0, 4))}</small></h2><div>${items.map(item => `<article class="session-line">
    <time>${esc(item.start_time)}</time><div><h3>${esc(item.title)}</h3><p class="muted">${esc(item.code)} · ${esc(item.room)}</p>${item.note ? `<p class="session-note">${esc(item.note)}</p>` : ''}</div>
    <div class="session-meta">${status(band[item.band])}<a href="#readings" data-filter="${item.id}">${item.reading_count} 条声测 →</a></div></article>`).join('')}</div></section>`).join('');
  return `${heading('测量日历', '按录音时段归档一分钟无声测量。', '<a class="secondary" href="#readings">查看声测记录 →</a>')}
    <div class="split"><section class="bound"><div class="section-label"><h2>棚内时段</h2><span>${state.sessions.length} 个时段</span></div>${schedule || empty('等待首次测量', '建立一个录音时段后即可录入声测。')}</section>
    <aside class="inset"><h2>${writable() ? '登记录音时段' : '测量口径'}</h2>${writable() ? form('sessions',
      field('时段编号', '<input name="code" placeholder="FS-1121-A" pattern="[A-Z0-9][A-Z0-9\\-]{0,23}" required>') +
      field('时段名称', '<input name="title" maxlength="80" placeholder="清晨隔声门复测" required>') +
      `<div class="pair">${field('日期', '<input type="date" name="recorded_on" required>')}${field('开始时间', '<input type="time" name="start_time" required>')}</div>` +
      field('工作时带', select('band', band)) + field('录音棚', '<input name="room" maxlength="48" value="A 棚 · 临街间" required>') +
      field('备注', '<textarea name="note" maxlength="350" rows="2"></textarea>'), '保存时段') : '<p>棚内静音 60 秒，同时记录 LAeq 与经过临街窗的车辆数。每条声测归到具体录音时段。</p>'}</aside></div>`;
}
