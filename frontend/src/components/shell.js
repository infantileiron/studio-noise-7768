import {role} from '../constants/labels.js';
import {pages} from '../router/pages.js';
import {esc} from '../utils/format.js';

export function shell(key, account, body, notice) {
  return `<header class="mast"><div class="mast-inner"><a href="#calendar" class="brand"><i aria-hidden="true">◉</i><span>伏声录制<small>FU SHENG STUDIO</small></span></a>
    <div class="account"><span title="${esc(account.email)}">${role[account.role]}</span><button class="signout" data-logout>退出</button></div></div></header>
    <nav aria-label="工作台" class="navigation"><div>${Object.entries(pages).map(([route, label]) => `<a href="#${route}" ${route === key ? 'aria-current="page"' : ''}>${label}</a>`).join('')}</div></nav>
    <main class="workspace"><p class="toast" role="status" ${notice ? '' : 'hidden'}>${esc(notice)}</p>${body}</main>`;
}
