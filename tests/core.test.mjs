import test from 'node:test';
import assert from 'node:assert/strict';
import {
  durationSeconds,
  nextAlarm,
  zoneName,
  restoreState,
  defaultState,
  formatDuration,
} from '../app/static/js/core.mjs';

test('timezone names preserve hyphens and use the final city component', () => {
  assert.equal(zoneName('America/Port-au-Prince'), 'Port-au-Prince');
  assert.equal(zoneName('America/Argentina/Buenos_Aires'), 'Buenos Aires');
});

test('timer rejects empty, fractional, negative, overflowing, and zero durations', () => {
  for (const values of [
    ['0', '0', '0'],
    ['', '1', '0'],
    ['1.5', '0', '0'],
    ['-1', '0', '0'],
    ['0', '60', '0'],
    ['24', '0', '1'],
    ['1e1', '0', '0'],
  ]) {
    assert.throws(() => durationSeconds(...values));
  }
  assert.equal(durationSeconds('24', '0', '0'), 86400);
  assert.equal(durationSeconds('0', '0', '1'), 1);
  assert.equal(formatDuration(1), '00:00:01');
  assert.equal(formatDuration(-100), '00:00:00');
});

test('past and equal alarm times schedule tomorrow, future times schedule today', () => {
  const now = new Date(2030, 0, 2, 12, 0, 0).getTime();
  assert.equal(nextAlarm('13:00', now), new Date(2030, 0, 2, 13).getTime());
  assert.equal(nextAlarm('12:00', now), new Date(2030, 0, 3, 12).getTime());
  assert.equal(nextAlarm('09:00', now), new Date(2030, 0, 3, 9).getTime());
  for (const value of ['', '24:00', '12:60', '9:00', '<script>'])
    assert.throws(() => nextAlarm(value, now));
});

test('alarm scheduling respects DST calendar days and rejects skipped local times', () => {
  const original = process.env.TZ;
  process.env.TZ = 'America/New_York';
  try {
    const beforeSpring = new Date(2030, 2, 9, 10).getTime();
    const target = nextAlarm('09:00', beforeSpring);
    assert.equal(new Date(target).getHours(), 9);
    assert.equal((target - beforeSpring) / 3600000, 22);
    assert.throws(() => nextAlarm('02:30', new Date(2030, 2, 10, 0).getTime()), /daylight saving/);
  } finally {
    if (original === undefined) delete process.env.TZ;
    else process.env.TZ = original;
  }
});

test('saved data cannot bypass limits or inject invalid timers and timezones', () => {
  const saved = defaultState();
  saved.favorites = ['Not/A_Zone', 'Asia/Manila', 'Asia/Manila', null];
  saved.pageSize = 100000;
  saved.timer = { duration: -1, remaining: -1, deadline: Date.now() };
  saved.alarms = Array.from({ length: 15 }, (_, index) => ({
    id: String(index),
    label: 'Test',
    at: Date.now() + (index + 1) * 60000,
  }));
  const restored = restoreState(JSON.stringify(saved));
  assert.deepEqual(restored.favorites, ['Asia/Manila']);
  assert.equal(restored.pageSize, 12);
  assert.equal(restored.timer, null);
  assert.equal(restored.alarms.length, 10);
  assert.throws(() => restoreState('{bad json'));
  assert.throws(() => restoreState('null'));
});

test('paused and overdue timers survive restoration so overdue alerts can be delivered', () => {
  for (const deadline of [null, Date.now() - 1000]) {
    const saved = defaultState();
    saved.timer = { duration: 5000, remaining: 2500, deadline };
    assert.deepEqual(restoreState(JSON.stringify(saved)).timer, saved.timer);
  }
});

test('static directory preserves search, regions, and bounded pagination', async () => {
  const { paginateCatalog } = await import('../app/static/js/catalog.mjs');
  const zones = [
    'America/Argentina/Buenos_Aires',
    'America/New_York',
    'America/Port-au-Prince',
    'Asia/Manila',
    'UTC',
  ];
  const query = (values) => paginateCatalog(zones, new URLSearchParams(values));
  assert.deepEqual(query({ q: '  NEW_york  ' }).zones, ['America/New_York']);
  assert.deepEqual(query({ q: 'buenos aires' }).zones, ['America/Argentina/Buenos_Aires']);
  assert.deepEqual(query({ region: 'Other' }).zones, ['UTC']);
  assert.equal(query({ q: 'not a city' }).total, 0);
  for (const values of [
    { page: 0 },
    { page: 2 },
    { page_size: 13 },
    { region: 'Missing' },
    { q: 'a'.repeat(81) },
  ]) {
    assert.throws(() => query(values));
  }
  const manyZones = Array.from(
    { length: 30 },
    (_, index) => `Asia/City_${String(index).padStart(2, '0')}`,
  );
  const first = paginateCatalog(manyZones, new URLSearchParams({ page: 1 }));
  const second = paginateCatalog(manyZones, new URLSearchParams({ page: 2 }));
  assert.equal(first.zones.length, 12);
  assert.equal(second.zones.length, 12);
  assert.equal(first.pages, 3);
  assert.equal(
    first.zones.some((zone) => second.zones.includes(zone)),
    false,
  );
});
