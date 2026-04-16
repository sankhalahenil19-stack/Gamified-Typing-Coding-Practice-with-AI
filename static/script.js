// ================= TEXT DATA =================
const texts = {
    easy: [
        "The cat is on the table",
        "I love typing practice",
        "This is a simple test",
        "Typing is fun and easy",
        "She sells sea shells by the shore",
        "The sun rises in the east every day"
    ],
    medium: [
        "The quick brown fox jumps over the lazy dog",
        "Practice typing daily to improve your speed",
        "Consistency is the key to success in life",
        "Accuracy matters more than speed when typing",
        "Technology is changing the world every single day",
        "Hard work and dedication lead to great results"
    ],
    hard: [
        "Artificial intelligence is transforming modern technology rapidly",
        "Consistency and discipline are essential for long term growth",
        "Advanced typing skills require focus precision and practice daily",
        "Optimization algorithms improve system performance and efficiency greatly",
        "The complexities of quantum computing challenge traditional programming",
        "Perseverance through difficulty builds character and exceptional resilience"
    ]
};

// ================= STATE =================
let currentLevel = "medium";
let aiDifficultyEnabled = true;
let raceCount = 0;
let wpmHistory = [];

let text = "";
let startTime;
let missedKeys = "";
let raceFinished = false;
let keyTimings = [];
let lastKeyTime = null;

// ================= AI DIFFICULTY ENGINE =================
function getAIDifficulty() {
    if (!aiDifficultyEnabled || wpmHistory.length < 1) return currentLevel;

    const avgWpm = wpmHistory.slice(-3).reduce((a, b) => a + b, 0) / Math.min(wpmHistory.length, 3);

    let newLevel;
    if (avgWpm < 25) {
        newLevel = "easy";
    } else if (avgWpm >= 25 && avgWpm < 50) {
        newLevel = "medium";
    } else {
        newLevel = "hard";
    }

    // Show badge if level changed
    if (newLevel !== currentLevel) {
        showDifficultyChange(currentLevel, newLevel, avgWpm);
        currentLevel = newLevel;
        // Sync the dropdown
        const sel = document.getElementById("difficultySelect");
        if (sel) sel.value = newLevel;
    }

    return currentLevel;
}

function showDifficultyChange(from, to, avgWpm) {
    const isUp = (to === "hard" && from !== "hard") ||
                 (to === "medium" && from === "easy");

    const emoji   = isUp ? "🔥" : "💡";
    const dir     = isUp ? "increased" : "decreased";
    const color   = isUp ? "red" : "blue";
    const label   = to.charAt(0).toUpperCase() + to.slice(1);

    showToast(`${emoji} AI adjusted difficulty to ${label} (avg ${Math.round(avgWpm)} WPM)`, color);

    // Animate the difficulty badge
    const badge = document.getElementById("aiBadge");
    if (badge) {
        badge.textContent = `🤖 AI: ${label}`;
        badge.classList.remove("badge-pulse");
        void badge.offsetWidth; // reflow
        badge.classList.add("badge-pulse");
    }
}

// ================= SET LEVEL (manual) =================
function setLevel(level) {
    currentLevel = level;
    aiDifficultyEnabled = false; // user took manual control
    const badge = document.getElementById("aiBadge");
    if (badge) badge.textContent = "🤖 AI: Manual";
}

function toggleAI() {
    aiDifficultyEnabled = !aiDifficultyEnabled;
    const btn = document.getElementById("aiToggleBtn");
    const badge = document.getElementById("aiBadge");
    if (aiDifficultyEnabled) {
        btn.innerHTML = `<span class="ai-dot"></span> AI Auto`;
        btn.classList.add("ai-on");
        if (badge) badge.textContent = "🤖 AI: Auto";
        showToast("🤖 AI Difficulty ON — adapts to your speed!", "green");
    } else {
        btn.innerHTML = `<span class="ai-dot off"></span> AI Off`;
        btn.classList.remove("ai-on");
        if (badge) badge.textContent = "🤖 AI: Off";
        showToast("AI Difficulty turned off", "blue");
    }
}

// ================= AI LOADING OVERLAY =================
function showAILoading() {
    const overlay = document.getElementById("aiLoadingOverlay");
    if (overlay) overlay.classList.add("active");
}
function hideAILoading() {
    const overlay = document.getElementById("aiLoadingOverlay");
    if (overlay) overlay.classList.remove("active");
}

