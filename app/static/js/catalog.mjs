let savedCatalog;

export function paginateCatalog(zones, params) {
  const query = (params.get('q') || '')
    .replaceAll('_', ' ')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, ' ');
  const region = params.get('region') || '';
  const page = Number(params.get('page') || 1);
  const pageSize = Number(params.get('page_size') || 12);
  const zoneRegion = (zone) => (zone.includes('/') ? zone.split('/')[0] : 'Other');
  const regions = [...new Set(zones.map(zoneRegion))].sort();
  if (
    query.length > 80 ||
    !Number.isInteger(page) ||
    page < 1 ||
    page > 10000 ||
    ![12, 24, 48].includes(pageSize) ||
    (region && !regions.includes(region))
  ) {
    throw new Error('Invalid directory filters.');
  }
  const matches = zones.filter(
    (zone) =>
      zone.replaceAll('_', ' ').toLowerCase().includes(query) &&
      (!region || zoneRegion(zone) === region),
  );
  const pages = Math.max(1, Math.ceil(matches.length / pageSize));
  if (page > pages) throw new Error('This page does not exist.');
  return {
    zones: matches.slice((page - 1) * pageSize, page * pageSize),
    regions,
    total: matches.length,
    page,
    page_size: pageSize,
    pages,
  };
}

export async function fetchCatalogPage(params, signal, staticMode) {
  if (!staticMode) {
    const response = await fetch(`/api/timezones?${params}`, { signal });
    if (!response.ok) throw new Error('Catalog unavailable');
    return response.json();
  }
  if (!savedCatalog) {
    const response = await fetch(new URL('../data/timezones.json', import.meta.url), { signal });
    if (!response.ok) throw new Error('Catalog unavailable');
    const zones = await response.json();
    if (
      !Array.isArray(zones) ||
      !zones.length ||
      !zones.every((zone) => typeof zone === 'string')
    ) {
      throw new Error('Invalid catalog');
    }
    signal.throwIfAborted();
    savedCatalog = zones;
  }
  signal.throwIfAborted();
  return paginateCatalog(savedCatalog, params);
}
