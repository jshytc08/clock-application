export const MAX_FAVORITES = 12;
export const MAX_ALARMS = 10;
export const MAX_DURATION = 86400;
export const STORAGE_KEY = 'meridian.v1';

export function zoneName(zone) {
  return zone.split('/').at(-1).replaceAll('_', ' ');
}

export function validZone(zone) {
  if (typeof zone !== 'string' || zone.length > 128) return false;
  try {
    new Intl.DateTimeFormat('en', { timeZone: zone });
    return true;
  } catch {
    return false;
  }
}

export function durationSeconds(hours, minutes, seconds) {
  const values = [hours, minutes, seconds].map((value) => {
    if (!/^\d{1,2}$/.test(String(value)))
      throw new Error('Enter whole numbers for hours, minutes, and seconds.');
    return Number(value);
  });
  const [h, m, s] = values;
  const total = h * 3600 + m * 60 + s;
  if (h > 24 || m > 59 || s > 59 || total < 1 || total > MAX_DURATION) {
    throw new Error(
      'Set a duration between 1 second and 24 hours. Minutes and seconds must be 0–59.',
    );
  }
  return total;
}

export function formatDuration(milliseconds) {
  const total = Math.max(0, Math.ceil(milliseconds / 1000));
  return [Math.floor(total / 3600), Math.floor(total / 60) % 60, total % 60]
    .map((value) => String(value).padStart(2, '0'))
    .join(':');
}

// Use the local calendar date, rather than adding 24h across DST changes.
export function nextAlarm(time, now = Date.now()) {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(time)) throw new Error('Choose a valid alarm time.');
  const [hours, minutes] = time.split(':').map(Number);
  const target = new Date(now);
  target.setHours(hours, minutes, 0, 0);
  if (target.getTime() <= now) {
    target.setDate(target.getDate() + 1);
    target.setHours(hours, minutes, 0, 0);
  }
  if (target.getHours() !== hours || target.getMinutes() !== minutes) {
    throw new Error('That local time is skipped by daylight saving. Choose another time.');
  }
  return target.getTime();
}

export function defaultState() {
  return {
    version: 1,
    hour12: false,
    pageSize: 12,
    favorites: ['Asia/Manila', 'Europe/London', 'America/New_York', 'Asia/Tokyo'],
    timer: null,
    alarms: [],
  };
}

export function restoreState(raw) {
  const state = defaultState();
  if (!raw) return state;
  const parsed = JSON.parse(raw);
  if (!parsed || parsed.version !== 1) throw new Error('Saved settings could not be read.');
  state.hour12 = parsed.hour12 === true;
  if ([12, 24, 48].includes(parsed.pageSize)) state.pageSize = parsed.pageSize;
  if (Array.isArray(parsed.favorites)) {
    state.favorites = [...new Set(parsed.favorites.filter(validZone))].slice(0, MAX_FAVORITES);
  }
  const timer = parsed.timer;
  if (
    timer &&
    Number.isInteger(timer.duration) &&
    timer.duration >= 1000 &&
    timer.duration <= MAX_DURATION * 1000 &&
    Number.isFinite(timer.remaining) &&
    timer.remaining >= 0 &&
    timer.remaining <= timer.duration &&
    (timer.deadline === null ||
      (Number.isSafeInteger(timer.deadline) &&
        timer.deadline > 0 &&
        timer.deadline <= Date.now() + MAX_DURATION * 1000))
  ) {
    state.timer = {
      duration: timer.duration,
      remaining: timer.remaining,
      deadline: timer.deadline,
    };
  }
  if (Array.isArray(parsed.alarms)) {
    const ids = new Set();
    const deadlines = new Set();
    state.alarms = parsed.alarms
      .filter((alarm) => {
        if (
          !alarm ||
          typeof alarm.id !== 'string' ||
          alarm.id.length > 64 ||
          ids.has(alarm.id) ||
          !Number.isSafeInteger(alarm.at) ||
          alarm.at <= 0 ||
          alarm.at > Date.now() + 26 * 3600000 ||
          deadlines.has(alarm.at) ||
          typeof alarm.label !== 'string' ||
          alarm.label.length > 40
        )
          return false;
        ids.add(alarm.id);
        deadlines.add(alarm.at);
        return true;
      })
      .slice(0, MAX_ALARMS)
      .map(({ id, at, label }) => ({ id, at, label }));
  }
  return state;
}
