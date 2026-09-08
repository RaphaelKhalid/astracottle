const $ = selector => document.querySelector(selector);
const node = (tag, text, className) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (className) e.className = className; return e; };
const cache = new Map();
let ledger, selected;

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $('#theme').textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
  $('#theme').setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
}
let preference;
try { preference = localStorage.getItem('astracottle-theme'); } catch {}
setTheme(preference === 'dark' || (!preference && matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light');
$('#theme').addEventListener('click', () => { const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; setTheme(next); try { localStorage.setItem('astracottle-theme', next); } catch {} });

function link(text, href, download = false) {
  const a = node('a', text); a.href = href;
  if (download) a.download = '';
  return a;
}
function badge(text, status) { return node('span', text, `tag ${status}`); }
function list(items) { const ul = node('ul'); items.forEach(text => ul.append(node('li', text))); return ul; }
function section(title, items) { const div = node('section'); div.append(node('h3', title)); div.append(Array.isArray(items) ? list(items) : node('p', items)); return div; }
function table(result) {
  const wrap = node('div', undefined, 'table-scroll'), t = node('table');
  if (result.caption) t.append(node('caption', result.caption));
  const head = node('thead'), hr = node('tr'); result.columns.forEach(col => { const th = node('th', col); th.scope = 'col'; hr.append(th); }); head.append(hr); t.append(head);
  const body = node('tbody'); result.rows.forEach(row => { const tr = node('tr'); row.forEach(value => tr.append(node('td', String(value)))); body.append(tr); }); t.append(body); wrap.append(t); return wrap;
}
function renderIndex() {
  const q = $('#search').value.trim().toLowerCase(), status = $('#status').value;
  const matches = ledger.experiments.filter(e => (status === 'all' || e.status === status) && `${e.id} ${e.title} ${e.topic} ${e.finding}`.toLowerCase().includes(q));
  const target = $('#experiment-list'); target.replaceChildren();
  matches.forEach(e => {
    const row = node('div'); row.setAttribute('role', 'listitem');
    const a = link('', `#${e.id}`); a.className = 'study-link'; a.setAttribute('aria-current', String(e.id === selected));
    a.append(node('span', `${e.number} / ${e.date}`, 'num'), node('span', e.title, 'name'), badge(e.statusLabel, e.status)); row.append(a); target.append(row);
  });
  if (!matches.length) target.append(node('p', 'No experiments match. Try another search or status.', 'empty'));
}
async function loadData(path) {
  if (!cache.has(path)) cache.set(path, fetch(path).then(r => { if (!r.ok) throw new Error('Public data unavailable'); return r.json(); }));
  try { return await cache.get(path); } catch (error) { cache.delete(path); throw error; }
}
function traceExplorer(experiment) {
  const details = node('details'), summary = node('summary', 'Inspect the public traces'); details.append(summary);
  let opened = false;
  details.addEventListener('toggle', async () => {
    if (!details.open || opened) return; opened = true;
    const state = node('p', 'Loading public traces…'); details.append(state);
    try {
      const data = await loadData(experiment.data);
      const entries = [];
      for (const run of data.runs || []) for (const d of run.decisions || []) entries.push({ label: `${run.trial_id || `${run.mode} / ${run.arm}`} / ${d.filename || d.label || 'decision'}`, decision: d });
      for (const control of data.positive_controls || []) for (const [view, d] of Object.entries(control.reviews || {})) entries.push({ label: `Positive control / ${control.name} / ${view}`, decision: d });
      if (!entries.length && data.trials) for (const t of data.trials) entries.push({ label: t.trial_id || t.label || t.variant || 'Trial', decision: t });
      state.remove();
      if (!entries.length) { details.append(link('Open the complete public dataset ↗', experiment.data)); return; }
      const controls = node('div', undefined, 'trace-controls');
      const label = node('label', 'Decision'); label.htmlFor = 'trace-choice';
      const select = node('select'); select.id = 'trace-choice'; entries.forEach((entry, i) => { const option = node('option', entry.label); option.value = String(i); select.append(option); });
      const view = node('select'); view.setAttribute('aria-label', 'Trace fields'); [['record','Public output'],['input','Supplied input'],['full','All released fields']].forEach(([value, text]) => { const option = node('option', text); option.value = value; view.append(option); });
      const pre = node('pre'), copy = node('button', 'Copy JSON'); copy.type = 'button';
      const notice = node('span', '', 'index-note'); notice.setAttribute('role','status');
      function show() { const d = entries[Number(select.value)].decision; const value = view.value === 'input' ? (d.input || d.prompt || d) : view.value === 'full' ? d : (d.parsed || d.public_output || d.text || d); pre.textContent = typeof value === 'string' ? value : JSON.stringify(value, null, 2); notice.textContent = ''; }
      select.addEventListener('change', show); view.addEventListener('change', show);
      copy.addEventListener('click', async () => { try { await navigator.clipboard.writeText(pre.textContent); notice.textContent = 'Copied.'; } catch { notice.textContent = 'Select the text below to copy it.'; } });
      controls.append(label, select, view, copy, notice); details.append(controls, pre); show();
    } catch { state.textContent = 'The traces could not be loaded. The dataset is also available from the source repository.'; opened = false; }
  });
  return details;
}
function renderExperiment(id) {
  const e = ledger.experiments.find(x => x.id === id) || ledger.experiments[0]; selected = e.id;
  const article = $('#experiment'); article.replaceChildren();
  const meta = node('div', undefined, 'meta'); meta.append(node('span', `EXPERIMENT ${e.number}`), badge(e.statusLabel, e.status), node('span', e.date));
  article.append(meta, node('h2', e.title), node('p', e.question));
  const finding = node('div', undefined, 'finding'); finding.append(node('span', e.findingLabel || 'CURRENT FINDING', 'label'), node('p', e.finding)); article.append(finding);
  const stats = node('div', undefined, 'study-stats'); e.stats.forEach(stat => { const s = node('span'); s.append(node('b', String(stat.value)), document.createTextNode(` ${stat.label}`)); stats.append(s); }); article.append(stats);
  article.append(section('Setup', e.setup));
  if (e.results) { article.append(node('h3', 'Observed results'), table(e.results)); }
  if (e.interpretation) article.append(section('Interpretation', e.interpretation));
  article.append(section('Limits on the claim', e.limitations));
  if (e.next) article.append(section('Next decision', e.next));
  const resources = node('div', undefined, 'resources');
  if (e.data) resources.append(link('↓ Public dataset (.json)', e.data, true));
  if (e.protocol) resources.append(link('Read protocol ↗', e.protocol));
  if (e.report) resources.append(link('Read full report ↗', e.report));
  resources.append(link('Permanent link', `#${e.id}`)); article.append(resources);
  if (e.data) article.append(traceExplorer(e));
  renderIndex();
  document.title = `Astracottle — ${e.number}: ${e.title}`;
}
$('#search').addEventListener('input', renderIndex); $('#status').addEventListener('change', renderIndex);
window.addEventListener('hashchange', () => { if (ledger && ledger.experiments.some(e => `#${e.id}` === location.hash)) renderExperiment(location.hash.slice(1)); });
document.addEventListener('keydown', e => { if (e.key === '/' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) && !e.metaKey && !e.ctrlKey && !e.altKey) { e.preventDefault(); $('#search').focus(); } if (e.key === 'Escape' && document.activeElement === $('#search')) { $('#search').value = ''; renderIndex(); $('#search').blur(); } });
fetch('/data/ledger.json').then(r => { if (!r.ok) throw new Error('Ledger unavailable'); return r.json(); }).then(data => {
  ledger = data; $('#updated').textContent = `UPDATED ${data.updated}`;
  $('#study-count').textContent = data.experiments.length;
  $('#decision-count').textContent = data.experiments.reduce((sum,e) => sum+e.decisions, 0).toLocaleString();
  $('#complete-count').textContent = data.experiments.filter(e => e.status === 'completed').length;
  renderExperiment(location.hash.slice(1));
}).catch(() => { $('#experiment').replaceChildren(node('p', 'The experiment ledger could not be loaded.')); const error = $('#error'); error.hidden = false; error.replaceChildren(document.createTextNode('Please reload the page, or '), link('read the source repository', 'https://github.com/RaphaelKhalid/astracottle'), document.createTextNode('.')); });
