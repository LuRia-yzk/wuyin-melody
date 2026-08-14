/* 老祖宗的 MBTI · 前端逻辑 */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const sections = {
    input: $('section-input'),
    bazi: $('section-bazi'),
    result: $('section-result'),
  };

  /* ---------- 工具 ---------- */
  function showSection(name) {
    Object.keys(sections).forEach((k) => {
      sections[k].classList.toggle('hidden', k !== name);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function setAccent(color) {
    if (color) {
      document.documentElement.style.setProperty('--accent', color);
      document.documentElement.style.setProperty('--accent-soft', hexToRgba(color, 0.1));
    }
  }
  function hexToRgba(hex, alpha) {
    const h = hex.replace('#', '');
    const n = parseInt(h, 16);
    const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function collectForm() {
    return {
      year: parseInt($('f-year').value, 10),
      month: parseInt($('f-month').value, 10),
      day: parseInt($('f-day').value, 10),
      hour: parseInt($('f-hour').value, 10),
      minute: parseInt($('f-minute').value || 0, 10),
      gender: $('f-gender').value,
    };
  }

  async function postJSON(url, body) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.detail || `请求失败 (${resp.status})`);
    }
    return resp.json();
  }

  function showError(el, msg) {
    el.textContent = msg;
    el.classList.remove('hidden');
  }

  /* ---------- 板块1 → 排盘 ---------- */
  $('birth-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = $('btn-submit');
    const errEl = $('form-error');
    errEl.classList.add('hidden');
    btn.disabled = true;
    btn.textContent = '排盘中…';
    try {
      const data = await postJSON('/api/bazi', collectForm());
      renderBazi(data);
      showSection('bazi');
    } catch (err) {
      showError(errEl, err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = '排 盘';
    }
  });

  let currentChart = null;
  let currentReport = null;

  function renderBazi(data) {
    const c = data.chart;
    const p = data.personality;
    currentChart = c;
    setAccent(p.wuxing['颜色']);

    const P = ['年柱', '月柱', '日柱', '时柱'];
    const G = ['年干', '月干', '日干', '时干'];
    const Z = ['年支', '月支', '日支', '时支'];

    /* ---- 五行色（天干/地支的格子底色，一眼看出分布） ---- */
    const WUXING_BG = {
      '木': 'rgba(47,107,63,0.22)', '火': 'rgba(192,57,43,0.22)',
      '土': 'rgba(184,134,11,0.22)', '金': 'rgba(127,140,141,0.22)', '水': 'rgba(31,97,141,0.22)',
    };
    const GAN_WX = { 甲: '木', 乙: '木', 丙: '火', 丁: '火', 戊: '土', 己: '土', 庚: '金', 辛: '金', 壬: '水', 癸: '水' };
    const ZHI_WX = { 子: '水', 丑: '土', 寅: '木', 卯: '木', 辰: '土', 巳: '火', 午: '火', 未: '土', 申: '金', 酉: '金', 戌: '土', 亥: '水' };

    /* ---- 四柱盘表格 ---- */
    const HI_COL = 2; // 日柱列
    const shishenGan = G.map((k) => c['十神(透干)'][k] || '');
    const tianGan = P.map((k) => ({ v: c['四柱'][k][0], wx: GAN_WX[c['四柱'][k][0]] }));
    const diZhi = P.map((k) => ({ v: c['四柱'][k][1], wx: ZHI_WX[c['四柱'][k][1]] }));
    const cangGan = Z.map((k) => (c['藏干'][k] || []).join(' '));
    const cangGanSS = Z.map((k) => (c['十神(藏干)'][k] || []).map((x) => x[1]).join(' '));
    const naYin = P.map((k) => c['纳音'][k] || '');
    const changSheng = Z.map((k) => c['十二长生'][k] || '');

    const gridRow = (label, cells, opts) => {
      const hiCol = opts && opts.hiCol;
      const dmCol = opts && opts.dayMaster;
      let html = `<div class="gr"><div class="gl">${label}</div>`;
      cells.forEach((cellData, i) => {
        const text = typeof cellData === 'object' ? cellData.v : cellData;
        const wx = typeof cellData === 'object' ? cellData.wx : null;
        const isHi = hiCol === i;
        const isDM = dmCol === i;
        let style = '';
        if (wx) style += `background:${WUXING_BG[wx]};`;
        if (isDM) style += 'font-weight:700;font-size:17px;';
        html += `<div class="gc${isHi ? ' hi' : ''}${isDM ? ' dm' : ''}"${style ? ` style="${style}"` : ''}>${text || '&nbsp;'}</div>`;
      });
      return html + `</div>`;
    };

    $('bazi-grid').innerHTML =
      `<div class="gr gr-head"><div class="gl"></div>` +
      P.map((k, i) => `<div class="gc${i === HI_COL ? ' hi' : ''}">${k.replace('柱', '')}</div>`).join('') + `</div>` +
      gridRow('十神', shishenGan, { hiCol: HI_COL }) +
      gridRow('天干', tianGan, { hiCol: HI_COL, dayMaster: HI_COL }) +
      gridRow('地支', diZhi, { hiCol: HI_COL }) +
      gridRow('藏干', cangGan, { hiCol: HI_COL }) +
      gridRow('藏干十神', cangGanSS, { hiCol: HI_COL }) +
      gridRow('纳音', naYin, { hiCol: HI_COL }) +
      gridRow('长生', changSheng, { hiCol: HI_COL });

    /* ---- 命理摘要 ---- */
    const wuxing = Object.entries(c['五行分布'])
      .map(([k, v]) => `${k}${v.toFixed(1)}`).join(' · ');
    const xiyong = (c['喜用神'] || {}).喜用神 || [];
    $('bazi-summary').innerHTML =
      `<div class="sum-line">` +
      `<span class="tag">日主 ${c['日主']}（${c['日主强弱']}）</span>` +
      `<span class="tag">格局 ${c['格局']['格名']}</span>` +
      `<span class="tag">喜用神 ${xiyong.join('、')}</span>` +
      `<span class="tag">空亡 ${c['空亡']['日柱旬空'] || ''}</span>` +
      `</div>` +
      `<div class="sum-line wuxing-line">${wuxing}</div>`;

    /* ---- 胎元 / 命宫 / 身宫 ---- */
    const t = c['胎元'], m = c['命宫'], s = c['身宫'];
    $('bazi-three').innerHTML =
      `<div class="three-item">胎元 <b>${t['干支']}</b><span>${t['纳音']}</span></div>` +
      `<div class="three-item">命宫 <b>${m['干支']}</b><span>${m['纳音']}</span></div>` +
      `<div class="three-item">身宫 <b>${s['干支']}</b><span>${s['纳音']}</span></div>`;

    /* ---- 神煞 ---- */
    $('bazi-shensha').innerHTML =
      `<div class="sub-title">神煞</div>` +
      `<div class="tag-list">${(c['神煞'] || []).map((x) => `<span class="tag">${x}</span>`).join('')}</div>`;

    /* ---- 大运 + 近10年流年 ---- */
    const dy = c['大运'] || {};
    const dyList = (dy['大运列表'] || []).map((d) =>
      `<span class="dy-item"><b>${d['干支']}</b>运 ${d['起止']}（${d['年龄']}·${d['十神']}）</span>`
    ).join('');
    const ln = (c['近10年流年'] || []).map((x) => `${x.year}${x['ganzhi']}`).join(' · ');
    $('bazi-dayun').innerHTML =
      `<div class="sub-title">大运</div>` +
      `<div class="dy-meta">${dy['顺逆']} · ${dy['起运']}起运${dy['起运公历'] ? '（' + dy['起运公历'] + '）' : ''}</div>` +
      `<div class="dy-list">${dyList}</div>` +
      `<div class="sub-title">近10年流年</div>` +
      `<div class="ln-list">${ln}</div>`;

    /* ---- 类型揭晓 ---- */
    $('type-code').textContent = p.type_code;
    $('type-name').textContent = p['type_name'];
    $('type-tag').textContent = p['type_tag'];
    $('type-slogan').textContent = p.slogan;
    $('type-tags').innerHTML =
      `<span class="tag">${p.wuxing['五行']} · ${p.wuxing['意象']}</span>` +
      `<span class="tag">${p.shishen['主导类']}主导</span>` +
      `<span class="tag">${p.strength}</span>`;
  }

  /* ---------- 板块2 → 性格分析 ---------- */
  $('btn-analyze').addEventListener('click', async () => {
    const btn = $('btn-analyze');
    btn.disabled = true;
    showSection('result');
    $('loading').classList.remove('hidden');
    $('report').classList.add('hidden');
    try {
      const report = await postJSON('/api/analyze', collectForm());
      renderResult(report);
    } catch (err) {
      $('loading').classList.add('hidden');
      $('report').classList.remove('hidden');
      $('report').innerHTML = `<p style="color:#b03030;text-align:center">分析失败：${err.message}<br>请重试</p>`;
    } finally {
      btn.disabled = false;
      $('loading').classList.add('hidden');
    }
  });

  function renderResult(r) {
    currentReport = r;
    setAccent(r.wuxing['颜色']);
    const a = r.analysis;

    const dimsHtml = Object.entries(r.dimensions || {})
      .map(([label, val]) => `
        <div class="dim-bar">
          <div class="dim-label"><span>${label}</span><span>${val}</span></div>
          <div class="dim-track"><div class="dim-fill" style="width:${Math.min(100, Math.max(0, val))}%"></div></div>
        </div>`)
      .join('');

    $('report').innerHTML = `
      <div class="report-head">
        <div class="r-name">${r['type_name']} · ${r['type_tag']}</div>
        <div class="r-tag">${r.type_code}</div>
      </div>
      <div class="r-section"><h4>核心特质</h4><p>${a.core_traits}</p></div>
      <div class="r-section"><h4>你的超能力</h4><p>${a.superpower}</p></div>
      <div class="r-section"><h4>潜在盲点</h4><p>${a.blind_spot}</p></div>
      <div class="r-section"><h4>最佳相处方式</h4><p>${a.relationship}</p></div>
      <div class="r-section"><div class="r-saying">${a.old_saying}</div></div>
      <div class="r-section"><h4>能量维度</h4>${dimsHtml}</div>`;

    $('report').classList.remove('hidden');
    renderShareCard(r);
    setTimeout(() => {
      document.getElementById('share-card').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
  }

  /* ---------- 分享卡 ---------- */
  function renderShareCard(r) {
    const a = r.analysis;
    const dimsHtml = Object.entries(r.dimensions || {})
      .map(([label, val]) => `
        <div class="dim-bar">
          <div class="dim-label"><span>${label}</span><span>${val}</span></div>
          <div class="dim-track"><div class="dim-fill" style="width:${Math.min(100, Math.max(0, val))}%"></div></div>
        </div>`)
      .join('');

    $('share-card').innerHTML = `
      <div class="card-top">老祖宗的 MBTI · 命格性格</div>
      <div class="card-body">
        <div class="card-icon">☯</div>
        <div class="card-code">${r.type_code}</div>
        <div class="card-name">${r['type_name']}</div>
        <div class="card-tag">${r['type_tag']}</div>
        <div class="card-slogan">${r.slogan}</div>
        <div class="card-dims">${dimsHtml}</div>
        <div class="card-saying">${a.old_saying}</div>
      </div>
      <div class="card-foot">${r.bazi_summary}</div>`;
  }

  /* ---------- 返回导航 ---------- */
  $('btn-back-input').addEventListener('click', () => showSection('input'));
  $('btn-back-bazi').addEventListener('click', () => showSection('bazi'));

  /* ---------- 再测一次 ---------- */
  $('btn-retest').addEventListener('click', () => {
    showSection('input');
    $('report').classList.add('hidden');
  });

  /* ---------- 复制排盘信息 ---------- */
  function buildBaziText(c) {
    const P = ['年柱', '月柱', '日柱', '时柱'];
    const G = ['年干', '月干', '日干', '时干'];
    const Z = ['年支', '月支', '日支', '时支'];
    const bazi = P.map((k) => c['四柱'][k]).join(' ');
    const shishenGan = G.map((k) => c['十神(透干)'][k]).join(' ');
    const tianGan = P.map((k) => c['四柱'][k][0]).join(' ');
    const diZhi = P.map((k) => c['四柱'][k][1]).join(' ');
    const cangGan = Z.map((k) => (c['藏干'][k] || []).join('')).join(' ');
    const cangGanSS = Z.map((k) => (c['十神(藏干)'][k] || []).map((x) => x[1]).join('·')).join(' ');
    const naYin = P.map((k) => c['纳音'][k]).join(' ');
    const changSheng = Z.map((k) => c['十二长生'][k]).join(' ');
    const xiyong = (c['喜用神']['喜用神'] || []).join('、');
    const kong = c['空亡']['日柱旬空'];
    const shensha = (c['神煞'] || []).join('、');
    const dy = c['大运'];
    const dyList = (dy['大运列表'] || []).map((d) =>
      `  ${d['干支']}运 ${d['起止']}（${d['年龄']}·${d['十神']}）`).join('\n');
    const ln = (c['近10年流年'] || []).map((x) => `${x.year}${x['ganzhi']}`).join(' ');
    const wuxing = Object.entries(c['五行分布']).map(([k, v]) => `${k}${v.toFixed(1)}`).join(' ');

    return `【八字排盘】${bazi}（${c['出生信息']['公历']} ${c['出生信息']['性别']}）
日主：${c['日主']}（${c['日主强弱']}）

天干十神：${shishenGan}
天干：${tianGan}
地支：${diZhi}
藏干：${cangGan}
藏干十神：${cangGanSS}
纳音：${naYin}
空亡：日柱旬空 ${kong}
十二长生：${changSheng}
胎元/命宫/身宫：${c['胎元']['干支']} / ${c['命宫']['干支']} / ${c['身宫']['干支']}
格局：${c['格局']['格名']}
喜用神：${xiyong}
五行分布：${wuxing}
神煞：${shensha}

大运：${dy['顺逆']} ${dy['起运']}起运
${dyList}

近10年流年：${ln}`;
    return text;
  }

  function buildPersonalityText(p) {
    const dims = Object.entries(p.dimensions || {})
      .map(([k, v]) => `${k} ${v}`).join('  ');
    return `【命格性格类型】
类型码：${p.type_code}
类型：${p['type_name']} · ${p['type_tag']}
Slogan：${p.slogan}
能量维度：${dims}`;
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // 降级：临时 textarea + execCommand
    return new Promise((resolve, reject) => {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); resolve(); }
      catch (e) { reject(e); }
      document.body.removeChild(ta);
    });
  }

  function handleCopy(btnId, getText, doneText) {
    if (!currentChart && !currentReport) return;
    const btn = $(btnId);
    copyText(getText()).then(() => {
      btn.textContent = '已复制 ✓';
      setTimeout(() => { btn.textContent = doneText; }, 1500);
    }).catch(() => {
      btn.textContent = '复制失败';
      setTimeout(() => { btn.textContent = doneText; }, 1500);
    });
  }
  $('btn-copy-bazi').addEventListener('click', () =>
    handleCopy('btn-copy-bazi', () => buildBaziText(currentChart), '复制排盘信息'));
  $('btn-copy-bazi-result').addEventListener('click', () =>
    handleCopy('btn-copy-bazi-result', () => buildPersonalityText(currentReport), '复制性格类型'));
})();
