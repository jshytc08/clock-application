import {
  MAX_FAVORITES,
  MAX_ALARMS,
  STORAGE_KEY,
  zoneName,
  validZone,
  durationSeconds,
  formatDuration,
  nextAlarm,
  defaultState,
  restoreState,
} from './core.mjs';

const $ = (id) => document.getElementById(id);
let state;
try {
  state = restoreState(localStorage.getItem(STORAGE_KEY));
} catch {
  state = defaultState();
  storageNotice('Saved settings were unavailable or damaged. Defaults are in use.');
}
let page = 1;
let pages = 1;
let catalog = [];
let requestController;
let searchDelay;
let epochAnchor = Date.now();
let performanceAnchor = performance.now();
let synced = false;
let syncPending = false;
let lastPaint = '';
let audioContext;
let ringing;
const formatters = new Map();
const localZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';

function storageNotice(message) {
  $('storage-notice').textContent = message;
  $('storage-notice').hidden = false;
}
function save() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    storageNotice(
      'Browser storage is unavailable. Changes work in this tab but may not survive a reload.',
    );
  }
}
function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}
function clockNow() {
  return synced ? epochAnchor + performance.now() - performanceAnchor : Date.now();
}
function formatter(zone) {
  const key = `${zone}:${state.hour12}`;
  if (!formatters.has(key)) {
    formatters.set(key, {
      time: new Intl.DateTimeFormat('en-US', {
        timeZone: zone,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: state.hour12,
        ...(state.hour12 ? {} : { hourCycle: 'h23' }),
      }),
      date: new Intl.DateTimeFormat('en-US', {
        timeZone: zone,
        weekday: 'short',
        month: 'short',
        day: 'numeric',
      }),
      offset: new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'shortOffset' }),
    });
  }
  return formatters.get(key);
}
async function syncTime() {
  if (syncPending) return;
  syncPending = true;
  const start = performance.now();
  try {
    const response = await fetch('/api/time', {
      cache: 'no-store',
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) throw new Error('Sync failed');
    const data = await response.json();
    if (!Number.isSafeInteger(data.epoch_ms)) throw new Error('Invalid time');
    performanceAnchor = performance.now();
    epochAnchor = data.epoch_ms + (performanceAnchor - start) / 2;
    synced = true;
    $('sync-status').textContent = '● Server synced';
  } catch {
    synced = false;
    $('sync-status').textContent = 'Device time · sync unavailable';
  } finally {
    syncPending = false;
    lastPaint = '';
    tick();
  }
}
function createCard(zone) {
  const card = make('article', 'clock-card');
  card.dataset.zone = zone;
  const top = make('div', 'card-top');
  const parts = zone.split('/');
  top.append(
    make(
      'span',
      'card-region',
      parts.length > 1 ? parts.slice(0, -1).join(' / ').replaceAll('_', ' ') : 'Universal',
    ),
  );
  const star = make('button', 'star');
  star.type = 'button';
  const selected = state.favorites.includes(zone);
  star.textContent = selected ? '★' : '☆';
  star.setAttribute(
    'aria-label',
    `${selected ? 'Remove' : 'Save'} ${zoneName(zone)} ${selected ? 'from' : 'to'} favorites`,
  );
  star.setAttribute('aria-pressed', String(selected));
  star.addEventListener('click', () => toggleFavorite(zone));
  top.append(star);
  card.append(
    top,
    make('h3', '', zoneName(zone)),
    make('div', 'clock-time', '--:--:--'),
    make('p', 'clock-date'),
    make('p', 'clock-offset'),
  );
  return card;
}
function toggleFavorite(zone) {
  $('favorite-message').textContent = '';
  if (state.favorites.includes(zone))
    state.favorites = state.favorites.filter((item) => item !== zone);
  else {
    if (state.favorites.length >= MAX_FAVORITES) {
      $('favorite-message').textContent =
        'You have 12 favorites. Remove one before saving another.';
      return;
    }
    if (!validZone(zone)) {
      $('favorite-message').textContent =
        'Your browser does not support this timezone. Try updating your browser.';
      return;
    }
    state.favorites.push(zone);
  }
  save();
  // Preserve the clicked control rather than replacing the focused catalog card.
  renderFavorites();
  document.querySelectorAll('#clock-grid .clock-card').forEach((card) => {
    const selected = state.favorites.includes(card.dataset.zone);
    const button = card.querySelector('.star');
    button.textContent = selected ? '★' : '☆';
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute(
      'aria-label',
      `${selected ? 'Remove' : 'Save'} ${zoneName(card.dataset.zone)} ${selected ? 'from' : 'to'} favorites`,
    );
  });
  lastPaint = '';
  tick();
}
function renderFavorites() {
  const focusWasFavorite = $('favorites-grid').contains(document.activeElement);
  $('favorites-grid').replaceChildren(...state.favorites.map(createCard));
  $('favorite-count').textContent = `${state.favorites.length} / ${MAX_FAVORITES} saved places`;
  $('favorites-empty').hidden = state.favorites.length > 0;
  if (focusWasFavorite) ($('favorites-grid').querySelector('button') || $('searchInput')).focus();
}
function pageControls(loading = false) {
  $('previous-page').disabled = loading || page <= 1;
  $('next-page').disabled = loading || page >= pages;
}
async function loadCatalog() {
  clearTimeout(searchDelay);
  requestController?.abort();
  const controller = new AbortController();
  requestController = controller;
  $('clock-grid').setAttribute('aria-busy', 'true');
  $('catalog-error').hidden = true;
  $('no-results').hidden = true;
  $('catalog-status').textContent = 'Loading world clocks…';
  $('clock-grid').replaceChildren();
  $('page-summary').textContent = '';
  pageControls(true);
  const params = new URLSearchParams({
    q: $('searchInput').value.trim(),
    region: $('regionSelect').value,
    page: String(page),
    page_size: String(state.pageSize),
  });
  try {
    const response = await fetch(`/api/timezones?${params}`, {
      signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10000)]),
    });
    if (!response.ok) throw new Error('Catalog unavailable');
    const data = await response.json();
    if (controller.signal.aborted) return;
    catalog = data.zones;
    pages = data.pages;
    if ($('regionSelect').options.length === 1) {
      data.regions.forEach((region) => {
        const option = make('option', '', region);
        option.value = region;
        $('regionSelect').append(option);
      });
    }
    $('clock-grid').replaceChildren(...catalog.map(createCard));
    $('no-results').hidden = data.total !== 0;
    $('catalog-status').textContent =
      `${data.total} ${data.total === 1 ? 'timezone' : 'timezones'} found`;
    const start = data.total ? (page - 1) * state.pageSize + 1 : 0;
    $('page-summary').textContent =
      `Showing ${start}–${Math.min(page * state.pageSize, data.total)} of ${data.total}`;
    $('page-number').textContent = `Page ${page} of ${pages}`;
    pageControls();
    lastPaint = '';
    tick();
  } catch {
    if (controller.signal.aborted) return;
    $('catalog-error').hidden = false;
    $('catalog-status').textContent = 'World clock directory unavailable';
    $('page-number').textContent = 'Unable to load';
    pageControls(true);
  } finally {
    if (!controller.signal.aborted) $('clock-grid').setAttribute('aria-busy', 'false');
  }
}
function renderPreferences() {
  $('hour-format').textContent = state.hour12 ? '12-hour' : '24-hour';
  $('hour-format').setAttribute('aria-pressed', String(state.hour12));
  $('page-size').value = String(state.pageSize);
  lastPaint = '';
}
function timerRemaining() {
  return state.timer
    ? Math.max(
        0,
        state.timer.deadline === null ? state.timer.remaining : state.timer.deadline - Date.now(),
      )
    : 0;
}
function renderTimer() {
  const timer = state.timer;
  const running = Boolean(timer && timer.deadline !== null);
  $('timer-inputs').disabled = Boolean(timer);
  $('timer-start').disabled = running;
  $('timer-start').textContent = timer && timer.deadline === null ? 'Resume timer' : 'Start timer';
  $('timer-pause').disabled = !running;
  $('timer-reset').disabled = !timer;
  $('timer-status').textContent = running
    ? 'Focus on what matters. We’ll keep time.'
    : timer
      ? 'Paused · take your time'
      : 'Ready when you are';
  if (timer) $('timer-display').textContent = formatDuration(timerRemaining());
  else previewTimer();
}
function previewTimer() {
  if (state.timer) return;
  try {
    $('timer-display').textContent = formatDuration(
      durationSeconds($('timer-hours').value, $('timer-minutes').value, $('timer-seconds').value) *
        1000,
    );
  } catch {
    $('timer-display').textContent = '00:00:00';
  }
}
function alarmDate(at) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: state.hour12,
  }).format(at);
}
function renderAlarms() {
  const hadFocus = $('alarm-list').contains(document.activeElement);
  $('alarm-count').textContent = `${state.alarms.length} / ${MAX_ALARMS}`;
  $('alarm-add').disabled = state.alarms.length >= MAX_ALARMS;
  $('alarms-empty').hidden = state.alarms.length > 0;
  $('alarm-list').replaceChildren(
    ...[...state.alarms]
      .sort((a, b) => a.at - b.at)
      .map((alarm) => {
        const item = make('li');
        const detail = make('div', 'alarm-detail');
        detail.append(
          make('strong', '', alarm.label || 'Alarm'),
          make('span', '', alarmDate(alarm.at)),
        );
        const remove = make('button', 'secondary', 'Remove');
        remove.type = 'button';
        remove.setAttribute('aria-label', `Remove alarm ${alarm.label || alarmDate(alarm.at)}`);
        remove.addEventListener('click', () => {
          state.alarms = state.alarms.filter((item) => item.id !== alarm.id);
          save();
          renderAlarms();
          $('alarm-error').textContent = '';
        });
        item.append(detail, remove);
        return item;
      }),
  );
  if (hadFocus) ($('alarm-list').querySelector('button') || $('alarm-time')).focus();
}
function alarmPreview() {
  try {
    $('alarm-preview').textContent =
      `Will ring ${alarmDate(nextAlarm($('alarm-time').value))} · local time`;
  } catch {
    $('alarm-preview').textContent =
      'Choose a valid local time. Past times are scheduled for tomorrow.';
  }
}
async function enableSound() {
  try {
    audioContext ||= new AudioContext();
    await audioContext.resume();
    if (audioContext.state !== 'running') throw new Error('Sound blocked');
    $('enable-sound').textContent = 'Test sound';
    $('sound-status').textContent = 'Sound enabled for this page. Visual alerts are always on.';
    chime();
  } catch {
    $('sound-status').textContent =
      'Sound is unavailable. Visual alerts will still appear on this page.';
  }
}
function chime() {
  if (audioContext?.state !== 'running') return;
  const start = audioContext.currentTime;
  [523.25, 659.25, 783.99].forEach((frequency, index) => {
    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();
    const at = start + index * 0.2;
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0, at);
    gain.gain.linearRampToValueAtTime(0.13, at + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, at + 0.7);
    oscillator.connect(gain);
    gain.connect(audioContext.destination);
    oscillator.start(at);
    oscillator.stop(at + 0.75);
    oscillator.onended = () => {
      oscillator.disconnect();
      gain.disconnect();
    };
  });
}
function alertUser(messages) {
  $('alert-messages').append(...messages.map((message) => make('li', '', message)));
  if (!$('alert-dialog').open) {
    $('alert-dialog').showModal();
    $('dismiss-alert').focus();
  }
  chime();
  if (!ringing) ringing = setInterval(chime, 5000);
}
function tick() {
  const now = Date.now();
  const messages = [];
  if (state.timer && state.timer.deadline !== null && state.timer.deadline <= now) {
    state.timer = null;
    messages.push('Your focus timer is complete. Take a breath.');
    renderTimer();
    $('timer-display').textContent = '00:00:00';
    $('timer-status').textContent = 'Complete · nicely done';
  } else if (state.timer) $('timer-display').textContent = formatDuration(timerRemaining());
  const due = state.alarms.filter((alarm) => alarm.at <= now);
  if (due.length) {
    state.alarms = state.alarms.filter((alarm) => alarm.at > now);
    messages.push(
      ...due.map((alarm) => `${alarm.label || 'Alarm'} · scheduled ${alarmDate(alarm.at)}`),
    );
    renderAlarms();
  }
  if (messages.length) {
    save();
    alertUser(messages);
  }
  const date = new Date(clockNow());
  const paint = `${Math.floor(date.getTime() / 1000)}:${state.hour12}`;
  if (paint === lastPaint) return;
  lastPaint = paint;
  const local = formatter(localZone);
  $('local-time').textContent = local.time.format(date);
  $('local-date').textContent = new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
  document.querySelectorAll('.clock-card').forEach((card) => {
    try {
      const format = formatter(card.dataset.zone);
      card.querySelector('.clock-time').textContent = format.time.format(date);
      card.querySelector('.clock-date').textContent = format.date.format(date);
      card.querySelector('.clock-offset').textContent = format.offset
        .formatToParts(date)
        .find((part) => part.type === 'timeZoneName').value;
    } catch {
      card.querySelector('.clock-time').textContent = 'Unavailable';
      card.querySelector('.clock-date').textContent = 'Update your browser for this timezone.';
    }
  });
}

