#!/usr/bin/env python3
"""
OMNIFILES · Placeholder Generator
Παράγει placeholder HTML για όλους τους φακέλους σε κατάσταση "ΑΠΟΚΡΥΠΤΟΓΡΑΦΕΙΤΑΙ".
Όταν ανεβαίνει το τελικό HTML αντικαθιστά το placeholder.

Χρήση:
  # Δοκιμή — μόνο 3 κεντρικά + 3 υποφάκελοι
  python3 placeholder_gen.py --test --output-dir ./output

  # Πλήρης παραγωγή
  python3 placeholder_gen.py --output-dir ./output
"""

import argparse
import os
from pathlib import Path
from datetime import date


# ── Placeholder Template ───────────────────────────────────────────────────

def build_placeholder(file_number, lang="el"):
    """Παράγει placeholder HTML για έναν φάκελο."""

    parts = file_number.split(".")
    if len(parts) == 1:
        breadcrumb = f'<a href="/">ROOT</a><span class="sep">›</span><a href="/el/">ΑΡΧΕΙΟ</a><span class="sep">›</span><span class="current">FILE #{file_number}</span>'
        parent_url = "/el/"
        parent_label = "ΑΡΧΕΙΟ"
    else:
        main, branch, page = parts
        breadcrumb = (
            f'<a href="/">ROOT</a><span class="sep">›</span>'
            f'<a href="/el/">ΑΡΧΕΙΟ</a><span class="sep">›</span>'
            f'<a href="/el/{main}.html">ΚΕΦ. {main}</a><span class="sep">›</span>'
            f'<a href="/el/{main}/{branch}/1.html">ΚΛΑΔΟΣ {branch}</a><span class="sep">›</span>'
            f'<span class="current">FILE #{file_number}</span>'
        )
        parent_url = f"/el/{main}.html"
        parent_label = f"ΚΕΦ. {main}"

    today = date.today().isoformat()

    return f"""<!DOCTYPE html>
<html lang="el">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="OMNI 14 — Αρχείο #{file_number} υπό αποκρυπτογράφηση.">
  <meta name="robots" content="index, follow">
  <link rel="canonical" href="https://omnifiles.org/el/{_url(file_number)}">
  <link rel="icon" href="/assets/favicon.ico">
  <link rel="stylesheet" href="/assets/style.css">
  <title>#{file_number} ΑΠΟΚΡΥΠΤΟΓΡΑΦΕΙΤΑΙ · OMNIFILES</title>
  <style>
    .decrypt-wrap {{
      padding: 48px 0 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 32px;
    }}

    /* Radar animation */
    .radar {{
      position: relative;
      width: 120px;
      height: 120px;
    }}
    .radar-ring {{
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 1px solid rgba(204,34,0,.3);
    }}
    .radar-ring:nth-child(2) {{ inset: 15px; border-color: rgba(204,34,0,.25); }}
    .radar-ring:nth-child(3) {{ inset: 30px; border-color: rgba(204,34,0,.2); }}
    .radar-ring:nth-child(4) {{ inset: 45px; border-color: rgba(204,34,0,.15); }}
    .radar-sweep {{
      position: absolute;
      inset: 0;
      border-radius: 50%;
      background: conic-gradient(
        from 0deg,
        transparent 0deg,
        rgba(204,34,0,.0) 200deg,
        rgba(204,34,0,.35) 340deg,
        rgba(204,34,0,.5) 360deg
      );
      animation: sweep 3s linear infinite;
    }}
    .radar-dot {{
      position: absolute;
      top: 50%; left: 50%;
      width: 6px; height: 6px;
      background: #cc2200;
      border-radius: 50%;
      transform: translate(-50%,-50%);
      box-shadow: 0 0 8px #cc2200;
    }}
    @keyframes sweep {{
      from {{ transform: rotate(0deg); }}
      to   {{ transform: rotate(360deg); }}
    }}

    /* Scrolling code lines */
    .code-stream {{
      width: 100%;
      max-width: 640px;
      height: 260px;
      overflow: hidden;
      position: relative;
      border: 1px solid #1c1c1a;
      background: #030303;
      padding: 14px 18px;
    }}
    .code-lines {{
      animation: scroll-up 1.5s linear infinite;
    }}
    .code-line {{
      font-family: 'Share Tech Mono', monospace;
      font-size: 1rem;
      line-height: 1.55;
      color: #c2c2c2;
      letter-spacing: .03em;
      white-space: nowrap;
    }}
    .code-line.active {{ color: #ff4422; text-shadow: 0 0 10px rgba(220,50,0,.5); }}
    .code-line.mid    {{ color: #aa3311; }}
    .code-line.dim    {{ color: #555; }}
    @keyframes scroll-up {{
      0%   {{ transform: translateY(0); }}
      100% {{ transform: translateY(-50%); }}
    }}

    /* Status text */
    .decrypt-status {{
      font-family: 'Share Tech Mono', monospace;
      font-size: .7rem;
      color: #cc3300;
      letter-spacing: .3em;
      animation: blink 1.4s ease-in-out infinite;
    }}
    @keyframes blink {{
      0%, 100% {{ opacity: 1; }}
      50%       {{ opacity: .3; }}
    }}

    .decrypt-sub {{
      font-family: 'Share Tech Mono', monospace;
      font-size: .75rem;
      color: #b7b7b7;
      letter-spacing: .15em;
      text-align: center;
      line-height: 2;
    }}

    .decrypt-progress-wrap {{
      width: 100%;
      max-width: 400px;
    }}
    .decrypt-progress-label {{
      font-family: 'Share Tech Mono', monospace;
      font-size: .48rem;
      color: #333;
      letter-spacing: .2em;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
    }}
    .decrypt-progress-bar {{
      height: 3px;
      background: #111;
      border: 1px solid #1c1c1a;
    }}
    .decrypt-progress-fill {{
      height: 100%;
      background: #cc2200;
      animation: progress-anim 8s ease-in-out infinite alternate;
    }}
    @keyframes progress-anim {{
      0%   {{ width: 12%; }}
      40%  {{ width: 67%; }}
      70%  {{ width: 43%; }}
      100% {{ width: 89%; }}
    }}
  </style>
</head>
<body>

<div class="container">

  <header class="site-header">
    <div>
      <a href="/" class="site-logo">OMNIFILES</a>
      <div class="site-tagline">GLOBAL INTELLIGENCE ARCHIVE &middot; UNAUTHORIZED ACCESS PROHIBITED</div>
    </div>
    <div class="site-session">
      <div>ACCESS LEVEL: PUBLIC</div>
      <div>{today}</div>
    </div>
  </header>

  <nav class="breadcrumb">{breadcrumb}</nav>

  <div class="file-meta" style="margin-top:20px;">
    <div class="file-meta-top">
      <div>
        <div class="file-number-label">FILE NUMBER</div>
        <div class="file-number">#{file_number}</div>
      </div>
      <div class="classification-badge" style="color:#cc2200;border-color:#661100;background:#0a0000;">
        ΑΠΟΚΡΥΠΤΟΓΡΑΦΕΙΤΑΙ
      </div>
    </div>
    <div class="file-grid">
      <div>
        <div class="file-field-label">ΚΑΤΑΣΤΑΣΗ</div>
        <div class="file-field-value" style="color:#cc2200;">ΥΠΟ ΕΠΕΞΕΡΓΑΣΙΑ</div>
      </div>
      <div>
        <div class="file-field-label">ΣΥΣΤΗΜΑ</div>
        <div class="file-field-value">PeakBots AI v3</div>
      </div>
      <div>
        <div class="file-field-label">ΕΚΤΙΜΩΜΕΝΗ ΑΠΟΠΕΡΑΤΩΣΗ</div>
        <div class="file-field-value" style="color:#555;">ΑΓΝΩΣΤΗ</div>
      </div>
    </div>
  </div>

  <div class="decrypt-wrap">

    <!-- Radar -->
    <div class="radar">
      <div class="radar-ring"></div>
      <div class="radar-ring"></div>
      <div class="radar-ring"></div>
      <div class="radar-ring"></div>
      <div class="radar-sweep"></div>
      <div class="radar-dot"></div>
    </div>

    <div class="decrypt-status">⬤ ΑΠΟΚΡΥΠΤΟΓΡΑΦΗΣΗ ΣΕ ΕΞΕΛΙΞΗ</div>

    <!-- Scrolling code -->
    <div class="code-stream">
      <div class="code-lines" id="clines"></div>
    </div>

    <!-- Progress -->
    <div class="decrypt-progress-wrap">
      <div class="decrypt-progress-label">
        <span>ΑΠΟΚΡΥΠΤΟΓΡΑΦΗΣΗ</span>
        <span id="pct">—</span>
      </div>
      <div class="decrypt-progress-bar">
        <div class="decrypt-progress-fill"></div>
      </div>
    </div>

    <div class="decrypt-sub">
      Αυτό το αρχείο βρίσκεται υπό αποκρυπτογράφηση<br>
      από το σύστημα Eratosthenes της PeakBots AI.<br>
      Το περιεχόμενο θα είναι διαθέσιμο σύντομα.
    </div>

  </div>

  <nav class="chapter-nav" style="margin-top:48px;">
    <span class="nav-link disabled">← —</span>
    <a href="{parent_url}" class="nav-return">&#x21A9; {parent_label}</a>
    <span class="nav-link disabled">— →</span>
  </nav>

  <footer class="site-footer">
    <div class="footer-left">OMNIFILES &copy; {date.today().year} &middot; FICTION ARCHIVE</div>
    <div class="footer-right">
      <a href="/en/">EN</a> &middot; <a href="/el/about.html">ABOUT</a>
    </div>
  </footer>

  <div class="credits-bar">
    Created by <a href="https://cybernetica.gr" target="_blank" rel="noopener">Cybernetica</a>
    &middot;
    Powered by <a href="https://peakbots.ai" target="_blank" rel="noopener">PeakBots AI</a>
  </div>

  <div class="legal-bar">
    OMNIFILES IS A WORK OF FICTION &middot; ALL CHARACTERS AND EVENTS ARE FICTITIOUS &middot;
    <a href="/el/about.html">ΣΧΕΤΙΚΑ</a>
  </div>

</div>

<script src="/assets/ads.js"></script>
<script>
  // Progress counter
  const fill = document.querySelector('.decrypt-progress-fill');
  const pct  = document.getElementById('pct');
  function updatePct() {{
    const w = parseFloat(getComputedStyle(fill).width);
    const t = parseFloat(getComputedStyle(fill.parentElement).width);
    pct.textContent = Math.round(w/t*100) + '%';
  }}
  setInterval(updatePct, 200);

  // Exotic code generator — APL + Forth + fake assembly mashup
  const T = ['active','active','mid','','','dim','','mid','active','','',''];
  const lines = [
    '⍺∇⍵ ⌊⌈⍟ ÷× CIPHER::BLOCK[{file_number}] ⊂⊃⊆⊇ → 0xAF3C',
    'MOV R7, #0xFF3A  ;;  XOR KEYSTREAM Σ[i+1..n]  PUSH 0xDEAD',
    '⟨ decode ∘ verify ∘ extract ⟩ ← omni14/archive/{file_number}',
    'SWAP DROP DUP ROT  : DECRYPT  BEGIN  KEY@ XOR  LOOP ;',
    'λf.λx. f(f(f(x))) ⊕ 0b10110011 → FRAME::SHIFT ±∞',
    '∀ψ∈Ψ: ψ↑0xC4 ⊗ BLOCK_KEY ≡ AUTH[{file_number}] mod p',
    'CALL 0x7FFE3A  ;; jmp _decrypt_core  ;; nop nop nop xchg',
    '⌿⍀⍴⍉ ∧∨¬≠≤≥ STREAM_CIPHER ⊢⊣ → NULL_FRAME SKIP',
    ': ΣΧΕΔΙΟ  R> DROP  RECURSE  AGAIN  HALT? IF EXIT THEN ;',
    'ld hl, (0xDE3F)  ld b, 0x7E  djnz $  xor a  ret nz',
    '⍎⍕⌷⍒⍋ ⊥⊤ ⍸⍷ TEMPORAL::LOCK ≢ EPOCH[n-1] → PUSH R14',
    'FETCH EXECUTE STORE  ⟦ validate ⟧  :: OMNI14_KEY_7 ;;',
    '∂/∂t ∫∫ K(s,t)ψ(t)dt = λψ(s)  EIGENVAL::SOLVE {file_number}',
    'FF D9 3A 00 4F AA  ;; RAW BLOCK  ;; CRC MISMATCH → RETRY',
    '⊕⊗⊘ ∑∏√ GATE::XOR CHAIN  CLOCK ↑↓ FEED 0xF3 INTO REG_A',
    'BEGIN AGAIN  MARKER::SET  KEY? WHILE DECRYPT REPEAT END',
    'ψ(x,t) = Ae^(ikx-iωt) ⊗ CARRIER_WAVE  MODULATE {file_number}',
    '⌂ ← STACK_FRAME  ;; RSP-8  ;; CANARY::CHECK  JNE _FAULT',
    '∃x ∈ Ω : f(x) ≡ 0  SEARCH::EXHAUST  TIMEOUT → REQUEUE',
    'UNPACK SHUFFLE FOLD  ⋈ JOIN ARCHIVE::INDEX ON KEY={file_number}',
    '⍺∇⍵ ⌊⌈⍟ ÷× CIPHER::BLOCK[{file_number}] ⊂⊃⊆⊇ → 0xAF3C',
    'MOV R7, #0xFF3A  ;;  XOR KEYSTREAM Σ[i+1..n]  PUSH 0xDEAD',
    '⟨ decode ∘ verify ∘ extract ⟩ ← omni14/archive/{file_number}',
    'SWAP DROP DUP ROT  : DECRYPT  BEGIN  KEY@ XOR  LOOP ;',
    'λf.λx. f(f(f(x))) ⊕ 0b10110011 → FRAME::SHIFT ±∞',
    '∀ψ∈Ψ: ψ↑0xC4 ⊗ BLOCK_KEY ≡ AUTH[{file_number}] mod p',
    'CALL 0x7FFE3A  ;; jmp _decrypt_core  ;; nop nop nop xchg',
    '⌿⍀⍴⍉ ∧∨¬≠≤≥ STREAM_CIPHER ⊢⊣ → NULL_FRAME SKIP',
    ': ΣΧΕΔΙΟ  R> DROP  RECURSE  AGAIN  HALT? IF EXIT THEN ;',
    'ld hl, (0xDE3F)  ld b, 0x7E  djnz $  xor a  ret nz',
  ];

  // Διπλό loop για seamless scroll χωρίς κενό
  const el = document.getElementById('clines');
  [0, 1].forEach(() => {{
    lines.forEach((l, i) => {{
      const d = document.createElement('div');
      d.className = 'code-line ' + (T[i % T.length] || '');
      d.textContent = l;
      el.appendChild(d);
    }});
  }});
</script>
</body>
</html>"""


