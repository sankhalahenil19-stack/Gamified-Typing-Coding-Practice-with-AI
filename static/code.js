let currentQuestionId = 1;
let isRunning = false;

// ── RUN CODE ──────────────────────────────────────────
function runCode(onDone) {
    if (isRunning) return;
    isRunning = true;

    const code     = document.getElementById("codeInput").value;
    const langEl   = document.getElementById("language");
    const language = langEl ? langEl.value : "python";
    const box      = document.getElementById("resultBox");

    box.innerHTML = '<span style="color:var(--text-muted)">Running…</span>';

    fetch("/run-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, question_id: currentQuestionId, language })
    })
    .then(res => res.json())
    .then(data => {
        isRunning = false;
        if (data.error) {
            box.innerHTML = `<p class="fail">❌ ${data.error}</p>`;
            return;
        }

        let html = `<h3>Status: ${data.status}</h3>`;
        data.results.forEach(r => {
            html += `<p class="${r.includes('❌') ? 'fail' : 'pass'}">${r}</p>`;
        });
        box.innerHTML = html;

        const accepted = data.status && data.status.includes("Accepted");
        if (typeof onDone === 'function') onDone(accepted);

        // Auto-advance on accepted (only when called from runCode directly, not submitCode)
        if (accepted && typeof onDone !== 'function') {
            setTimeout(() => loadQuestion(parseInt(currentQuestionId) + 1), 1500);
        }
    })
    .catch(err => {
        isRunning = false;
        box.innerHTML = `<p class="fail">❌ Network error: ${err.message}</p>`;
    });
}

// ── LOAD QUESTION ─────────────────────────────────────
function loadQuestion(id) {
    currentQuestionId = id;

    fetch("/get-question/" + id)
    .then(res => res.json())
    .then(data => {
        if (data.error) return;  // no more questions

        // Highlight active question in sidebar
        document.querySelectorAll(".question-item").forEach(el => {
            el.style.background = '';
            el.style.color = 'var(--text-secondary)';
            el.style.fontWeight = '';
        });
        const active = document.querySelector(`.question-item[data-id="${id}"]`);
        if (active) {
            active.style.background = 'var(--surface-2)';
            active.style.color = 'var(--text-primary)';
            active.style.fontWeight = '600';
        }

        // starter_code now arrives with real newlines from the server
        document.getElementById("codeInput").value = data.starter_code || '';
        const diffColor = {Easy:'#22c55e', Medium:'#f59e0b', Hard:'#ef4444'}[data.difficulty] || '#8b9ab5';
        const diffBadge = data.difficulty
            ? `<span style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px;background:${diffColor}22;color:${diffColor};border:1px solid ${diffColor}44;margin-left:8px;">${data.difficulty}</span>`
            : '';
        document.getElementById("problemBox").innerHTML =
            `<strong style="color:var(--text-primary)">${data.title}</strong>${diffBadge}` +
            `<span style="color:var(--text-muted);margin-left:8px;">— ${data.description}</span>`;
    })
    .catch(() => {});
}

// ── SUBMIT ────────────────────────────────────────────
function submitCode() {
    runCode(function(accepted) {
        if (accepted) {
            setTimeout(() => loadQuestion(parseInt(currentQuestionId) + 1), 1500);
        }
    });
}

// ── INIT ──────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
    // Sidebar click handlers
    document.querySelectorAll(".question-item").forEach(item => {
        item.addEventListener("click", function () {
            loadQuestion(this.getAttribute("data-id"));
        });
    });

    // Load first question automatically
    const first = document.querySelector(".question-item");
    if (first) loadQuestion(first.getAttribute("data-id"));
});