$('search-form').addEventListener('submit', (event) => {
  event.preventDefault();
  page = 1;
  loadCatalog();
});
$('searchInput').addEventListener('input', () => {
  requestController?.abort();
  clearTimeout(searchDelay);
  page = 1;
  pageControls(true);
  searchDelay = setTimeout(loadCatalog, 250);
});
$('regionSelect').addEventListener('change', () => {
  page = 1;
  loadCatalog();
});
$('page-size').addEventListener('change', () => {
  state.pageSize = Number($('page-size').value);
  save();
  page = 1;
  loadCatalog();
});
$('clear-search').addEventListener('click', () => {
  $('searchInput').value = '';
  $('regionSelect').value = '';
  page = 1;
  loadCatalog();
  $('searchInput').focus();
});
$('previous-page').addEventListener('click', () => {
  if (page > 1) {
    page--;
    loadCatalog();
  }
});
$('next-page').addEventListener('click', () => {
  if (page < pages) {
    page++;
    loadCatalog();
  }
});
$('retry').addEventListener('click', loadCatalog);
$('hour-format').addEventListener('click', () => {
  state.hour12 = !state.hour12;
  save();
  formatters.clear();
  renderPreferences();
  renderAlarms();
  alarmPreview();
  tick();
});
$('timer-form').addEventListener('submit', (event) => {
  event.preventDefault();
  $('timer-error').textContent = '';
  try {
    if (state.timer?.deadline != null) return;
    const remaining = state.timer
      ? state.timer.remaining
      : durationSeconds(
          $('timer-hours').value,
          $('timer-minutes').value,
          $('timer-seconds').value,
        ) * 1000;
    state.timer = {
      duration: state.timer?.duration || remaining,
      remaining,
      deadline: Date.now() + remaining,
    };
    save();
    renderTimer();
  } catch (error) {
    $('timer-error').textContent = error.message;
  }
});
$('timer-pause').addEventListener('click', () => {
  if (!state.timer) return;
  const remaining = timerRemaining();
  if (!remaining) {
    tick();
    return;
  }
  state.timer.remaining = remaining;
  state.timer.deadline = null;
  save();
  renderTimer();
});
$('timer-reset').addEventListener('click', () => {
  state.timer = null;
  save();
  $('timer-error').textContent = '';
  renderTimer();
});
['timer-hours', 'timer-minutes', 'timer-seconds'].forEach((id) =>
  $(id).addEventListener('input', previewTimer),
);
$('alarm-time').addEventListener('input', alarmPreview);
$('alarm-form').addEventListener('submit', (event) => {
  event.preventDefault();
  $('alarm-error').textContent = '';
  try {
    if (state.alarms.length >= MAX_ALARMS)
      throw new Error('You can set up to 10 alarms. Remove one to add another.');
    const label = $('alarm-label').value.trim();
    if (label.length > 40) throw new Error('Keep alarm labels to 40 characters or fewer.');
    const at = nextAlarm($('alarm-time').value);
    if (state.alarms.some((alarm) => alarm.at === at))
      throw new Error('An alarm is already scheduled for that time.');
    state.alarms.push({ id: crypto.randomUUID(), at, label });
    save();
    renderAlarms();
    $('alarm-label').value = '';
    alarmPreview();
  } catch (error) {
    $('alarm-error').textContent = error.message;
  }
});
$('enable-sound').addEventListener('click', enableSound);
$('dismiss-alert').addEventListener('click', () => $('alert-dialog').close());
$('alert-dialog').addEventListener('close', () => {
  clearInterval(ringing);
  ringing = null;
  $('alert-messages').replaceChildren();
});
window.addEventListener('storage', (event) => {
  if (event.key !== STORAGE_KEY && event.key !== null) return;
  try {
    state = restoreState(event.newValue);
    renderPreferences();
    renderFavorites();
    renderTimer();
    renderAlarms();
    page = 1;
    loadCatalog();
    tick();
  } catch {
    storageNotice(
      'Settings from another tab could not be read. This tab kept its current settings.',
    );
  }
});
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    synced = false;
    lastPaint = '';
    tick();
    syncTime();
  }
});
window.addEventListener('online', syncTime);
$('local-zone').textContent = localZone.replaceAll('_', ' ');
renderPreferences();
renderFavorites();
renderTimer();
renderAlarms();
tick();
loadCatalog();
syncTime();
setInterval(tick, 250);
setInterval(syncTime, 300000);
