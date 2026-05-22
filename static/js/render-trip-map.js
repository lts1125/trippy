  function renderTripCard(d, cardIndex) {
    const daysHtml = (d.itinerary || []).map(function(day) {
      const spots = (day.spots || []).map(function(s) {
        var transportHtml = '';
        if (s.transport) {
          var t = s.transport;
          var tRoute = t.route || '';
          var tDetail = t.detail || '';
          transportHtml = '<div class="spot-transport">🚇 ' + escapeHtml(t.type || '') + (tRoute ? ' · ' + escapeHtml(tRoute) : '') + (tDetail ? ' · ' + escapeHtml(tDetail) : '') + '</div>';
        }
        return '<div class="spot-item">' +
          '<div class="spot-time">' + escapeHtml(s.time || '') + '</div>' +
          '<div>' +
            '<div class="spot-name">' + escapeHtml(s.name || '') + ' <span class="spot-duration">(' + escapeHtml(s.duration || '') + ')</span></div>' +
            transportHtml +
            (s.note ? '<div class="spot-note">' + escapeHtml(s.note) + '</div>' : '') +
          '</div>' +
        '</div>';
      }).join('');
      return '<div class="trip-day">' +
        '<div class="day-label">第 ' + day.day + ' 天' + (day.title ? ' — ' + escapeHtml(day.title) : '') + '</div>' +
        spots +
        (day.total_cost ? '<div class="card-footer"><span>💰 预计花费</span><span class="total-cost">¥' + day.total_cost + '</span></div>' : '') +
      '</div>';
    }).join('');

    var tripCardIndex = (window._tripCards || []).findIndex(function(c) { return c.data === d; });
    return '<div class="card trip-card" data-trip-card-index="' + tripCardIndex + '">' +
      '<div class="card-header">' +
        '<div class="destination">' + escapeHtml(d.destination || '') + '</div>' +
        '<div class="trip-meta">' + (d.days || 0) + '天 · ' + escapeHtml(d.travelers || '') + '</div>' +
      '</div>' +
      buildTripMap(d, cardIndex) +
      daysHtml +
      (d.total_cost ? '<div class="card-footer"><span>💰 总预算</span><span class="total-cost">¥' + d.total_cost + '</span></div>' : '') +
    '</div>';
  }

  function buildTripMap(d, cardIndex) {
    var allSpots = [];
    (d.itinerary || []).forEach(function(day) {
      (day.spots || []).forEach(function(s) {
        if (s.location && s.location.match(/^[\d.]+,[\d.]+$/)) {
          allSpots.push({ name: s.name || '', location: s.location });
        }
      });
    });
    if (allSpots.length < 2) return '';

    var W = 600, H = 200, pad = 30;
    var coords = allSpots.map(function(s) {
      var parts = s.location.split(',');
      return [parseFloat(parts[0]), parseFloat(parts[1])]; // [lng, lat]
    });

    var lngs = coords.map(function(c) { return c[0]; });
    var lats = coords.map(function(c) { return c[1]; });
    var minLng = Math.min.apply(null, lngs);
    var maxLng = Math.max.apply(null, lngs);
    var minLat = Math.min.apply(null, lats);
    var maxLat = Math.max.apply(null, lats);

    var rangeLng = maxLng - minLng || 0.001;
    var rangeLat = maxLat - minLat || 0.001;
    var scaleLng = (W - 2 * pad) / rangeLng;
    var scaleLat = (H - 2 * pad) / rangeLat;
    var scale = Math.min(scaleLng, scaleLat);

    function toXY(lng, lat) {
      return {
        x: pad + (lng - minLng) * scale,
        y: H - pad - (lat - minLat) * scale
      };
    }

    var points = coords.map(function(c) { return toXY(c[0], c[1]); });
    var lineParts = ['M ' + points[0].x + ' ' + points[0].y]
      .concat(points.slice(1).map(function(p) { return 'L ' + p.x + ' ' + p.y; }));

    var markersSvg = points.map(function(p, i) {
      var num = i + 1;
      return '<circle cx="' + p.x + '" cy="' + p.y + '" r="7" fill="#1E88E5" stroke="white" stroke-width="2"/>' +
             '<text x="' + p.x + '" y="' + (p.y - 12) + '" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A2E">' + num + '</text>';
    }).join('');

    var labelsSvg = points.map(function(p, i) {
      var name = escapeHtml(allSpots[i].name);
      return '<text x="' + (p.x + 10) + '" y="' + (p.y + 4) + '" font-size="11" fill="#1A1A2E" opacity="0.85">' + name + '</text>';
    }).join('');

    var svgContent = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" style="display:block;border-radius:8px;background:#f5f7fa;border:1px solid #e5e7eb;margin-bottom:12px;overflow:visible">' +
      '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#1E88E5" opacity="0.7"/></marker></defs>' +
      '<path d="' + lineParts.join(' ') + '" stroke="#1E88E5" stroke-width="2.5" fill="none" stroke-dasharray="8,4" opacity="0.7" marker-end="url(#arrow)"/>' +
      markersSvg +
      labelsSvg +
      '</svg>';

    return svgContent;
  }