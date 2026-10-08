#!/usr/bin/env node
// Generator raportu HTML skill-scout (jasny styl „papier i tusz”).
// Wejście: JSON z kandydatami na skille. Wyjście: Raporty/raport-aktualny.html + Raporty/YYYY-MM-DD.html.
// Użycie: node generate-raport.mjs <ścieżka-do-json>

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const fmtDate = (iso) => {
  const p = String(iso || '').slice(0, 10).split('-');
  return p.length === 3 ? `${p[2]}.${p[1]}` : '';
};

// STATE_DIR MUSI celować w ŻYWY vault (Obsidian Sync), NIE w realpath symlinka .claude → vault-git.
// Node rozwija symlink w __dirname — kotwiczymy w cwd / markerze .obsidian.
function vaultRoot() {
  if (process.env.SKILL_SCOUT_WORKSPACE) return resolve(process.env.SKILL_SCOUT_WORKSPACE);
  if (process.env.CLAUDE_CRON_WORKSPACE) return resolve(process.env.CLAUDE_CRON_WORKSPACE);
  let cur = process.cwd();
  for (let i = 0; i < 8; i++) {
    if (existsSync(join(cur, '.obsidian'))) return cur;
    const parent = dirname(cur);
    if (parent === cur) break;
    cur = parent;
  }
  return process.cwd();
}
const STATE_DIR = join(vaultRoot(), 'Zasoby/raporty/skill-scout');
const RAPORTY = join(STATE_DIR, 'Raporty');
const todayISO = () => new Date().toISOString().slice(0, 10);

const DATA = process.argv[2] ? resolve(process.argv[2]) : join(STATE_DIR, 'data', `${todayISO()}.json`);

const esc = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const fmtMin = (m) => {
  const v = Number(m) || 0;
  if (v >= 60) return `${(v / 60).toFixed(v % 60 ? 1 : 0)} h`;
  return `${v} min`;
};
// Klasa priorytetu: tusz / jasna / wyblakła.
const prioCls = (p) => (p >= 120 ? 'sc-hot' : p >= 40 ? 'sc-mid' : 'sc-low');

// Oszczędność i priorytet liczy kod, nie model: freq × minuty na przebieg.
function withScore(c) {
  const saved = Math.round((Number(c.freq) || 0) * (Number(c.minutes_per_run) || 0));
  return { ...c, saved_per_week_min: saved, priority: saved };
}