def _url(num):
    parts = num.split(".")
    if len(parts) == 1:
        return f"{num}.html"
    main, branch, page = parts
    return f"{main}/{branch}/{page}.html"


def output_path(output_dir, num, lang="el"):
    return Path(output_dir) / lang / _url(num)


# ── Generator ──────────────────────────────────────────────────────────────

def generate_placeholders(output_dir, test_mode=False, lang="el"):
    output_dir = Path(output_dir)
    count = 0

    # Κεντρικά κεφάλαια
    main_range = range(1, 6) if test_mode else range(1, 101)

    for ch in main_range:
        num = str(ch)
        path = output_path(output_dir, num, lang)
        if path.exists():
            print(f"  SKIP (υπάρχει): {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(build_placeholder(num, lang), encoding="utf-8")
        print(f"  ✓ {path}")
        count += 1

    # Υποφάκελοι (από κεφάλαιο 10 έως 100)
    sub_range = range(10, 13) if test_mode else range(10, 101)
    branch_range = range(1, 4) if test_mode else range(1, 11)
    page_range   = range(1, 4) if test_mode else range(1, 11)

    for ch in sub_range:
        for br in branch_range:
            for pg in page_range:
                num = f"{ch}.{br}.{pg}"
                path = output_path(output_dir, num, lang)
                if path.exists():
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(build_placeholder(num, lang), encoding="utf-8")
                print(f"  ✓ {path}")
                count += 1

    return count


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OMNIFILES Placeholder Generator")
    parser.add_argument("--output-dir", required=True, help="Root output directory")
    parser.add_argument("--lang",       default="el",  help="Γλώσσα (el ή en)")
    parser.add_argument("--test",       action="store_true",
                        help="Test mode — μόνο λίγα αρχεία για δοκιμή")
    args = parser.parse_args()

    mode = "TEST" if args.test else "ΠΛΗΡΗΣ"
    print(f"\nOMNIFILES Placeholder Generator — {mode}")
    print(f"Output: {args.output_dir} / lang: {args.lang}")
    print("─" * 40)

    if args.test:
        print("TEST MODE: κεφ. 1-5 + υποφάκελοι 10-12 / κλάδοι 1-3 / σελίδες 1-3")

    count = generate_placeholders(args.output_dir, args.test, args.lang)

    print(f"\n{'─'*40}")
    print(f"Παράχθηκαν: {count} placeholder αρχεία")

    if args.test:
        print("\nΕπόμενο βήμα — αν είναι εντάξει:")
        print(f"  python3 placeholder_gen.py --output-dir {args.output_dir} --lang {args.lang}")

if __name__ == "__main__":
    main()
