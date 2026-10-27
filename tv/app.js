/* Lumio TV client. Shipped in firmware; talks to the backend over JSON. */
(function () {
  "use strict";

  var CHECK_INTERVAL_MS = 5000;
  var DOWNLOAD_MS = 3000;
  var INSTALL_MS = 1500;
  var GRID_COLUMNS = 5;

  var params = new URLSearchParams(window.location.search);
  var deviceId = params.get("device") || "TV-001";

  var tv = {
    device: null,
    state: "menu",
    apps: [],
    focus: 0,
    channel: 1,
    updating: false,
    lastCheck: null
  };

  var el = function (id) { return document.getElementById(id); };

  function api(method, path, body) {
    var options = { method: method, headers: {} };
    if (body !== undefined) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }
    return fetch(path, options).then(function (res) {
      el("offline").hidden = true;
      return res.json().then(function (data) {
        if (!res.ok) { throw new Error(data.error || ("HTTP " + res.status)); }
        return data;
      });
    }, function (err) {
      el("offline").hidden = false;
      throw err;
    });
  }

  function log(text, kind) {
    var item = document.createElement("li");
    var time = document.createElement("time");
    time.textContent = new Date().toLocaleTimeString("pl-PL");
    item.appendChild(time);
    item.appendChild(document.createTextNode(text));
    if (kind) { item.className = kind; }
    var list = el("log");
    list.insertBefore(item, list.firstChild);
    while (list.children.length > 200) { list.removeChild(list.lastChild); }
  }

  /* ---------- rendering ---------- */

  function renderStatus() {
    var d = tv.device;
    el("sb-device").textContent = d.id;
    el("sb-model").textContent = d.model_name + " (" + d.model + ")";
    el("sb-region").textContent = d.region;
    el("sb-firmware").textContent = d.firmware;
    el("downloads").textContent = d.downloads;
  }

  function renderClock() {
    if (!tv.device) { return; }
    var now = new Date(Date.now() + tv.device.utc_offset_min * 60000);
    var hh = String(now.getUTCHours()).padStart(2, "0");
    var mm = String(now.getUTCMinutes()).padStart(2, "0");
    el("sb-clock").textContent = hh + ":" + mm;
  }

  function renderGrid() {
    var grid = el("grid");
    grid.innerHTML = "";
    tv.apps.forEach(function (app, i) {
      var tile = document.createElement("div");
      tile.className = "tile" + (app.featured ? " featured" : "") + (i === tv.focus ? " focused" : "");
      tile.style.background = app.color;
      tile.innerHTML = "<span></span><small></small>";
      tile.firstChild.textContent = app.name;
      tile.lastChild.textContent = "v" + app.version;
      tile.addEventListener("click", function () { tv.focus = i; openApp(); });
      grid.appendChild(tile);
    });
  }

  function setState(state) {
    tv.state = state;
    el("screen").setAttribute("data-state", state);
    api("POST", "/api/devices/" + deviceId + "/report", { state: state }).catch(function () {});
  }

  /* ---------- remote control ---------- */

  function openApp() {
    var app = tv.apps[tv.focus];
    if (!app) { return; }
    el("player-title").textContent = app.name;
    setState("watching");
  }

  function watchChannel() {
    el("player-title").textContent = "Kanał " + tv.channel;
    setState("watching");
  }

  function press(key) {
    if (key === "power") {
      setState(tv.state === "standby" ? "menu" : "standby");
      log(tv.state === "standby" ? "Tryb czuwania" : "Włączono");
      return;
    }
    if (tv.state === "standby") { return; }

    if (key === "home" || key === "back") {
      setState("menu");
    } else if (key === "chup" || key === "chdown") {
      tv.channel = Math.max(1, tv.channel + (key === "chup" ? 1 : -1));
      watchChannel();
    } else if (tv.state === "menu") {
      var n = tv.apps.length;
      if (key === "left") { tv.focus = Math.max(0, tv.focus - 1); }
      if (key === "right") { tv.focus = Math.min(n - 1, tv.focus + 1); }
      if (key === "up") { tv.focus = Math.max(0, tv.focus - GRID_COLUMNS); }
      if (key === "down") { tv.focus = Math.min(n - 1, tv.focus + GRID_COLUMNS); }
      if (key === "ok") { openApp(); }
      renderGrid();
    }
  }

  var KEYS = {
    ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
    Enter: "ok", Escape: "back", Backspace: "back", h: "home", p: "power",
    PageUp: "chup", PageDown: "chdown"
  };

  /* ---------- firmware updates ---------- */

  function checkForUpdate() {
    if (tv.updating || !tv.device) { return; }
    api("POST", "/api/ota/check", {
      device_id: deviceId,
      firmware: tv.device.firmware,
      state: tv.state,
      utc_offset_min: tv.device.utc_offset_min
    }).then(function (res) {
      if (res.update) {
        installUpdate(res.update);
      } else if (tv.lastCheck !== "none") {
        log("Brak aktualizacji (FW " + tv.device.firmware + ")");
      }
      tv.lastCheck = res.update ? "update" : "none";
    }).catch(function (err) {
      log("Błąd sprawdzania aktualizacji: " + err.message, "warn");
    });
  }

  function animateProgress(ms) {
    return new Promise(function (resolve) {
      var start = Date.now();
      var timer = setInterval(function () {
        var p = Math.min(1, (Date.now() - start) / ms);
        el("progress-bar").style.width = Math.round(p * 100) + "%";
        if (p >= 1) { clearInterval(timer); resolve(); }
      }, 100);
    });
  }

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function installUpdate(update) {
    tv.updating = true;
    var mb = Math.round(update.size_bytes / 1048576);
    log("Dostępna aktualizacja " + update.build + " (" + mb + " MB)", "warn");
    el("banner").hidden = false;
    el("banner-title").textContent = "Pobieranie aktualizacji " + update.build;
    el("banner-notes").textContent = update.notes || "";
    el("progress-bar").style.width = "0";

    api("POST", "/api/ota/download", { device_id: deviceId, build: update.build })
      .then(function () { return animateProgress(DOWNLOAD_MS); })
      .then(function () {
        el("banner-title").textContent = "Instalowanie " + update.build + "…";
        return wait(INSTALL_MS);
      })
      .then(function () {
        return api("POST", "/api/devices/" + deviceId + "/report", {
          firmware: update.build,
          state: tv.state
        });
      })
      .then(function () {
        log("Zainstalowano " + update.build + ", restart", "ok");
        return refreshDevice();
      })
      .catch(function (err) {
        log("Aktualizacja nieudana: " + err.message, "warn");
      })
      .then(function () {
        el("banner").hidden = true;
        tv.updating = false;
        tv.lastCheck = null;
      });
  }

  /* ---------- boot ---------- */

  function refreshDevice() {
    return api("GET", "/api/devices/" + deviceId).then(function (device) {
      tv.device = device;
      renderStatus();
      renderClock();
      return api("GET", "/api/devices/" + deviceId + "/apps");
    }).then(function (res) {
      tv.apps = res.apps;
      tv.focus = Math.min(tv.focus, Math.max(0, tv.apps.length - 1));
      renderGrid();
    });
  }

  function renderDeviceLinks() {
    api("GET", "/api/devices").then(function (res) {
      var nav = el("devices");
      nav.innerHTML = "";
      res.devices.forEach(function (d) {
        var a = document.createElement("a");
        a.href = "?device=" + encodeURIComponent(d.id);
        a.textContent = d.id + " · " + d.model + " · " + d.region;
        if (d.id === deviceId) { a.className = "current"; }
        nav.appendChild(a);
      });
    }).catch(function () {});
  }

  function boot() {
    document.title = "Lumio TV · " + deviceId;
    document.querySelectorAll("[data-key]").forEach(function (button) {
      button.addEventListener("click", function () { press(button.getAttribute("data-key")); });
    });
    document.addEventListener("keydown", function (e) {
      if (KEYS[e.key]) { e.preventDefault(); press(KEYS[e.key]); }
    });

    refreshDevice().then(function () {
      log("Uruchomiono " + deviceId + ", FW " + tv.device.firmware);
      setState(tv.state);
      checkForUpdate();
      setInterval(checkForUpdate, CHECK_INTERVAL_MS);
      setInterval(renderClock, 10000);
    }).catch(function (err) {
      log("Nie można uruchomić " + deviceId + ": " + err.message, "warn");
    });
    renderDeviceLinks();
  }

  boot();
})();
