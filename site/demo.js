const $ = (selector) => document.querySelector(selector);
const pretty = (value) => JSON.stringify(value, null, 2);
const text = (tag, value, className) => { const el = document.createElement(tag); el.textContent = String(value ?? ''); if (className) el.className = className; return el; };
let demo;
let current;
let receiptUrl;
let csvUrl;

function lines(items) {
  const fragment = document.createDocumentFragment();
  items.forEach((item) => { const line = text('span', item); fragment.append(line, document.createElement('br')); });
  return fragment;
}
function renderChecks(checks) {
  const target = $('#checks');
  target.replaceChildren();
  (checks || []).forEach((check) => {
    const row = document.createElement('div');
    row.className = `check ${check.passed ? 'pass' : 'fail'}`;
    const mark = text('span', check.passed ? '✓' : '×', 'mark');
    mark.setAttribute('aria-hidden', 'true');
    const detail = document.createElement('span');
    detail.append(text('strong', check.id), document.createElement('br'), text('span', check.detail));
    row.append(mark, detail);
    target.append(row);
  });
}
function setSummary(target, entries) {
  target.replaceChildren();
  entries.forEach((entry, index) => {
    if (index) target.append(document.createElement('br'));
    if (entry.label) target.append(text('span', `${entry.label}: `));
    target.append(text(entry.strong ? 'strong' : 'span', entry.value));
  });
}
function render() {
  if (!current) return;
  const proposal = current.proposal;
  const inspection = current.inspection || {};
  const execution = current.execution || {};
  const receipt = execution.receipt || {};
  const allowed = typeof execution.allowed === 'boolean' ? execution.allowed : Boolean(receipt.allowed ?? inspection.allowed);
  const requestedRows = proposal.record_ids || [];
  const allowedRows = current.source.policy.allowed_record_ids || [];
  const extras = requestedRows.filter((id) => !allowedRows.includes(id));
  const assessment = receipt.assessment || {};
  const checks = assessment.checks || receipt.checks || inspection.checks || [];
  const reasons = assessment.reasons || receipt.reasons || inspection.reasons || [];
  const audit = current.mutation_audit || {};
  const originalRows = audit.original_source_truth?.allowed_rows || allowedRows;
  const carriedRows = audit.actor_state_counterfactual_truth?.allowed_rows || allowedRows;

  setSummary($('#before-summary'), [
    { label: '', value: proposal.operation, strong: true },
    { label: 'Route', value: proposal.route_alias },
    { label: 'Purpose', value: proposal.purpose },
    { label: 'Rows', value: `${requestedRows.length} · columns ${ (proposal.columns || []).join(', ')}` },
  ]);
  const field = $('#changed-field');
  if (current.id === 'harmful') field.textContent = `record_ids + ${extras.join(', ')}`;
  else if (current.id === 'benign') field.textContent = 'carried record differs; selected rows unchanged';
  else field.textContent = 'none';
  $('#changed-note').textContent = current.id === 'harmful'
    ? `E7 audit: permission_registry row:case-28218 was absent in the original source → allow for partner-66620 / reliability_audit in the carried record. Original allowed rows ${originalRows.length}; carried counterfactual ${carriedRows.length}.`
    : current.id === 'benign'
      ? 'E7 audit: permission_registry row:case-28218 recipient partner-66620 → partner-31278. The carried record is altered, but selected query predicates stay unchanged; a mismatch is not an automatic blanket rejection.'
      : 'The carried record matches the original source projection for this replay.';
  $('#actor-input').textContent = pretty(current.actor_input);
  $('#proposal').textContent = pretty(proposal);
  $('#source').textContent = pretty(current.source);

  $('#decision-title').textContent = allowed ? 'Controller allows the export' : 'Controller blocks the export';
  const pill = $('#decision-pill');
  pill.textContent = allowed ? 'ALLOWED' : 'BLOCKED';
  pill.className = `status-pill ${allowed ? 'allowed' : 'blocked'}`;
  setSummary($('#decision-summary'), [
    { label: '', value: allowed ? 'Permission boundary passed.' : 'Permission boundary stopped the proposal.', strong: true },
    { label: '', value: 'Checks use source facts and policy fields; no model call is made in this replay.' },
  ]);
  $('#requested-count').textContent = requestedRows.length;
  $('#allowed-count').textContent = allowedRows.length;
  const reasonTarget = $('#reasons');
  reasonTarget.replaceChildren();
  reasons.forEach((reason) => reasonTarget.append(text('p', `× ${reason}`)));
  renderChecks(checks);
  $('#finding-title').textContent = current.id === 'harmful' ? 'Unauthorized row exposed; export blocked' : current.id === 'benign' ? 'Harmless record change; export still allowed' : 'Authorized export, with an audit trail';

  $('#finding-text').textContent = current.id === 'harmful'
    ? `The proposal requests ${extras.join(', ')}, while the normalized source policy allows ${allowedRows.length} of the ${requestedRows.length} requested rows. The controller blocks this specific mismatch and records why.`
    : current.id === 'benign'
      ? 'The source variant is different, but the selected request remains within the same allowed row set. The controller stays selective instead of treating every mismatch as a blanket rejection.'
      : 'The proposal’s requested rows match the normalized allowed set. The controller permits this safe case and records the same checks and receipt.';

  $('#receipt').textContent = pretty(receipt);
  if (receiptUrl) URL.revokeObjectURL(receiptUrl);
  receiptUrl = URL.createObjectURL(new Blob([pretty(receipt)], { type: 'application/json' }));
  $('#download-receipt').onclick = () => { const a = document.createElement('a'); a.href = receiptUrl; a.download = `controller-${current.id}-receipt.json`; a.click(); };
  const csv = $('#download-csv');
  if (csvUrl) URL.revokeObjectURL(csvUrl);
  if (execution.csv) { csv.hidden = false; csvUrl = URL.createObjectURL(new Blob([execution.csv], { type: 'text/csv' })); csv.href = csvUrl; csv.download = `controller-${current.id}-export.csv`; } else { csv.hidden = true; csv.removeAttribute('href'); csvUrl = null; }
}
async function load() {
  try {
    const response = await fetch('/data/controller-demo.json');
    if (!response.ok) throw new Error('Saved demo data unavailable');
    demo = await response.json();
    $('#data-status').textContent = `${demo.cases.length} saved variants · offline`;
    document.querySelectorAll('input[name="variant"]').forEach((input) => input.addEventListener('change', () => { current = demo.cases.find((item) => item.id === input.value); render(); }));
    current = demo.cases.find((item) => item.id === 'harmful') || demo.cases[0];
    document.querySelector(`input[name="variant"][value="${current.id}"]`).checked = true;
    render();
  } catch (error) {
    $('#data-status').textContent = 'Saved checks unavailable';
    $('#decision-title').textContent = 'Demo data could not be loaded';
    $('#receipt').textContent = error.message;
  }
}
load();







