import {form, field} from '../components/common/forms.js';

export function login() {
  return `<main class="login">
    <section class="cover"><div class="cover-name">伏声录制 <span>FU SHENG STUDIO</span></div>
      <div class="tape" aria-hidden="true"><div class="tape-label"><b>ROOM TONE</b><span>LAeq · 60 s</span></div><div class="reel-pair"><i></i><div></div><i></i></div><div class="tape-foot"></div></div>
      <div class="cover-foot"><span>A 棚 · 临街间</span><span>底噪测量手册</span></div>
    </section>
    <section class="sign"><div class="sign-inner"><h1>棚内底噪归因</h1><p>记录同一分钟的声级与车流，比较不同风机档位和测点的底噪关联。</p>
      ${form('login', field('账号邮箱', '<input name="email" type="email" autocomplete="username" placeholder="analyst@demo.local" required>') +
        field('密码', '<input name="password" type="password" autocomplete="current-password" required>'), '进入工作台')}
      <div class="demo-access"><span>演示账号</span><div><button class="text-button" type="button" data-demo="analyst">声测分析员</button><button class="text-button" type="button" data-demo="admin">业务负责人</button><button class="text-button" type="button" data-demo="viewer">观察员</button></div></div>
    </div></section></main>`;
}