function card(c, isHistory = false) {
  const isUpdate = c.type === 'update';
  const tag = isUpdate
    ? `<span class="tag tag-up">UPDATE · ${esc(c.update_target || '?')}</span>`
    : `<span class="tag">NOWY SKILL</span>`;
  const prio = Number(c.priority) || 0;
  const evidence = Array.isArray(c.evidence) && c.evidence.length
    ? `<ul class="ev">${c.evidence.map((e) => `<li>${esc(e)}</li>`).join('')}</ul>`
    : '';
  const slug = c.slug ? `<code class="slug">/${esc(c.slug)}</code>` : '';
  const since = isHistory && c.first_proposed
    ? `<span class="since">typowany od ${fmtDate(c.first_proposed)}</span>` : '';

  return `<article class="card${isHistory ? ' hist' : ''}" data-prio="${prio}" data-freq="${Number(c.freq) || 0}">
    <div class="body">
      <div class="chips">
        ${tag}
        <span class="score ${prioCls(prio)}">prio ${prio}</span>
        ${since}
        <span class="sub">${slug}</span>
      </div>
      <h3 class="title">${esc(c.title)}</h3>
      <div class="meta">
        <span class="m-up">↻ ${Number(c.freq) || 0}× w oknie</span>
        <span>⏱ ${fmtMin(c.minutes_per_run)}/raz</span>
        <span>💰 ~${fmtMin(c.saved_per_week_min)}/tydz</span>
      </div>
      ${c.what ? `<p class="summary">${esc(c.what)}</p>` : ''}
      ${evidence ? `<details class="ev-wrap"><summary>Dowód (${c.evidence.length})</summary>${evidence}</details>` : ''}
    </div>
  </article>`;
}

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Inter:wght@400;500;600;700&display=swap');
  :root {
    color-scheme: light;
    --ink: #141414; --canvas: #FAF8F4; --surface: #FFFFFF; --alt: #F6F3EC;
    --accent: #E8590C; --muted: #6E6A61; --line: #E5E1D8;
  }
  * { box-sizing: border-box; margin: 0; }
  body {
    background: var(--canvas); color: var(--ink);
    background-image: linear-gradient(rgba(20,20,20,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(20,20,20,.045) 1px, transparent 1px);
    background-size: 32px 32px;
    font: 16px/1.55 Inter, -apple-system, 'Segoe UI', sans-serif;
    padding: 56px 16px 80px; max-width: 680px; margin: 0 auto;
    -webkit-font-smoothing: antialiased;
  }
  .overline { font: 700 11px/1.3 Inter; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
  h1 { font: 400 32px/1.1 'Archivo Black', sans-serif; text-transform: uppercase; letter-spacing: -.02em; margin: 8px 0 6px; text-wrap: balance; }
  h1 .accent { background: var(--accent); color: #fff; padding: 0 6px; }
  .sub-head { color: var(--muted); font-size: 14px; }

  .funnel { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 28px 0 36px; }
  .stat { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 16px 14px; box-shadow: 0 2px 8px rgba(20,20,20,.05); }
  .stat b { display: block; font: 400 26px/1 'Archivo Black', sans-serif; font-variant-numeric: tabular-nums; }
  .stat.accent b { color: var(--accent); }
  .stat .lab { display: block; color: var(--muted); font-size: 11.5px; margin-top: 7px; line-height: 1.3; }

  .listhead { display: flex; align-items: center; justify-content: space-between; gap: 12px; font: 600 13px/1.2 Inter; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 14px; flex-wrap: wrap; }
  .sortbar { display: flex; gap: 4px; background: var(--surface); border: 1px solid var(--line); border-radius: 9999px; padding: 3px; }
  .sortbtn { border: none; cursor: pointer; background: transparent; color: var(--muted); border-radius: 9999px; padding: 7px 13px; font: 700 11.5px/1 Inter; }
  .sortbtn:hover { color: var(--ink); }
  .sortbtn.on { background: var(--ink); color: #fff; }
  .sortbtn:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 14px; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(20,20,20,.06); }
  .body { padding: 20px 22px; }

  .chips { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
  .tag { background: var(--accent); color: #fff; border-radius: 9999px; padding: 4px 11px; font: 700 10.5px/1.3 Inter; text-transform: uppercase; letter-spacing: .05em; }
  .tag-up { background: var(--surface); color: var(--ink); box-shadow: inset 0 0 0 1.5px var(--ink); }
  .score { border-radius: 9999px; padding: 4px 10px; font: 700 11.5px/1.3 Inter; font-variant-numeric: tabular-nums; }
  .sc-hot { background: var(--ink); color: #fff; }
  .sc-mid { background: var(--alt); color: var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
  .sc-low { background: var(--alt); color: var(--muted); }
  .sub { margin-left: auto; color: var(--muted); font: 600 12px/1.3 Inter; }
  .slug { background: var(--alt); border: 1px solid var(--line); border-radius: 7px; padding: 2px 7px; font: 600 12px/1.3 ui-monospace, monospace; color: var(--ink); }
  .since { color: var(--muted); font: 600 11px/1.3 Inter; }

  .section-h { font: 700 13px/1.2 Inter; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 36px 0 14px; padding-top: 8px; }
  .section-h.fresh { color: var(--accent); }
  .card.hist { opacity: .78; }

  .title { font: 700 19px/1.3 Inter, sans-serif; letter-spacing: -.01em; text-wrap: balance; color: var(--ink); }
  .meta { display: flex; gap: 14px; margin: 10px 0 14px; color: var(--muted); font: 600 12.5px/1.3 Inter; font-variant-numeric: tabular-nums; flex-wrap: wrap; }
  .m-up { color: var(--accent); }
  .summary { color: #2b2925; font-size: 14.5px; line-height: 1.62; }

  .ev-wrap { margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
  .ev-wrap summary { cursor: pointer; color: var(--muted); font: 600 12.5px/1 Inter; }
  .ev-wrap summary:hover { color: var(--accent); }
  .ev { margin: 12px 0 0; padding-left: 18px; color: var(--muted); font-size: 13px; line-height: 1.6; }
  .ev li { margin-bottom: 5px; }

  .empty { color: var(--muted); background: var(--surface); border: 1px solid var(--line); border-radius: 14px; padding: 32px; text-align: center; }
  @media (max-width: 480px) { .funnel { grid-template-columns: 1fr; } }
`;

const SORT_JS = `
  (function () {
    var box = document.getElementById('cards');
    if (!box) return;
    var btns = document.querySelectorAll('.sortbtn');
    function sortCards(mode) {
      var arr = Array.prototype.slice.call(box.children);
      arr.sort(function (a, b) {
        if (mode === 'freq') return (+b.dataset.freq) - (+a.dataset.freq);
        return (+b.dataset.prio) - (+a.dataset.prio);
      });
      arr.forEach(function (c) { box.appendChild(c); });
    }
    btns.forEach(function (btn) {
      btn.addEventListener('click', function () {
        btns.forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on');
        sortCards(btn.dataset.sort);
      });
    });
  })();
`;

function page(title, body) {
  return `<!DOCTYPE html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>${esc(title)}</title>
<style>${CSS}</style></head><body>${body}<script>${SORT_JS}</script></body></html>`;
}

function loadHistory() {
  try {
    const j = JSON.parse(readFileSync(join(STATE_DIR, '_proposed.json'), 'utf8'));
    return Array.isArray(j.proposed) ? j.proposed : [];
  } catch {
    return [];
  }
}

function main() {
  let data = { candidates: [], stats: {} };
  try {
    data = JSON.parse(readFileSync(DATA, 'utf8'));
  } catch {
    console.error(`✗ Nie wczytano danych: ${DATA}`);
    process.exit(1);
  }
  mkdirSync(RAPORTY, { recursive: true });

  const byPrio = (a, b) => (Number(b.priority) || 0) - (Number(a.priority) || 0);
  // NOWE w tym przebiegu (na górze).
  const fresh = (Array.isArray(data.candidates) ? data.candidates : []).map(withScore).sort(byPrio);
  const freshSlugs = new Set(fresh.map((c) => c.slug));
  // HISTORIA: wcześniej wytypowane (poniżej). Czytane z _proposed.json PRZED dopisaniem nowych.
  // Odsiewamy te, które i tak są w sekcji "nowe", żeby nie dublować.
  const history = loadHistory().filter((c) => !freshSlugs.has(c.slug)).map(withScore).sort(byPrio);

  const intents = data.stats?.intents ?? '–';
  const freshSaved = fresh.reduce((s, c) => s + (Number(c.saved_per_week_min) || 0), 0);
  const savedLabel = freshSaved >= 60 ? `${(freshSaved / 60).toFixed(1).replace(".", ",")} h` : `${freshSaved} min`;

  const freshSection = fresh.length
    ? `<div class="section-h fresh">🆕 Nowe w tym tygodniu (${fresh.length})</div>
       <div id="cards">${fresh.map((c) => card(c, false)).join('\n')}</div>`
    : `<div class="section-h fresh">🆕 Nowe w tym tygodniu (0)</div>
       <div class="empty">Brak nowych kandydatów ≥3× w tym oknie. Powtarzalna robota albo już wytypowana niżej, albo cisza. 🎯</div>`;

  const histSection = history.length
    ? `<div class="section-h">📋 Wcześniej wytypowane (${history.length})</div>
       <div id="hist-cards">${history.map((c) => card(c, true)).join('\n')}</div>`
    : '';

  const body = `
    <div class="overline">Skill Scout</div>
    <h1>Co warto <span class="accent">opakować w skill</span></h1>
    <p class="sub-head">Powtarzalna ręczna robota z ostatnich ${data.window_days || 7} dni · ${data.date || todayISO()}</p>
    <div class="funnel">
      <div class="stat"><b>${intents}</b><span class="lab">Przeskanowanych próśb</span></div>
      <div class="stat accent"><b>${fresh.length}</b><span class="lab">Nowych w tym tygodniu</span></div>
      <div class="stat"><b>${savedLabel}</b><span class="lab">Potencjał z nowych / tydzień</span></div>
    </div>
    ${freshSection}
    ${histSection}`;

  const html = page(`Skill Scout · ${data.date || todayISO()}`, body);
  writeFileSync(join(RAPORTY, 'raport-aktualny.html'), html);
  writeFileSync(join(RAPORTY, `${data.date || todayISO()}.html`), html);
  console.error(`→ raport zapisany: Zasoby/raporty/skill-scout/Raporty/raport-aktualny.html (${fresh.length} nowych, ${history.length} w historii)`);
}

main();
