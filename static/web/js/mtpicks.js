(() => {
  const API = "/api";
  const state = {
    track: localStorage.getItem("mtpicks.track") || "GP",
    tab: "today",
    deviceId: localStorage.getItem("mtpicks.deviceId") || crypto.randomUUID(),
  };
  localStorage.setItem("mtpicks.deviceId", state.deviceId);

  const $ = (sel) => document.querySelector(sel);
  const screen = $("#screen");
  const title = $("#screen-title");
  const trackCodeEl = $("#track-code");

  const TITLES = {
    today: "Today",
    picks: "Our Picks",
    vip: "VIP Board",
    results: "Results",
    more: "More",
  };

  async function api(path, options) {
    const res = await fetch(`${API}${path}`, {
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      const text = await res.text();
      let detail = text;
      try {
        detail = JSON.parse(text).detail || text;
      } catch (_) {}
      throw new Error(detail || `HTTP ${res.status}`);
    }
    return res.json();
  }

  function horses(nums) {
    if (!nums || !nums.length) return '<span class="meta">—</span>';
    return `<div class="horses">${nums
      .map((n) => `<span class="horse">${n}</span>`)
      .join("")}</div>`;
  }

  function statusChip(status, mtp) {
    const mtpLabel =
      mtp == null ? "" : mtp >= 0 ? `${mtp} MTP` : `${Math.abs(mtp)} min`;
    return `<span class="chip">${status || "—"}</span><span class="meta">${mtpLabel}</span>`;
  }

  function setLoading(msg = "Loading…") {
    screen.innerHTML = `<div class="state">${msg}</div>`;
  }

  function setError(err) {
    screen.innerHTML = `<div class="state error">${err.message || err}<br/><button class="btn-ghost" id="retry-btn" style="margin-top:12px">Retry</button></div>`;
    $("#retry-btn")?.addEventListener("click", () => renderTab(state.tab));
  }

  async function renderToday() {
    setLoading();
    const data = await api(`/schedule/today/?track=${encodeURIComponent(state.track)}`);
    const races = (data.meets || []).flatMap((m) => m.races || []);
    if (!races.length) {
      screen.innerHTML = `<div class="state">No card for ${state.track} today. Seed demo data or pick another track.</div>`;
      return;
    }
    screen.innerHTML = races
      .map(
        (r) => `
      <article class="row" data-race="${r.id}">
        <div class="race-num">R${r.race_number}</div>
        <div style="flex:1">
          <p class="title-sm">${r.distance || "—"} · ${r.surface_label || r.surface || ""}</p>
          ${statusChip(r.status_label || r.status, r.minutes_to_post)}
        </div>
      </article>`
      )
      .join("");
    screen.querySelectorAll("[data-race]").forEach((el) => {
      el.addEventListener("click", () => renderRace(el.dataset.race));
    });
  }

  async function renderPicks() {
    setLoading();
    const data = await api(`/our-picks/?track=${encodeURIComponent(state.track)}`);
    const races = data.races || [];
    if (!races.length) {
      screen.innerHTML = `<div class="state">No picks published for ${state.track}.</div>`;
      return;
    }
    screen.innerHTML = races
      .map((r) => {
        const tips = r.tips
          ? ["selections", "max_speed", "first_class", "max_pace"]
              .map((k) => r.tips[k])
              .filter(Boolean)
              .map(
                (b) =>
                  `<div class="tip-label">${b.label}</div>${horses(b.horses)}`
              )
              .join("")
          : "";
        return `
        <article class="block">
          <div class="row" style="border:0;padding:0;cursor:default">
            <div class="race-num">R${r.race_number}</div>
            <div>${statusChip(r.status, r.minutes_to_post)}</div>
          </div>
          ${tips}
          <div class="cols">
            <div><div class="col-label">Morning</div>${horses(r.morning)}</div>
            <div><div class="col-label">5 MTP</div>${horses(r.mtp5)}</div>
          </div>
        </article>`;
      })
      .join("");
  }

  async function renderVip() {
    setLoading();
    const data = await api(`/vip-board/?track=${encodeURIComponent(state.track)}`);
    const races = data.races || [];
    if (!races.length) {
      screen.innerHTML = `<div class="state">VIP board is empty for ${state.track}.</div>`;
      return;
    }
    screen.innerHTML =
      `<div class="cols" style="margin-bottom:8px"><div class="col-label">Morning</div><div class="col-label">Last Hour / 5 MTP</div></div>` +
      races
        .map(
          (r) => `
        <article class="row" data-race="${r.race_id}">
          <div class="race-num">R${r.race_number}</div>
          <div style="flex:1">
            ${statusChip(r.status, r.minutes_to_post)}
            <div class="cols">
              <div>${horses(r.morning)}</div>
              <div>${horses(r.mtp5?.length ? r.mtp5 : r.last_hour)}</div>
            </div>
          </div>
        </article>`
        )
        .join("");
    screen.querySelectorAll("[data-race]").forEach((el) => {
      el.addEventListener("click", () => renderRace(el.dataset.race));
    });
  }

  async function renderResults() {
    setLoading();
    const data = await api(`/results/?track=${encodeURIComponent(state.track)}`);
    const results = data.results || [];
    if (!results.length) {
      screen.innerHTML = `<div class="state">No official results yet for ${state.track}.</div>`;
      return;
    }
    const order = ["W", "P", "S", "EXA", "TRI", "SUPER", "DD"];
    screen.innerHTML = results
      .map((r) => {
        const top = (r.top_three || []).map((t) => t.program_number);
        const divs = order
          .filter((k) => r.dividends && r.dividends[k])
          .map(
            (k) =>
              `<div class="meta">${k} ${r.dividends[k].combination} $${Number(
                r.dividends[k].amount
              ).toFixed(2)}</div>`
          )
          .join("");
        return `
        <article class="block">
          <p class="title-sm">R${r.race_number} · ${r.distance || "—"}</p>
          <div class="col-label">Finish</div>
          ${horses(top)}
          <div class="col-label" style="margin-top:10px">Payouts</div>
          ${divs || '<span class="meta">—</span>'}
        </article>`;
      })
      .join("");
  }

  async function renderRace(id) {
    title.textContent = "Race";
    setLoading();
    const r = await api(`/races/${id}/`);
    title.textContent = `${r.track_code} R${r.race_number}`;
    const runners = (r.runners || [])
      .map(
        (x) => `
      <div class="row" style="cursor:default">
        <div class="race-num">#${x.program_number}</div>
        <div>
          <p class="title-sm">${x.horse_name}${x.scratched ? " (SCR)" : ""}</p>
          <div class="meta">${x.jockey || "—"} · ML ${x.morning_line_odds || "—"}</div>
        </div>
      </div>`
      )
      .join("");
    screen.innerHTML = `
      ${statusChip(r.status_label || r.status, r.minutes_to_post)}
      <p class="meta" style="margin:10px 0">${r.distance || ""}</p>
      <div class="col-label">Runners</div>
      ${runners || '<div class="state">No runners</div>'}
      <button class="btn-ghost" id="back-tab" style="margin-top:16px">← Back</button>`;
    $("#back-tab")?.addEventListener("click", () => renderTab(state.tab));
  }

  async function renderMore() {
    setLoading("Loading referral profile…");
    let profileHtml = "";
    try {
      const me = await api(
        `/referrals/me/?device_id=${encodeURIComponent(state.deviceId)}`
      );
      profileHtml = `
        <div class="more-card">
          <h3>Referrals</h3>
          <p class="meta">Your code</p>
          <p class="title-sm" style="font-family:var(--display);font-size:1.6rem;color:var(--neon)">${me.code}</p>
          <p class="meta">Credits: ${me.credits} · VIP days: ${me.vip_days}</p>
          <button class="btn-ghost" id="share-btn" style="margin-top:10px">Share</button>
        </div>
        <div class="more-card">
          <h3>Claim a code</h3>
          <input class="input" id="claim-code" placeholder="AHRXXXXXX" />
          <button class="btn-ghost" id="claim-btn">Claim</button>
          <p class="meta" id="claim-msg"></p>
        </div>`;
    } catch (e) {
      profileHtml = `<div class="more-card"><h3>Referrals</h3><p class="meta">${e.message}</p></div>`;
    }

    screen.innerHTML = `
      ${profileHtml}
      <div class="more-card">
        <h3>API</h3>
        <p class="meta">Live against this server: <code>/api</code></p>
        <p class="meta">Track: ${state.track}</p>
        <button class="btn-ghost" id="health-btn">Test health</button>
        <p class="meta" id="health-msg"></p>
      </div>
      <div class="more-card">
        <h3>Brand</h3>
        <p class="meta">MTPicks — Minutes To Post. High-edge picks for the American racing board.</p>
        <button class="btn-ghost" id="splash-btn">Show splash</button>
      </div>`;

    $("#share-btn")?.addEventListener("click", async () => {
      try {
        const me = await api(
          `/referrals/me/?device_id=${encodeURIComponent(state.deviceId)}`
        );
        if (navigator.share) {
          await navigator.share({ text: me.share_text, url: me.share_url });
        } else {
          await navigator.clipboard.writeText(me.share_text);
          alert("Share text copied.");
        }
      } catch (e) {
        alert(e.message);
      }
    });

    $("#claim-btn")?.addEventListener("click", async () => {
      const code = $("#claim-code").value.trim();
      const msg = $("#claim-msg");
      try {
        const result = await api("/referrals/claim/", {
          method: "POST",
          body: JSON.stringify({
            device_id: state.deviceId,
            referral_code: code,
          }),
        });
        msg.textContent = `Claimed. +${result.rewards.referee_credits} credits.`;
      } catch (e) {
        msg.textContent = e.message;
      }
    });

    $("#health-btn")?.addEventListener("click", async () => {
      const msg = $("#health-msg");
      try {
        const h = await api("/health/");
        msg.textContent = `OK · ${h.service} · ${h.status}`;
      } catch (e) {
        msg.textContent = e.message;
      }
    });

    $("#splash-btn")?.addEventListener("click", () => {
      $("#app").classList.add("hidden");
      $("#splash").classList.remove("hidden");
    });
  }

  async function renderTab(tab) {
    state.tab = tab;
    title.textContent = TITLES[tab] || "MTPicks";
    trackCodeEl.textContent = state.track;
    document.querySelectorAll(".tab").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tab);
    });
    try {
      if (tab === "today") await renderToday();
      else if (tab === "picks") await renderPicks();
      else if (tab === "vip") await renderVip();
      else if (tab === "results") await renderResults();
      else await renderMore();
    } catch (e) {
      setError(e);
    }
  }

  async function openTracks() {
    const modal = $("#track-modal");
    const list = $("#track-list");
    list.innerHTML = `<div class="state">Loading tracks…</div>`;
    modal.showModal();
    try {
      const data = await api("/tracks/");
      const tracks = Array.isArray(data) ? data : data.results || [];
      list.innerHTML = tracks
        .map(
          (t) => `
        <button type="button" class="track-item ${
          t.code === state.track ? "active" : ""
        }" data-code="${t.code}">
          <span class="code">${t.code}</span>
          <span><strong>${t.name}</strong><br/><span class="meta">${t.state} · ${
            t.country
          }</span></span>
        </button>`
        )
        .join("");
      list.querySelectorAll("[data-code]").forEach((btn) => {
        btn.addEventListener("click", () => {
          state.track = btn.dataset.code;
          localStorage.setItem("mtpicks.track", state.track);
          trackCodeEl.textContent = state.track;
          modal.close();
          renderTab(state.tab);
        });
      });
    } catch (e) {
      list.innerHTML = `<div class="state error">${e.message}</div>`;
    }
  }

  function enterApp() {
    $("#splash").classList.add("hidden");
    $("#app").classList.remove("hidden");
    renderTab(state.tab);
  }

  $("#enter-app")?.addEventListener("click", enterApp);
  $("#track-btn")?.addEventListener("click", openTracks);
  document.querySelectorAll(".tab").forEach((btn) => {
    btn.addEventListener("click", () => renderTab(btn.dataset.tab));
  });
})();