// ================= TOAST =================
function showToast(message, type = "blue") {
    const existing = document.querySelector('.toast');
    if (existing) { existing.classList.add('hide'); setTimeout(() => existing.remove(), 200); }

    setTimeout(() => {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<div class="toast-dot"></div><span>${message}</span>`;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('hide');
            setTimeout(() => toast.remove(), 300);
        }, 3200);
    }, existing ? 250 : 0);
}

// ================= START RACE =================
function startRace() {
    missedKeys = "";
    raceFinished = false;
    keyTimings = [];
    lastKeyTime = null;

    // AI picks difficulty
    getAIDifficulty();

    let arr = texts[currentLevel];
    text = arr[Math.floor(Math.random() * arr.length)];

    const inputBox = document.getElementById("inputBox");
    const display  = document.getElementById("textDisplay");

    inputBox.disabled = true;
    inputBox.value = "";
    document.getElementById("userBar").style.width = "0%";
    document.getElementById("botBar").style.width = "0%";

    // Animate stats reset
    animateStatReset();

    let count = 3;
    display.innerHTML = countdownHTML(count);

    let countdown = setInterval(() => {
        count--;
        if (count > 0) {
            display.innerHTML = countdownHTML(count);
            pulseCountdown();
        } else if (count === 0) {
            display.innerHTML = `<span class="go-text">GO!</span>`;
        } else {
            clearInterval(countdown);
            inputBox.disabled = false;
            inputBox.focus();
            startTime = new Date();
            renderText("");
            moveBot();
        }
    }, 1000);
}

function countdownHTML(n) {
    return `<span class="countdown-num">${n}</span>`;
}

function pulseCountdown() {
    const el = document.querySelector('.countdown-num');
    if (el) { el.classList.add('pop'); setTimeout(() => el.classList.remove('pop'), 400); }
}

function animateStatReset() {
    ['wpm','accuracy','league'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.add('stat-flash');
            setTimeout(() => el.classList.remove('stat-flash'), 500);
        }
    });
    document.getElementById("wpm").innerText = "0";
    document.getElementById("accuracy").innerText = "100";
    document.getElementById("league").innerText = "—";
}

// ================= RENDER TEXT =================
function renderText(input) {
    let html = "";
    for (let i = 0; i < text.length; i++) {
        const ch = text[i] === " " ? "&nbsp;" : text[i];
        if (i < input.length) {
            if (input[i] === text[i]) {
                html += `<span class="char-correct">${ch}</span>`;
            } else {
                html += `<span class="char-wrong animate-wrong">${ch}</span>`;
            }
        } else if (i === input.length) {
            html += `<span class="char-current">${ch}</span>`;
        } else {
            html += `<span class="char-pending">${ch}</span>`;
        }
    }
    document.getElementById("textDisplay").innerHTML = html;
}

// ================= TYPING =================
function handleTyping() {
    if (raceFinished) return;
    const input = document.getElementById("inputBox").value;
    const now = Date.now();
    if (lastKeyTime !== null) keyTimings.push(now - lastKeyTime);
    lastKeyTime = now;

    for (let i = 0; i < input.length; i++) {
        if (input[i] !== text[i] && !missedKeys.includes(text[i])) {
            missedKeys += text[i];
        }
    }

    renderText(input);
    updateStats(input);
    if (input === text) completeRace();
}

// ================= STATS =================
function updateStats(input) {
    const elapsed = (new Date() - startTime) / 1000 / 60;
    const correct  = [...input].filter((c, i) => c === text[i]).length;
    const wpm      = Math.round((correct / 5) / elapsed) || 0;
    const accuracy = input.length ? Math.round((correct / input.length) * 100) : 100;

    animateCounter("wpm", wpm);
    animateCounter("accuracy", accuracy);
    document.getElementById("userBar").style.width = (input.length / text.length) * 100 + "%";

    let league = wpm < 30 ? "🥉 Bronze" : wpm < 60 ? "🥈 Silver" : "🥇 Gold";
    document.getElementById("league").innerText = league;
}

let counterVals = { wpm: 0, accuracy: 100 };
function animateCounter(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const current = counterVals[id] || 0;
    if (current === target) return;
    counterVals[id] = target;
    el.innerText = target;
    el.classList.add('stat-pop');
    setTimeout(() => el.classList.remove('stat-pop'), 300);
}

// ================= BOT =================
function moveBot() {
    let progress = 0;
    let interval = setInterval(() => {
        if (raceFinished) { clearInterval(interval); return; }
        const userWPM = Number(document.getElementById("wpm").innerText) || 0;
        let baseSpeed = currentLevel === "easy" ? 0.22 : currentLevel === "medium" ? 0.33 : 0.48;
        let speed = baseSpeed + (userWPM / 600);
        progress += speed;
        document.getElementById("botBar").style.width = Math.min(progress, 100) + "%";

        if (progress >= 100) {
            clearInterval(interval);
            if (!raceFinished) {
                raceFinished = true;
                const wpm      = document.getElementById("wpm").innerText;
                const accuracy = document.getElementById("accuracy").innerText;
                document.getElementById("inputBox").disabled = true;
                wpmHistory.push(Number(wpm));
                raceCount++;
                showToast("🤖 Bot won! Keep practising 💪", "red");
                saveAndShowResult(false, wpm, accuracy);
            }
        }
    }, 100);
}

// ================= COMPLETE =================
function completeRace() {
    if (raceFinished) return;
    raceFinished = true;
    document.getElementById("inputBox").disabled = true;

    const wpm      = document.getElementById("wpm").innerText;
    const accuracy = document.getElementById("accuracy").innerText;

    wpmHistory.push(Number(wpm));
    raceCount++;

    // Confetti burst on win
    launchConfetti();
    showToast("🎉 Race complete! Getting AI insights...", "green");
    saveAndShowResult(true, wpm, accuracy);
}

// ================= CONFETTI =================
function launchConfetti() {
    const colors = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#8b5cf6','#06b6d4'];
    for (let i = 0; i < 60; i++) {
        setTimeout(() => {
            const c = document.createElement('div');
            c.className = 'confetti-piece';
            c.style.cssText = `
                left:${Math.random()*100}vw;
                background:${colors[Math.floor(Math.random()*colors.length)]};
                animation-duration:${0.8 + Math.random()*1.2}s;
                animation-delay:${Math.random()*0.4}s;
                width:${6+Math.random()*6}px;
                height:${6+Math.random()*6}px;
                border-radius:${Math.random()>0.5?'50%':'2px'};
            `;
            document.body.appendChild(c);
            setTimeout(() => c.remove(), 2000);
        }, i * 18);
    }
}

// ================= SAVE + AI =================
function saveAndShowResult(isWin, wpm, accuracy) {
    showAILoading();
    fetch("/save-result", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wpm, accuracy, missed_keys: missedKeys, timings: keyTimings })
    })
    .then(res => res.json())
    .then(data => {
        hideAILoading();
        showResult(isWin, wpm, accuracy, data.league, data.weak_keys,
                   data.pattern, data.fatigue, data.practice_text,
                   data.feedback, data.suggestion);
        updateHeatmap(data.weak_keys);
    })
    .catch(err => {
        console.error("Backend error:", err);
        hideAILoading();
        const fallbackWeak = missedKeys ? [...new Set(missedKeys.split(""))] : [];
        showResult(isWin, wpm, accuracy, "Guest", fallbackWeak,
                   "N/A", "N/A", "Practice more", "Could not load AI insights.", "");
        updateHeatmap(fallbackWeak);
    });
}

// ================= RESULT MODAL =================
function showResult(isWin, wpm=0, accuracy=0, league="", weak=[], pattern="", fatigue="", suggestion="", feedback="", coachTip="") {
    const modal = document.getElementById("resultModal");
    const title = document.getElementById("resultTitle");

    modal.style.display = "flex";
    title.innerText = isWin ? "🎉 You Win!" : "🤖 Bot Wins!";
    title.className  = isWin ? "win" : "lose";

    // Animate numbers counting up
    countUp("finalWpm", Number(wpm), 800);
    countUp("finalAccuracy", Number(accuracy), 800);

    document.getElementById("finalLeague").innerText   = league;
    document.getElementById("finalWeak").innerText     = weak.length ? weak.join(", ") : "None ✅";
    document.getElementById("finalPattern").innerText  = pattern || "N/A";
    document.getElementById("finalFatigue").innerText  = fatigue || "N/A";
    document.getElementById("finalPractice").innerText = suggestion || "N/A";

    // AI Insight
    const insightEl = document.getElementById("aiInsightText");
    if (insightEl) {
        const parts = [feedback, coachTip].filter(Boolean);
        insightEl.innerText = parts.length ? parts.join(" ") : "No AI insight available.";
    }

    // Show WPM history mini-chart
    updateMiniChart();
}

// ================= COUNT UP ANIMATION =================
function countUp(id, target, duration) {
    const el = document.getElementById(id);
    if (!el) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
        start = Math.min(start + step, target);
        el.innerText = Math.round(start);
        if (start >= target) clearInterval(timer);
    }, 16);
}

// ================= MINI CHART (WPM history) =================
function updateMiniChart() {
    const canvas = document.getElementById("miniChart");
    if (!canvas || wpmHistory.length < 2) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const max = Math.max(...wpmHistory, 1);
    const pts = wpmHistory.map((v, i) => ({
        x: (i / (wpmHistory.length - 1)) * (w - 20) + 10,
        y: h - 10 - (v / max) * (h - 20)
    }));

    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    pts.forEach((p, i) => i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y));
    ctx.stroke();

    // Fill under
    ctx.lineTo(pts[pts.length-1].x, h);
    ctx.lineTo(pts[0].x, h);
    ctx.closePath();
    ctx.fillStyle = "rgba(59,130,246,0.12)";
    ctx.fill();

    // Dots
    pts.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
        ctx.fillStyle = "#60a5fa";
        ctx.fill();
    });
}

// ================= CLOSE MODAL =================
function closeModal() {
    document.getElementById("resultModal").style.display = "none";
    location.reload();
}

// ================= HEATMAP =================
function updateHeatmap(weakKeys) {
    const normalizedWeak = (weakKeys || []).map(k => String(k).toLowerCase().trim());
    document.querySelectorAll(".key").forEach(k => {
        k.classList.remove("weak");
        const keyChar = k.textContent.trim().toLowerCase();
        if (keyChar && normalizedWeak.includes(keyChar)) {
            k.classList.add("weak");
        }
    });
}
