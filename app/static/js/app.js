const state = { start: '', end: '', entity: 'artists', files: [], searchTimer: null };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

document.addEventListener('DOMContentLoaded', () => {
  bindNavigation(); bindFilters(); bindImport(); bindExplorer(); bindSearch(); bindActions();
  boot();
});

async function boot() {
  try {
    const [summary, years] = await Promise.all([getJSON('/api/summary'), getJSON('/api/years')]);
    fillYears(years); renderSummary(summary);
    if (summary.plays) await loadOverviewVisuals();
    else showEmpty(true);
  } catch (error) { notify(error.message); }
}

function bindNavigation() {
  $$('.nav-item').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
  $('.go-top').addEventListener('click', () => showView('top'));
  $('#menu-button').addEventListener('click', () => $('.sidebar').classList.toggle('open'));
}

function showView(name) {
  $$('.view').forEach(view => view.classList.toggle('active', view.id === `view-${name}`));
  $$('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.view === name));
  $('.sidebar').classList.remove('open');
  if (name === 'top') loadTop();
  if (name === 'diagnostics') loadDiagnostics();
}

function bindFilters() {
  $('#apply-range').addEventListener('click', applyRange);
  $('#clear-range').addEventListener('click', () => {
    $('#start-date').value = ''; $('#end-date').value = ''; $('#year-filter').value = ''; applyRange();
  });
  $('#year-filter').addEventListener('change', event => {
    const year = event.target.value;
    $('#start-date').value = year ? `${year}-01-01` : '';
    $('#end-date').value = year ? `${year}-12-31` : '';
    applyRange();
  });
}

async function applyRange() {
  state.start = $('#start-date').value; state.end = $('#end-date').value;
  if (state.start && state.end && state.start > state.end) return notify('The start date must be before the end date.');
  $('#range-caption').textContent = state.start || state.end ? `${state.start || 'Beginning'} — ${state.end || 'Today'}` : 'All time';
  try {
    const summary = await getJSON(`/api/summary?${filterParams()}`);
    renderSummary(summary); await loadOverviewVisuals();
    if ($('#view-top').classList.contains('active')) loadTop();
  } catch (error) { notify(error.message); }
}

function fillYears(years) { years.forEach(year => $('#year-filter').insertAdjacentHTML('beforeend', `<option value="${year}">${year}</option>`)); }
function filterParams(extra = {}) { return new URLSearchParams({ ...(state.start && { start: state.start }), ...(state.end && { end: state.end }), ...extra }).toString(); }

function renderSummary(data) {
  showEmpty(!data.plays); $('#stat-grid').classList.remove('skeleton');
  const cards = [
    ['Listening time', `${number(data.hours)}h`, `${number(data.average_minutes_per_listening_day)} min / listening day`],
    ['Total plays', number(data.plays), `${number(data.listening_days)} active days`],
    ['Unique artists', number(data.unique_artists), data.top_artist?.artist_name || '—'],
    ['Unique tracks', number(data.unique_tracks), data.top_track?.track_name || '—'],
  ];
  $('#stat-grid').innerHTML = cards.map(([label, value, note]) => `<article class="stat-card"><small>${escapeHTML(label)}</small><strong>${escapeHTML(value)}</strong><span>${escapeHTML(note)}</span></article>`).join('');
}

function showEmpty(empty) { $('#empty-state').classList.toggle('hidden', !empty); $('#dashboard-content').classList.toggle('hidden', empty); }

async function loadOverviewVisuals() {
  const query = filterParams();
  const [timeline, calendar, artists] = await Promise.all([
    getJSON(`/api/timeline?${query}`), getJSON(`/api/calendar?${query}`),
    getJSON(`/api/top?${filterParams({ entity: 'artists', limit: 7 })}`)
  ]);
  drawTimeline(timeline); drawCalendar(calendar); renderRanks($('#overview-artists'), artists, 'artists');
}

function drawTimeline(data) {
  const container = $('#timeline-chart');
  if (!data.length) { container.innerHTML = '<p class="muted">No listens in this range.</p>'; return; }
  const width = 900, height = 260, pad = 30, max = Math.max(...data.map(item => item.hours), 1);
  const x = index => pad + index * (width - pad * 2) / Math.max(data.length - 1, 1);
  const y = value => height - pad - value / max * (height - pad * 2);
  const points = data.map((item, index) => `${x(index)},${y(item.hours)}`).join(' ');
  const labels = data.filter((_, index) => index % Math.max(Math.ceil(data.length / 6), 1) === 0);
  $('#timeline-total').textContent = `${number(data.reduce((sum, item) => sum + item.hours, 0))} hours`;
  container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Listening hours over time"><defs><linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9ff66" stop-opacity=".28"/><stop offset="1" stop-color="#b9ff66" stop-opacity="0"/></linearGradient></defs>${[0,.25,.5,.75,1].map(f => `<line class="chart-grid" x1="${pad}" x2="${width-pad}" y1="${y(max*f)}" y2="${y(max*f)}"/>`).join('')}<polygon class="chart-area" points="${pad},${height-pad} ${points} ${width-pad},${height-pad}"/><polyline class="chart-line" points="${points}"/>${labels.map(item => { const index=data.indexOf(item); return `<text class="axis-label" x="${x(index)}" y="${height-5}" text-anchor="middle">${escapeHTML(item.period)}</text>`; }).join('')}</svg>`;
}

function drawCalendar(data) {
  const container = $('#calendar-chart');
  if (!data.length) { container.innerHTML = '<p class="muted">No calendar data in this range.</p>'; return; }
  const max = Math.max(...data.map(item => item.minutes), 1);
  container.innerHTML = `<div class="calendar-grid">${data.map(item => { const level = item.minutes ? Math.min(4, Math.ceil(item.minutes / max * 4)) : 0; return `<i class="calendar-day l${level}" title="${item.date}: ${number(item.minutes)} minutes, ${number(item.plays)} plays"></i>`; }).join('')}</div>`;
}

function bindExplorer() {
  $$('#entity-tabs button').forEach(button => button.addEventListener('click', () => {
    state.entity = button.dataset.entity; $$('#entity-tabs button').forEach(item => item.classList.toggle('active', item === button)); loadTop();
  }));
  $('#rank-metric').addEventListener('change', loadTop); $('#rank-limit').addEventListener('change', loadTop);
}

async function loadTop() {
  const container = $('#top-results'); container.innerHTML = '<p class="muted">Calculating rankings…</p>';
  try {
    const rows = await getJSON(`/api/top?${filterParams({ entity: state.entity, metric: $('#rank-metric').value, limit: $('#rank-limit').value })}`);
    renderRanks(container, rows, state.entity);
  } catch (error) { container.innerHTML = `<p class="muted">${escapeHTML(error.message)}</p>`; }
}

function renderRanks(container, rows, entity) {
  if (!rows.length) { container.innerHTML = '<p class="muted">No matching listens.</p>'; return; }
  const max = Math.max(...rows.map(item => item.total_ms), 1);
  container.innerHTML = rows.map(item => {
    const name = entity === 'artists' ? item.artist_name : entity === 'tracks' ? item.track_name : item.album_name;
    const subtitle = entity === 'artists' ? `${number(item.unique_days)} listening days` : item.artist_name;
    const value = $('#rank-metric')?.value === 'plays' ? `${number(item.play_count)} plays` : $('#rank-metric')?.value === 'days' ? `${number(item.unique_days)} days` : duration(item.total_ms);
    return `<button class="rank-row" data-entity="${entity.slice(0,-1)}" data-artist="${attr(item.artist_name)}" data-name="${attr(name)}"><span class="rank-number">${String(item.rank).padStart(2,'0')}</span><span class="rank-main"><strong>${escapeHTML(name)}</strong><small>${escapeHTML(subtitle)}</small><span class="bar"><i style="width:${item.total_ms/max*100}%"></i></span></span><span class="rank-value">${escapeHTML(value)}<small>${item.share ?? 0}%</small></span></button>`;
  }).join('');
  $$('.rank-row', container).forEach(row => row.addEventListener('click', () => openDetails(row.dataset.entity, row.dataset.artist, row.dataset.name)));
}

async function openDetails(entity, artist, name) {
  const dialog = $('#detail-dialog'); $('#detail-content').innerHTML = '<p class="muted">Loading details…</p>'; dialog.showModal();
  try {
    const data = await getJSON(`/api/entity/${entity}?${new URLSearchParams({ artist, ...(entity !== 'artist' && { name }) })}`);
    const max = Math.max(...data.timeline.map(item => item.total_ms), 1);
    $('#detail-content').innerHTML = `<p class="eyebrow">${escapeHTML(entity)} detail</p><h2 class="detail-title">${escapeHTML(data.name)}</h2>${entity !== 'artist' ? `<p class="muted">${escapeHTML(artist)}</p>` : ''}<div class="stat-grid detail-stats"><article class="stat-card"><small>Listening time</small><strong>${number(data.stats.hours)}h</strong></article><article class="stat-card"><small>Plays</small><strong>${number(data.stats.play_count)}</strong></article><article class="stat-card"><small>Active days</small><strong>${number(data.stats.unique_days)}</strong></article></div><div class="mini-timeline" title="Monthly listening timeline">${data.timeline.map(item => `<i style="height:${Math.max(2,item.total_ms/max*100)}%" title="${item.period}: ${duration(item.total_ms)}"></i>`).join('')}</div><p class="muted">First played ${dateLabel(data.stats.first_play)} · Latest play ${dateLabel(data.stats.last_play)}</p>`;
  } catch (error) { $('#detail-content').innerHTML = `<p>${escapeHTML(error.message)}</p>`; }
}

function bindSearch() {
  $('#search-input').addEventListener('input', event => {
    clearTimeout(state.searchTimer); const query = event.target.value.trim();
    if (query.length < 2) { $('#search-results').innerHTML = '<p class="muted">Type at least two characters to search your imported history.</p>'; return; }
    state.searchTimer = setTimeout(() => runSearch(query), 250);
  });
}

async function runSearch(query) {
  const data = await getJSON(`/api/search?${new URLSearchParams({ q: query })}`);
  $('#search-results').innerHTML = ['artists','tracks','albums'].map(entity => `<article class="card search-group"><h2>${title(entity)}</h2><div class="rank-list">${data[entity].length ? data[entity].map((item,index) => { const name=entity==='artists'?item.artist_name:entity==='tracks'?item.track_name:item.album_name; return `<button class="rank-row" data-entity="${entity.slice(0,-1)}" data-artist="${attr(item.artist_name)}" data-name="${attr(name)}"><span class="rank-number">${index+1}</span><span class="rank-main"><strong>${escapeHTML(name)}</strong><small>${entity==='artists'?number(item.play_count)+' plays':escapeHTML(item.artist_name)}</small></span><span class="rank-value">${duration(item.total_ms)}</span></button>`; }).join('') : '<p class="muted">No matches</p>'}</div></article>`).join('');
  $$('.rank-row', $('#search-results')).forEach(row => row.addEventListener('click', () => openDetails(row.dataset.entity, row.dataset.artist, row.dataset.name)));
}

function bindImport() {
  const dialog = $('#import-dialog'), input = $('#file-input'), zone = $('#drop-zone');
  $$('.open-import').forEach(button => button.addEventListener('click', () => dialog.showModal()));
  $('#import-again').addEventListener('click', () => dialog.showModal());
  input.addEventListener('change', () => setFiles([...input.files]));
  ['dragenter','dragover'].forEach(type => zone.addEventListener(type, event => { event.preventDefault(); zone.classList.add('dragover'); }));
  ['dragleave','drop'].forEach(type => zone.addEventListener(type, event => { event.preventDefault(); zone.classList.remove('dragover'); }));
  zone.addEventListener('drop', event => setFiles([...event.dataTransfer.files]));
  $('#start-import').addEventListener('click', uploadFiles);
}

function setFiles(files) {
  state.files = files.filter(file => /\.(zip|json)$/i.test(file.name));
  $('#file-list').innerHTML = state.files.map(file => `<div class="file-pill"><strong>${escapeHTML(file.name)}</strong><span>${bytes(file.size)}</span></div>`).join('');
  $('#start-import').disabled = !state.files.length;
}

async function uploadFiles() {
  const form = new FormData(); state.files.forEach(file => form.append('files', file));
  $('#import-progress').classList.remove('hidden'); $('#import-result').classList.add('hidden'); $('#start-import').disabled = true;
  try {
    const response = await fetch('/api/import', { method: 'POST', body: form }); const data = await response.json();
    if (!response.ok && !data.accepted) throw new Error(data.error || data.files?.[0]?.warnings?.[0] || 'Import failed.');
    $('#import-result').innerHTML = `<strong>Import complete</strong><br>${number(data.accepted)} accepted · ${number(data.duplicates)} duplicates · ${number(data.ignored)} ignored · ${number(data.warning_count)} warnings`;
    $('#import-result').classList.remove('hidden'); notify(`Imported ${number(data.accepted)} listening events.`); await boot();
  } catch (error) { $('#import-result').textContent = error.message; $('#import-result').classList.remove('hidden'); }
  finally { $('#import-progress').classList.add('hidden'); $('#start-import').disabled = false; }
}

function bindActions() {
  $$('.dialog-close').forEach(button => button.addEventListener('click', () => button.closest('dialog').close()));
  $('#refresh-diagnostics').addEventListener('click', loadDiagnostics);
  $('#theme-button').addEventListener('click', () => document.body.classList.toggle('high-contrast'));
  $('#delete-data').addEventListener('click', deleteData);
}

async function loadDiagnostics() {
  try {
    const data = await getJSON('/api/diagnostics');
    const fields = [['Stored events', data.database.events], ['Source files', data.database.source_files], ['Missing albums', data.database.missing_albums], ['Unknown skip flags', data.database.unknown_skips]];
    $('#diagnostic-summary').innerHTML = fields.map(([label,value]) => `<article class="stat-card"><small>${label}</small><strong>${number(value)}</strong></article>`).join('');
    $('#import-runs').innerHTML = data.imports.length ? data.imports.map(run => `<article class="card import-run"><div class="run-heading"><div><h2>${dateLabel(run.finished_at)}</h2><p>${number(run.accepted)} accepted · ${number(run.duplicates)} duplicates · ${number(run.ignored)} ignored</p></div><span class="muted">${number(run.warning_count)} warnings</span></div>${run.files.map(file => `<div class="file-diagnostic"><code title="${attr(file.filename)}">${escapeHTML(file.filename)}</code><span>${escapeHTML(file.format)}</span><span>${number(file.accepted)} accepted</span><span>${number(file.duplicates)} duplicate</span><span>${number(file.ignored)} ignored</span>${file.warnings.length ? `<small class="muted">${file.warnings.map(escapeHTML).join(' • ')}</small>` : ''}</div>`).join('')}</article>`).join('') : '<p class="muted">No imports recorded yet.</p>';
  } catch (error) { notify(error.message); }
}

async function deleteData() {
  if (!confirm('Delete every imported listening event from this computer? This cannot be undone.')) return;
  const response = await fetch('/api/data', { method: 'DELETE', headers: {'Content-Type':'application/json'}, body: JSON.stringify({confirm:'DELETE'}) });
  const data = await response.json(); if (!response.ok) return notify(data.error || 'Could not delete data.');
  notify(`Deleted ${number(data.deleted)} local events.`); showView('overview'); await boot();
}

async function getJSON(url) { const response = await fetch(url); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Request failed.'); return data; }
function notify(message) { const toast=$('#toast'); toast.textContent=message; toast.classList.add('show'); setTimeout(()=>toast.classList.remove('show'),3500); }
function number(value) { return Number(value || 0).toLocaleString(undefined,{maximumFractionDigits:1}); }
function duration(ms) { const minutes=Math.round((ms||0)/60000); return minutes>=60?`${number(minutes/60)}h`:`${number(minutes)}m`; }
function bytes(value) { if(value<1024*1024) return `${number(value/1024)} KB`; return `${number(value/1024/1024)} MB`; }
function dateLabel(value) { return value ? new Date(value).toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}) : '—'; }
function title(value) { return value[0].toUpperCase()+value.slice(1); }
function escapeHTML(value) { return String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char])); }
function attr(value) { return escapeHTML(value); }
