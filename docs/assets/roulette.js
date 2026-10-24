/* 빙글 룰렛: 돌림판 그리기, 무작위 결과, 기록, 공유 */
(() => {
  "use strict";
  const TAU = Math.PI * 2;
  const COLORS = ["#ff6b57", "#ffc145", "#3cc9a8", "#5b95ff", "#a487ff", "#ff8cc6", "#5ccbff", "#a6db5e", "#ffa24c", "#4fd1c5"];
  const SEG_INK = "#18202e";
  const MAX_ITEMS = 60;
  const PRESETS = {
    lunch: ["김치찌개", "제육볶음", "짜장면", "돈가스", "쌀국수", "초밥", "햄버거", "칼국수"],
    penalty: ["노래 한 소절", "성대모사 하나", "커피 사기", "애교 3초", "칭찬 세 마디", "다음 판 깍두기", "엉덩이로 이름 쓰기", "면제 찬스"],
    numbers: Array.from({ length: 10 }, (_, i) => String(i + 1)),
    yesno: ["예", "아니오"],
    names: ["민준", "서연", "도윤", "하은", "지호", "수아"],
  };

  const $ = (s) => document.querySelector(s);
  const canvas = $("#wheel");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const ta = $("#items");
  const spinBtn = $("#spin");
  const hub = $("#hub");
  const pointer = $("#pointer");
  const resultBox = $("#result");
  const historyEl = $("#history");
  const removeWinner = $("#remove-winner");
  const soundOn = $("#sound");
  const pageKey = document.body.dataset.page || "main";
  const storeKey = "binggeul-roulette:" + pageKey;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  let segs = [];
  let angle = 0;
  let spinning = false;
  let size = 0;
  let pendingRemove = null;
  let history = [];
  let audio = null;
  let font = "Jua";

  const mod = (a, n) => ((a % n) + n) % n;
  const rand = () => {
    const a = new Uint32Array(1);
    (window.crypto || window.msCrypto).getRandomValues(a);
    return a[0] / 4294967296;
  };
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* 저장 안 돼도 동작 */ } },
  };

  // ---------- 항목 ----------
  function parseItems(text) {
    const out = [];
    for (const raw of text.split(/\r?\n/)) {
      let label = raw.trim();
      if (!label) continue;
      let weight = 1;
      const m = label.match(/^(.*?)\s*\*\s*(\d{1,3})$/);
      if (m && m[1].trim()) {
        label = m[1].trim();
        weight = Math.min(100, Math.max(1, parseInt(m[2], 10)));
      }
      out.push({ label: label.slice(0, 40), weight });
      if (out.length >= MAX_ITEMS) break;
    }
    return out;
  }

  function layout(items) {
    const total = items.reduce((s, it) => s + it.weight, 0);
    let a = 0;
    const out = items.map((it, i) => {
      const span = (it.weight / total) * TAU;
      const seg = { label: it.label, weight: it.weight, start: a, end: a + span, color: COLORS[i % COLORS.length] };
      a += span;
      return seg;
    });
    // 첫 칸과 마지막 칸이 같은 색으로 붙지 않게
    if (out.length > 2 && out[out.length - 1].color === out[0].color) out[out.length - 1].color = COLORS[(out.length + 1) % COLORS.length];
    if (out.length) out[out.length - 1].end = TAU;
    return out;
  }

  function sync(save = true) {
    const items = parseItems(ta.value);
    segs = layout(items);
    const n = items.length;
    $("#count").textContent = n >= MAX_ITEMS ? `${n}개 (최대)` : `${n}개`;
    const ok = n >= 2;
    spinBtn.disabled = !ok || spinning;
    hub.disabled = !ok || spinning;
    spinBtn.textContent = ok ? "돌리기" : "항목을 2개 이상 적어 주세요";
    if (save) store.set(storeKey, ta.value);
    draw();
  }

  // ---------- 그리기 ----------
  function cssVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    size = r.width;
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.width * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function fitText(text, maxW, fs) {
    ctx.font = `${fs}px ${font}, sans-serif`;
    if (ctx.measureText(text).width <= maxW) return [text, fs];
    const small = Math.max(9, fs * 0.82);
    ctx.font = `${small}px ${font}, sans-serif`;
    if (ctx.measureText(text).width <= maxW) return [text, small];
    let t = text;
    while (t.length > 1 && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
    return [t + "…", small];
  }

  function draw(phase) {
    const s = size;
    if (!s) return;
    const c = s / 2;
    const R = c - 2;
    const rim = Math.max(12, s * 0.05);
    const rIn = R - rim;
    ctx.clearRect(0, 0, s, s);

    ctx.beginPath();
    ctx.arc(c, c, R, 0, TAU);
    ctx.fillStyle = cssVar("--rim") || "#1e2738";
    ctx.fill();

    ctx.save();
    ctx.translate(c, c);
    ctx.rotate(angle);
    for (const seg of segs) {
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, rIn, seg.start - Math.PI / 2, seg.end - Math.PI / 2);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      if (segs.length > 1) {
        ctx.strokeStyle = "rgba(24, 32, 46, 0.22)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    ctx.fillStyle = SEG_INK;
    for (const seg of segs) {
      const span = seg.end - seg.start;
      ctx.save();
      ctx.rotate((seg.start + seg.end) / 2 - Math.PI / 2);
      const base = Math.min(s * 0.062, Math.max(9, rIn * Math.min(span, 1.2) * 0.36));
      const [text, fs] = fitText(seg.label, rIn * 0.64, base);
      ctx.font = `${fs}px ${font}, sans-serif`;
      ctx.fillText(text, rIn * 0.9, 1);
      ctx.restore();
    }
    ctx.restore();

    // 테두리 전구 (돌 때 깜빡임)
    const n = Math.max(16, Math.round(s / 24));
    const on = cssVar("--bulb") || "#ffbf1f";
    for (let i = 0; i < n; i++) {
      const a = (i / n) * TAU;
      ctx.beginPath();
      ctx.arc(c + Math.cos(a) * (R - rim / 2), c + Math.sin(a) * (R - rim / 2), rim * 0.2, 0, TAU);
      ctx.fillStyle = phase === undefined || (i + phase) % 2 === 0 ? on : "rgba(255, 255, 255, 0.28)";
      ctx.fill();
    }
  }

  // 바늘(위쪽) 아래에 있는 칸
  function indexAt(theta) {
    const a = mod(-theta, TAU);
    for (let i = 0; i < segs.length; i++) if (a >= segs[i].start && a < segs[i].end) return i;
    return segs.length - 1;
  }

  // ---------- 소리 ----------
  function ensureAudio() {
    if (audio || !soundOn || !soundOn.checked) return;
    try { audio = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { audio = null; }
  }
  function beep(freq, dur, vol, type) {
    if (!audio || !soundOn.checked) return;
    const t = audio.currentTime;
    const o = audio.createOscillator();
    const g = audio.createGain();
    o.type = type || "triangle";
    o.frequency.value = freq;
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(audio.destination);
    o.start(t);
    o.stop(t + dur + 0.02);
  }

  // ---------- 돌리기 ----------
  function applyPendingRemove() {
    if (!pendingRemove) return;
    const lines = ta.value.split(/\r?\n/);
    const i = lines.findIndex((l) => {
      const p = parseItems(l)[0];
      return p && p.label === pendingRemove;
    });
    if (i >= 0) lines.splice(i, 1);
    ta.value = lines.join("\n");
    pendingRemove = null;
    sync();
  }

  function spin() {
    if (spinning) return;
    applyPendingRemove();
    sync();
    if (segs.length < 2) return;
    ensureAudio();
    if (audio && audio.state === "suspended") audio.resume();

    const u = rand() * TAU;
    let target = segs.findIndex((sg) => u < sg.end);
    if (target < 0) target = segs.length - 1;
    const sg = segs[target];
    const at = sg.start + (sg.end - sg.start) * (0.12 + 0.76 * rand());
    const quick = reduceMotion.matches;
    const turns = quick ? 1 : 5 + Math.floor(rand() * 3);
    const from = angle;
    const base = from + TAU * turns;
    const to = base + mod(-at - base, TAU);
    const dur = quick ? 900 : 4300 + rand() * 1500;

    spinning = true;
    ta.readOnly = true;
    spinBtn.disabled = true;
    hub.disabled = true;
    resultBox.classList.remove("done");
    resultBox.innerHTML = '<span class="label">돌아가는 중…</span>';

    let last = indexAt(from);
    const t0 = performance.now();
    const frame = (now) => {
      const p = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - p, 4);
      angle = from + (to - from) * e;
      draw(Math.floor(now / 140) % 2);
      const idx = indexAt(angle);
      if (idx !== last) {
        last = idx;
        beep(1250, 0.03, 0.05, "square");
        if (!quick) {
          pointer.classList.add("tick");
          requestAnimationFrame(() => pointer.classList.remove("tick"));
        }
      }
      if (p < 1) requestAnimationFrame(frame);
      else finish(target);
    };
    requestAnimationFrame(frame);
  }

  function finish(target) {
    angle = mod(angle, TAU);
    draw();
    const idx = indexAt(angle);
    const label = segs[idx].label;
    window.binggeul = { target, index: idx, label };
    spinning = false;
    ta.readOnly = false;
    sync(false);
    beep(660, 0.12, 0.08);
    setTimeout(() => beep(990, 0.22, 0.08), 110);

    resultBox.classList.add("done");
    resultBox.innerHTML = '<span class="label">결과</span><strong></strong>';
    resultBox.querySelector("strong").textContent = label;
    addHistory(label);
    if (removeWinner && removeWinner.checked) {
      pendingRemove = label;
      toast(`다음에 돌릴 때 '${label}'을(를) 빼고 돌려요`);
    }
  }

  // ---------- 기록 ----------
  function addHistory(label) {
    const d = new Date();
    history.unshift({ label, time: `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}` });
    history = history.slice(0, 20);
    renderHistory();
  }
  function renderHistory() {
    historyEl.innerHTML = "";
    if (!history.length) {
      const li = document.createElement("li");
      li.className = "empty";
      li.textContent = "아직 돌린 기록이 없어요.";
      historyEl.append(li);
      return;
    }
    for (const h of history) {
      const li = document.createElement("li");
      const sp = document.createElement("span");
      sp.textContent = h.label;
      const tm = document.createElement("time");
      tm.textContent = h.time;
      li.append(sp, tm);
      historyEl.append(li);
    }
  }

  // ---------- 기타 ----------
  let toastTimer = null;
  function toast(msg) {
    const el = $("#toast");
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { el.hidden = true; }, 2600);
  }

  function setItems(list) {
    if (spinning) return;
    pendingRemove = null;
    ta.value = list.join("\n");
    sync();
  }

  function shuffle() {
    if (spinning) return;
    const lines = ta.value.split(/\r?\n/).filter((l) => l.trim());
    for (let i = lines.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [lines[i], lines[j]] = [lines[j], lines[i]];
    }
    ta.value = lines.join("\n");
    sync();
  }

  async function share() {
    const lines = ta.value.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    const url = location.origin + location.pathname + "?items=" + encodeURIComponent(lines.join("\n"));
    if (navigator.share) {
      try { await navigator.share({ title: document.title, url }); return; } catch (e) { if (e && e.name === "AbortError") return; }
    }
    try {
      await navigator.clipboard.writeText(url);
      toast("링크를 복사했어요. 카톡이나 메신저에 붙여넣으세요.");
    } catch (e) {
      const box = $("#share-url");
      box.value = url;
      box.hidden = false;
      box.select();
      toast("아래 링크를 길게 눌러 복사하세요.");
    }
  }

  function fillRange() {
    const a = parseInt($("#from").value, 10);
    const b = parseInt($("#to").value, 10);
    if (!Number.isFinite(a) || !Number.isFinite(b) || b <= a) { toast("끝 번호를 시작 번호보다 크게 넣어 주세요."); return; }
    if (b - a + 1 > MAX_ITEMS) { toast(`한 번에 ${MAX_ITEMS}개까지 넣을 수 있어요.`); return; }
    setItems(Array.from({ length: b - a + 1 }, (_, i) => String(a + i)));
  }

  // ---------- 시작 ----------
  const fromUrl = new URLSearchParams(location.search).get("items");
  const saved = store.get(storeKey);
  if (fromUrl) ta.value = fromUrl.split("\n").slice(0, MAX_ITEMS).join("\n");
  else if (typeof saved === "string" && saved.trim()) ta.value = saved;

  let typing = null;
  ta.addEventListener("input", () => { pendingRemove = null; clearTimeout(typing); typing = setTimeout(sync, 120); });
  spinBtn.addEventListener("click", spin);
  hub.addEventListener("click", spin);
  document.querySelectorAll("[data-preset]").forEach((b) => b.addEventListener("click", () => setItems(PRESETS[b.dataset.preset])));
  const on = (sel, fn) => { const el = $(sel); if (el) el.addEventListener("click", fn); };
  on("#shuffle", shuffle);
  on("#share", share);
  on("#fill-range", fillRange);
  on("#clear-history", () => { history = []; renderHistory(); });
  document.addEventListener("keydown", (e) => {
    const tag = (e.target.tagName || "").toLowerCase();
    if (["textarea", "input", "button", "select", "a", "summary"].includes(tag)) return;
    if (e.code === "Space" || e.key === "Enter") { e.preventDefault(); spin(); }
  });
  if (window.ResizeObserver) new ResizeObserver(resize).observe(canvas);
  else window.addEventListener("resize", resize);
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", () => draw());
  if (document.fonts && document.fonts.load) {
    document.fonts.load("20px Jua").then(() => draw(), () => { font = "sans-serif"; });
  }

  renderHistory();
  sync(false);
  resize();
  window.binggeulTest = { parseItems, layout, indexAt: () => indexAt(angle), segs: () => segs, spin };
})();
