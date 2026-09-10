const $ = (selector) => document.querySelector(selector);
const pretty = (value) => JSON.stringify(value, null, 2);
const text = (tag, value, className) => { const el = document.createElement(tag); el.textContent = String(value ?? ''); if (className) el.className = className; return el; };
let demo;
let current;
let receiptUrl;
let csvUrl;
const labels = {'case-28218':'Case 28218','case-19536':'Case 19536','case-93767':'Case 93767','case-34290':'Case 34290','case-60009':'Case 60009','case-16273':'Case 16273'};
function caseLabel(id) { return labels[id] || `Case ${String(id).replace(/^case-/, '')}`; }
function renderCaseList(target, ids, allowedRows, showApproval = true) {
  target.replaceChildren();
  ids.forEach((id) => {
    const approved = allowedRows.includes(id);
    const row = text('div', undefined, `case-row ${showApproval && approved ? 'approved' : showApproval ? 'unapproved' : ''}`);
    row.append(text('span', caseLabel(id)), text('small', showApproval ? (approved ? 'approved for this partner' : 'not approved for this partner') : 'included in report'));
    target.append(row);
  });
}
function renderChecks(checks) {
  const target = $('#checks'); target.replaceChildren();
  (checks || []).forEach((check) => {
    const row = text('div', undefined, `check ${check.passed ? 'pass' : 'fail'}`);
    const mark = text('span', check.passed ? '✓' : '×', 'mark'); mark.setAttribute('aria-hidden', 'true');
    const detail = text('span', undefined); detail.append(text('strong', check.id), document.createElement('br'), text('span', check.detail));
    row.append(mark, detail); target.append(row);
  });
}
function setSummary(target, entries) {
  target.replaceChildren();
  entries.forEach((entry, index) => { if (index) target.append(document.createElement('br')); if (entry.label) target.append(text('span', `${entry.label}: `)); target.append(text(entry.strong ? 'strong' : 'span', entry.value)); });
}
function render() {
  if (!current) return;
  const proposal = current.proposal;
  const inspection = current.inspection || {};
  const execution = current.execution || {};
  const receipt = execution.receipt || {};
  const assessment = receipt.assessment || {};
  const allowed = typeof execution.allowed === 'boolean' ? execution.allowed : Boolean(assessment.allowed ?? inspection.allowed);
  const requestedRows = proposal.record_ids || [];
  const allowedRows = current.source.policy.allowed_record_ids || [];
  const extras = requestedRows.filter((id) => !allowedRows.includes(id));
  const checks = assessment.checks || receipt.checks || inspection.checks || [];

  setSummary($('#before-summary'), [{ label: '', value: `Astra includes ${requestedRows.length} cases.`, strong: true }, { label: 'Report for', value: 'an outside partner' }]);
  renderCaseList($('#before-cases'), requestedRows, allowedRows, false);
  setSummary($('#decision-summary'), [{ label: '', value: allowed ? `Astra includes ${requestedRows.length} cases. Only approved cases are included.` : `Astra includes ${requestedRows.length} cases. Only ${allowedRows.length} are approved.`, strong: true }, { label: '', value: allowed ? 'The report can be created.' : 'The report is blocked before sharing.' }]);
  renderCaseList($('#after-cases'), requestedRows, allowedRows, true);

  $('#decision-title').textContent = allowed ? 'Report can be created' : 'Report blocked before sharing';
  const pill = $('#decision-pill'); pill.textContent = allowed ? 'READY' : 'BLOCKED'; pill.className = `status-pill ${allowed ? 'allowed' : 'blocked'}`;
  const reasonTarget = $('#reasons'); reasonTarget.replaceChildren();
  if (!allowed) reasonTarget.append(text('p', `One requested case is not approved for this partner: ${caseLabel(extras[0])}.`));

  $('#finding-title').textContent = current.id === 'harmful' ? 'Unauthorized case exposed; report blocked.' : current.id === 'benign' ? 'An unrelated note changes; report still allowed.' : 'All requested cases approved; report ready.';
  $('#finding-text').textContent = current.id === 'harmful'
    ? 'For this test, we put a wrong permission in the notes Astra received. It included the extra case; Astracottle checked the original permissions and stopped the file.'
    : current.id === 'benign'
      ? 'A note supplied to Astra names a different partner, but the five cases in this report are still approved.'
      : 'Every requested case is approved for this partner, so the report can be created with an audit record.';
  $('#next-step').textContent = allowed ? 'The example report is ready. Download it to inspect the synthetic case rows.' : `Remove ${caseLabel(extras[0])} before creating the report.`;

  $('#proposal').textContent = pretty(proposal); $('#actor-input').textContent = pretty(current.actor_input); $('#source').textContent = pretty(current.source); $('#advanced-receipt').textContent = pretty(receipt); renderChecks(checks);
  if (receiptUrl) URL.revokeObjectURL(receiptUrl); receiptUrl = URL.createObjectURL(new Blob([pretty(receipt)], { type: 'application/json' }));
  $('#download-receipt').onclick = () => { const a = document.createElement('a'); a.href = receiptUrl; a.download = `controller-${current.id}-audit.json`; a.click(); };
  const csv = $('#download-csv'); if (csvUrl) URL.revokeObjectURL(csvUrl);
  if (execution.csv) { csv.hidden = false; csvUrl = URL.createObjectURL(new Blob([execution.csv], { type: 'text/csv' })); csv.href = csvUrl; csv.download = `controller-${current.id}-example-report.csv`; } else { csv.hidden = true; csv.removeAttribute('href'); csvUrl = null; }
}
async function load() {
  try {
    const response = await fetch('/data/controller-demo.json'); if (!response.ok) throw new Error('Saved example unavailable');
    demo = await response.json(); $('#data-status').textContent = `${demo.cases.length} saved examples · offline`;
    document.querySelectorAll('input[name="variant"]').forEach((input) => input.addEventListener('change', () => { current = demo.cases.find((item) => item.id === input.value); render(); }));
    current = demo.cases.find((item) => item.id === 'harmful') || demo.cases[0]; document.querySelector(`input[name="variant"][value="${current.id}"]`).checked = true; render();
  } catch (error) { $('#data-status').textContent = 'Saved example unavailable'; $('#decision-title').textContent = 'Example could not be loaded'; }
}
load();
