/**
 * Trippy Frontend JS
 */
(function () {
  const chatArea = document.getElementById('chatArea');
  const messagesEl = document.getElementById('messages');
  const welcomeScreen = document.getElementById('welcomeScreen');
  const skeletonScreen = document.getElementById('skeletonScreen');
  const inputEl = document.getElementById('messageInput');
  const sendBtn = document.getElementById('sendBtn');
  const tabs = document.querySelectorAll('.tab');
  const pills = document.querySelectorAll('.pill');

  let currentMode = 'guide';
  let conversationHistory = [];
  let lastCards = [];
  let _isLoading = false;
  let _mapIdCounter = 0;

  const modePlaceholders = {
    food: '说说你想去哪、想吃什么...',
    trip: '想去哪玩？几天？告诉我就行',
    guide: '查个目的地，我来给你攻略'
  };

  const modeLabels = { food: '🍜 美食', trip: '✈️ 行程', guide: '🗺️ 攻略' };
  const HISTORY_KEY = 'trippy_history';
  const MAX_HISTORY = 50;

  // ── History Manager ──────────────────────────────────
  function getHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); }
    catch { return []; }
  }

  function saveHistoryItem(text, mode) {
    const list = getHistory();
    const existing = list.findIndex(function(item) { return item.text === text && item.mode === mode; });
    if (existing !== -1) list.splice(existing, 1);
    list.unshift({ text: text, mode: mode, time: Date.now() });
    if (list.length > MAX_HISTORY) list.splice(MAX_HISTORY);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
  }

  function deleteHistoryItem(index) {
    const list = getHistory();
    list.splice(index, 1);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
    renderHistoryDrawer();
  }

  function clearAllHistory() {
    localStorage.setItem(HISTORY_KEY, '[]');
  }

  function formatHistoryTime(ts) {
    var d = new Date(ts);
    var now = new Date();
    var diffMs = now - d;
    var diffMins = Math.floor(diffMs / 60000);
    var diffHours = Math.floor(diffMs / 3600000);
    var diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return diffMins + '分钟前';
    if (diffHours < 24) return diffHours + '小时前';
    if (diffDays < 7) return diffDays + '天前';
    return (d.getMonth() + 1) + '/' + d.getDate();
  }

  function renderHistoryDrawer() {
    var list = getHistory();
    var container = document.getElementById('historyList');
    var empty = document.getElementById('historyEmpty');
    if (list.length === 0) {
      container.innerHTML = '<div class="history-empty" id="historyEmpty">暂无搜索记录</div>';
      return;
    }
    var html = list.map(function(item, i) {
      return '<div class="history-item" data-index="' + i + '" data-text="' + escapeHtml(item.text) + '" data-mode="' + item.mode + '">' +
        '<span class="history-item-mode">' + (modeLabels[item.mode] || item.mode) + '</span>' +
        '<span class="history-item-text">' + escapeHtml(item.text) + '</span>' +
        '<span class="history-item-time">' + formatHistoryTime(item.time) + '</span>' +
        '<button class="history-item-del" data-del="' + i + '" title="删除">×</button>' +
      '</div>';
    }).join('');
    container.innerHTML = html;
  }

  // ── History Drawer ────────────────────────────────
  var historyDrawer = document.getElementById('historyDrawer');
  var historyOverlay = document.getElementById('historyOverlay');
  var historyBtn = document.getElementById('historyBtn');
  var historyCloseBtn = document.getElementById('historyCloseBtn');

  function openHistoryDrawer() {
    renderHistoryDrawer();
    historyDrawer.classList.add('open');
    historyOverlay.classList.add('open');
  }
  function closeHistoryDrawer() {
    historyDrawer.classList.remove('open');
    historyOverlay.classList.remove('open');
  }

  historyBtn.addEventListener('click', openHistoryDrawer);
  historyCloseBtn.addEventListener('click', closeHistoryDrawer);
  historyOverlay.addEventListener('click', closeHistoryDrawer);
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeHistoryDrawer();
  });

  // Click on history item → re-send
  document.getElementById('historyList').addEventListener('click', function(e) {
    var delBtn = e.target.closest('[data-del]');
    if (delBtn) {
      e.stopPropagation();
      deleteHistoryItem(parseInt(delBtn.dataset.del, 10));
      return;
    }
    var item = e.target.closest('.history-item');
    if (!item) return;
    var text = item.dataset.text;
    var mode = item.dataset.mode;
    closeHistoryDrawer();
    // Switch tab
    tabs.forEach(function(t) {
      t.classList.toggle('active', t.dataset.mode === mode);
    });
    currentMode = mode;
    inputEl.value = text;
    sendMessage();
  });

  // ── Tab 切换动画 ───────────────────────────────────
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active');
        t.style.transform = '';
      });
      tab.classList.add('active');
      tab.style.transform = 'scale(1.05)';
      currentMode = tab.dataset.mode;
      inputEl.placeholder = modePlaceholders[currentMode] || modePlaceholders.guide;
      messagesEl.innerHTML = '';
      conversationHistory = [];
      destroyAllMaps();
      welcomeScreen.style.display = 'flex';
      welcomeScreen.style.animation = 'none';
      welcomeScreen.offsetHeight;
      welcomeScreen.style.animation = 'fadeIn 0.3s ease';
    });
  });

  // ── 快速入口点击 ──────────────────────────────────────
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      inputEl.value = pill.dataset.msg;
      sendMessage();
    });
  });

  // ── 发送消息 ─────────────────────────────────────────
  async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text || _isLoading) return;

    _isLoading = true;
    inputEl.value = '';
    sendBtn.disabled = true;
    sendBtn.style.opacity = '0.5';
    welcomeScreen.style.display = 'none';

    appendUserMsg(text);
    conversationHistory.push({ role: 'user', content: text });

    showSkeleton();

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          mode: currentMode,
          history: conversationHistory.slice(-6)
        })
      });

      const data = await resp.json();
      hideSkeleton();

      appendAssistantMsg(data.reply || '', data.cards || []);
      conversationHistory.push({ role: 'assistant', content: data.reply || '' });
      saveHistoryItem(text, currentMode);

    } catch (err) {
      hideSkeleton();
      appendAssistantMsg('抱歉，服务出了点问题，请稍后重试。', []);
      console.error(err);
    } finally {
      _isLoading = false;
      sendBtn.disabled = false;
      sendBtn.style.opacity = '1';
    }
  }

  // ── 发送按钮 & 回车发送 ────────────────────────────────
  sendBtn.addEventListener('click', sendMessage);
  inputEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // ── 辅助函数 ──────────────────────────────────────────

  function appendUserMsg(text) {
    const div = document.createElement('div');
    div.className = 'msg user';
    div.innerHTML = '<div class="msg-bubble">' + escapeHtml(text) + '</div>';
    messagesEl.appendChild(div);
    scrollToBottom();
  }

  function appendAssistantMsg(reply, cards) {
    lastCards = cards || [];
    window._tripCards = (cards || []).filter(function(c) { return c.type === 'trip'; });
    const div = document.createElement('div');
    div.className = 'msg assistant';

    let html = '';
    if (reply) {
      html += '<div class="msg-bubble">' + escapeHtml(reply) + '</div>';
    }
    if (cards && cards.length > 0) {
      html += '<div class="cards-container">' + cards.map((c, i) => renderCard(c, i)).join('') + '</div>';
    }

    div.innerHTML = html;
    messagesEl.appendChild(div);
    scrollToBottom();
    setTimeout(initTripMaps, 50);
  }


  function renderCard(card, cardIndex) {
    if (card.type === 'food') return renderFoodCard(card.data, cardIndex);
    if (card.type === 'trip') return renderTripCard(card.data, cardIndex);
    if (card.type === 'guide') return renderGuideCard(card.data, cardIndex);
    return '';
  }

  function renderFoodCard(d, cardIndex) {
    const tags = (d.tags || []).map(function(t) { return '<span class="tag">' + escapeHtml(t) + '</span>'; }).join('');
    const scores = [];
    if (d.scores) {
      if (d.scores.taste) scores.push('口味 <span>' + d.scores.taste + '</span>');
      if (d.scores.env) scores.push('环境 <span>' + d.scores.env + '</span>');
      if (d.scores.service) scores.push('服务 <span>' + d.scores.service + '</span>');
    }
    const scoresHtml = scores.length ? '<div class="card-scores">' + scores.map(function(s) { return '<div class="score-item">' + s + '</div>'; }).join('') + '</div>' : '';

    return '<div class="card food-card">' +
      '<div class="card-header">' +
        '<div class="card-name">' + escapeHtml(d.name || '') + '</div>' +
        '<div class="card-rating">★ ' + (d.rating || 0) + '</div>' +
      '</div>' +
      '<div class="card-meta">' +
        (d.cuisine ? '🍽️ ' + escapeHtml(d.cuisine) : '') + ' ' +
        (d.avg_price ? '💰 人均 ¥' + d.avg_price : '') + ' ' +
        (d.address ? '📍 ' + escapeHtml(d.address) : '') +
      '</div>' +
      (tags ? '<div class="card-tags">' + tags + '</div>' : '') +
      (d.summary ? '<div class="card-summary">' + escapeHtml(d.summary) + '</div>' : '') +
      scoresHtml +
      '<div class="card-actions">' +
        '<button class="card-action-btn detail-btn" data-index="' + cardIndex + '">查看详情</button>' +
      '</div>' +
    '</div>';
  }

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
    // Collect all spots with locations upfront (no circular reference)
    var allSpots = [];
    (d.itinerary || []).forEach(function(day) {
      (day.spots || []).forEach(function(s) {
        if (s.location && s.location.match(/^[\d.]+,[\d.]+$/)) {
          allSpots.push({ name: s.name || '', location: s.location });
        }
      });
    });
    var spotsJson = JSON.stringify(allSpots);
    var mapId = 'trip-map-' + (_mapIdCounter++);
    return '<div class="card trip-card">' +
      '<div class="card-header">' +
        '<div class="destination">' + escapeHtml(d.destination || '') + '</div>' +
        '<div class="trip-meta">' + (d.days || 0) + '天 · ' + escapeHtml(d.travelers || '') + '</div>' +
      '</div>' +
      (allSpots.length >= 1
        ? '<div class="trip-map-wrap" id="' + mapId + '" data-spots=\'' + spotsJson + '\' data-trip-data=\'' + JSON.stringify(d).replace(/'/g, "&#39;") + '\'></div>'
        : '') +
      daysHtml +
      (d.total_cost ? '<div class="card-footer"><span>💰 总预算</span><span class="total-cost">¥' + d.total_cost + '</span></div>' : '') +
    '</div>';
  }

  function renderGuideCard(d, cardIndex) {
    const spots = (d.spots || []).map(function(s) {
      const tips = (s.tips || []).map(function(t) { return '<span class="guide-tip">💡 ' + escapeHtml(t) + '</span>'; }).join('');
      return '<div class="guide-spot">' +
        '<div class="guide-spot-name">📍 ' + escapeHtml(s.name || '') + '</div>' +
        '<div class="guide-spot-meta">' +
          (s.open_time ? '🕐 ' + escapeHtml(s.open_time) : '') + ' ' +
          (s.ticket ? '🎟️ ' + escapeHtml(s.ticket) : '') + ' ' +
          (s.best_time ? '⏰ ' + escapeHtml(s.best_time) : '') +
        '</div>' +
        (s.summary ? '<div style="font-size:13px;color:var(--text-muted);margin-bottom:4px">' + escapeHtml(s.summary) + '</div>' : '') +
        (tips ? '<div style="margin-top:4px">' + tips + '</div>' : '') +
      '</div>';
    }).join('');

    const avoidPitfalls = (d.avoid_pitfalls || []).map(function(t) { return '<span class="guide-tip">' + escapeHtml(t) + '</span>'; }).join('');

    return '<div class="card guide-card">' +
      '<div class="card-header">🗺️ ' + escapeHtml(d.destination || '') + '</div>' +
      (d.overview ? '<div class="overview">' + escapeHtml(d.overview) + '</div>' : '') +
      spots +
      (avoidPitfalls ? '<div style="margin-top:10px"><span style="font-size:13px;font-weight:600">⚠️ 避坑：</span>' + avoidPitfalls + '</div>' : '') +
    '</div>';
  }

  var _skeletonTimer = null;
  var _skeletonMessages = [
    '正在理解你的需求...',
    '正在搜索目的地信息...',
    '正在规划行程...',
    '正在计算交通路线...',
    '快马上就好...'
  ];

  function showSkeleton() {
    skeletonScreen.style.display = 'flex';
    skeletonScreen.style.flexDirection = 'column';
    messagesEl.style.display = 'none';

    var statusEl = document.getElementById('skeletonStatus');
    if (statusEl) {
      statusEl.textContent = _skeletonMessages[0];
      var idx = 0;
      if (_skeletonTimer) clearInterval(_skeletonTimer);
      _skeletonTimer = setInterval(function() {
        idx = (idx + 1) % _skeletonMessages.length;
        statusEl.textContent = _skeletonMessages[idx];
      }, 2800);
    }
  }

  function hideSkeleton() {
    if (_skeletonTimer) {
      clearInterval(_skeletonTimer);
      _skeletonTimer = null;
    }
    skeletonScreen.style.display = 'none';
    messagesEl.style.display = 'flex';
  }

  function scrollToBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;')
      .replace(/\n/g, '<br>');
  }

  // ── Leaflet Map ──────────────────────────────────────
  var _mapInstances = {};

  function destroyAllMaps() {
    Object.keys(_mapInstances).forEach(function(mapId) {
      var map = _mapInstances[mapId];
      if (map && typeof map.remove === 'function') {
        try { map.remove(); } catch(e) {}
      }
    });
    _mapInstances = {};
  }

  function buildTripMapSvg(d) {
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
    var coords = allSpots.map(function(s) { var p = s.location.split(','); return [parseFloat(p[0]), parseFloat(p[1])]; });
    var lngs = coords.map(function(c) { return c[0]; }), lats = coords.map(function(c) { return c[1]; });
    var minLng = Math.min.apply(null, lngs), maxLng = Math.max.apply(null, lngs);
    var minLat = Math.min.apply(null, lats), maxLat = Math.max.apply(null, lats);
    var rangeLng = maxLng - minLng || 0.001, rangeLat = maxLat - minLat || 0.001;
    var scale = Math.min((W - 2*pad)/rangeLng, (H - 2*pad)/rangeLat);
    function toXY(lng, lat) { return { x: pad+(lng-minLng)*scale, y: H-pad-(lat-minLat)*scale }; }
    var points = coords.map(toXY);
    var linePath = points.map(function(p,i) { return (i===0?'M ':'L ')+p.x+' '+p.y; }).join(' ');
    var markers = points.map(function(p,i) {
      return '<circle cx="'+p.x+'" cy="'+p.y+'" r="7" fill="#1E88E5" stroke="white" stroke-width="2"/>'+
             '<text x="'+p.x+'" y="'+(p.y-10)+'" text-anchor="middle" font-size="12" font-weight="600" fill="#1A1A2E">'+(i+1)+'</text>';
    }).join('');
    var labels = points.map(function(p,i) {
      return '<text x="'+(p.x+12)+'" y="'+(p.y+4)+'" font-size="12" fill="#1A1A2E">'+escapeHtml(allSpots[i].name)+'</text>';
    }).join('');
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+W+' '+H+'" width="100%" height="100%" style="display:block;border-radius:8px;background:#f5f7fa;border:1px solid #d0d7de;margin-bottom:12px;overflow:visible">'+
      '<path d="'+linePath+'" stroke="#1E88E5" stroke-width="2.5" fill="none" stroke-dasharray="6,3" opacity="0.8"/>'+
      markers+labels+'</svg>';
  }


  function initTripMaps() {
    if (typeof L === 'undefined') {
      console.log('[Trippy] Leaflet not loaded yet, retry in 200ms');
      setTimeout(initTripMaps, 200);
      return;
    }

    document.querySelectorAll('.trip-map-wrap').forEach(function(wrap) {
      var mapId = wrap.id;
      if (!mapId) return;

      // If a stale map instance exists for this id but the DOM element is new,
      // remove the old one and re-init.
      if (_mapInstances[mapId]) {
        var oldMap = _mapInstances[mapId];
        var oldContainer = oldMap && oldMap.getContainer ? oldMap.getContainer() : null;
        if (oldContainer && document.contains(oldContainer) && oldContainer === wrap) {
          return;
        }
        try { oldMap.remove(); } catch(e) {}
        delete _mapInstances[mapId];
      }

      var spots = JSON.parse(wrap.dataset.spots || '[]');
      if (spots.length < 1) return;

      var coords = spots.map(function(s) {
        var parts = s.location.split(',');
        return [parseFloat(parts[1]), parseFloat(parts[0])];
      });
      var first = coords[0];

      try {
        var map = L.map(mapId, { zoomControl: true, scrollWheelZoom: false }).setView(first, 13);

        // Tile providers in priority order: Amap > OSM > Google
        var amapLayer = L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
          maxZoom: 18,
          attribution: '© 高德地图',
          subdomains: '1234'
        });
        var osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 18,
          attribution: '© OpenStreetMap'
        });
        var googleLayer = L.tileLayer('https://mt0.google.com/vt/lyrs=m@300&hl=zh-CN&x={x}&y={y}&z={z}', {
          maxZoom: 18,
          attribution: '© Google',
          subdomains: '0123'
        });

        var currentLayer = 0; // 0=amap, 1=osm, 2=google
        function tryNextLayer() {
          currentLayer++;
          if (currentLayer === 1) {
            console.log('[Trippy] Amap tiles failed, switching to OSM');
            map.removeLayer(amapLayer);
            osmLayer.addTo(map);
          } else if (currentLayer === 2) {
            console.log('[Trippy] OSM tiles failed, switching to Google');
            map.removeLayer(osmLayer);
            googleLayer.addTo(map);
          }
        }

        amapLayer.on('tileerror', tryNextLayer);
        osmLayer.on('tileerror', tryNextLayer);
        googleLayer.on('tileerror', function() {
          console.log('[Trippy] All tile providers failed');
        });
        amapLayer.addTo(map);

        coords.forEach(function(c, i) {
          L.marker(c).addTo(map).bindPopup(spots[i].name);
        });

        if (coords.length > 1) {
          L.polyline(coords, { color: '#1E88E5', weight: 3, opacity: 0.8 }).addTo(map);
          map.fitBounds(coords, { padding: [30, 30] });
        }

        _mapInstances[mapId] = map;
        console.log('[Trippy] map init done', mapId);

        // Fallback to SVG if no tiles load within 4s
        setTimeout(function() {
          var imgs = wrap.querySelectorAll('img');
          var anyLoaded = false;
          for (var i = 0; i < imgs.length; i++) {
            if (imgs[i].naturalWidth > 0) { anyLoaded = true; break; }
          }
          if (!anyLoaded) {
            console.log('[Trippy] tiles timed out, rendering SVG fallback');
            var tripData = JSON.parse(wrap.dataset.tripData || 'null');
            var svg = tripData ? buildTripMapSvg(tripData) : '';
            if (svg) {
              try { map.remove(); } catch(e) {}
              delete _mapInstances[mapId];
              wrap.innerHTML = svg;
            }
          }
        }, 4000);
      } catch(e) {
        console.log('[Trippy] map init error:', e.message);
        // Render SVG fallback on error
        var tripData = JSON.parse(wrap.dataset.tripData || 'null');
        var svg = tripData ? buildTripMapSvg(tripData) : '';
        if (svg) wrap.innerHTML = svg;
      }
    });
  }

  var detailModal = document.getElementById('detailModal');
  var detailModalBody = document.getElementById('detailModalBody');
  document.getElementById('detailCloseBtn').addEventListener('click', function() {
    detailModal.style.display = 'none';
  });
  detailModal.addEventListener('click', function(e) {
    if (e.target === detailModal) detailModal.style.display = 'none';
  });

  document.addEventListener('click', function(e) {
    var btn = e.target.closest('.detail-btn');
    if (!btn) return;
    var cardIndex = parseInt(btn.dataset.index, 10);
    showFoodDetail(cardIndex);
  });

  function showFoodDetail(index) {
    var card = lastCards[index];
    if (!card || card.type !== 'food') return;
    var d = card.data;
    var scores = [];
    if (d.scores) {
      if (d.scores.taste) scores.push('口味: ' + d.scores.taste);
      if (d.scores.env) scores.push('环境: ' + d.scores.env);
      if (d.scores.service) scores.push('服务: ' + d.scores.service);
    }

    var html = '<div class="detail-title">' + escapeHtml(d.name || '') + '</div>';
    html += '<div class="detail-row"><span class="detail-label">评分</span><span class="detail-value">★ ' + (d.rating || 0) + ' ' + scores.join(' | ') + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">人均</span><span class="detail-value">¥' + (d.avg_price || 0) + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">菜系</span><span class="detail-value">' + escapeHtml(d.cuisine || '') + '</span></div>';
    html += '<div class="detail-row"><span class="detail-label">地址</span><span class="detail-value">' + escapeHtml(d.address || '') + '</span></div>';
    if (d.tel) {
      html += '<div class="detail-row"><span class="detail-label">电话</span><span class="detail-value">' + escapeHtml(d.tel) + '</span></div>';
    }
    if (d.tags && d.tags.length) {
      var tagsHtml = d.tags.map(function(t) { return '<span class="tag">' + escapeHtml(t) + '</span>'; }).join(' ');
      html += '<div class="detail-row"><span class="detail-label">标签</span><span class="detail-value">' + tagsHtml + '</span></div>';
    }
    if (d.summary) {
      html += '<div class="detail-row" style="display:block;border:none;margin-top:12px">' +
        '<span class="detail-label" style="margin-bottom:4px;display:block">推荐理由</span>' +
        '<p style="font-size:14px;line-height:1.6;margin:0">' + escapeHtml(d.summary) + '</p></div>';
    }

    detailModalBody.innerHTML = html;
    detailModal.style.display = 'flex';
  }

})();
