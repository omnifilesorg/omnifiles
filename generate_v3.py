#!/usr/bin/env python3
"""
OMNIFILES · Page Generator v3
Δομή: /el/1.html, /el/10/1/1.html, /en/1.html, /en/10/1/1.html
Χρήση: python generate_v3.py --input chapter.json --output-dir ./output --tpl-dir .
"""

import argparse
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path


# ── Config ─────────────────────────────────────────────────────────────────

ADSENSE_CLIENT_ID      = "ca-pub-XXXXXXXXXXXXXXXX"
ADSENSE_SLOT_HEADER    = "1234567890"
ADSENSE_SLOT_INCONTENT = "0987654321"
ADSENSE_SLOT_FOOTER    = "1122334455"
ADSENSE_SLOT_SIDEBAR   = "5544332211"

NATIVE_PLACEHOLDER_PATTERN = re.compile(r'\{\{([A-Z_]+)\}\}')
CONTENT_SPLIT_WORDS = 400


# ── Helpers ────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_template(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓  {path}")

def sub(tpl, key, val):
    return tpl.replace(f"{{{{{key}}}}}", str(val))

def word_count(text):
    return len(re.findall(r'\S+', text))

def apply_native_ads(text, slots):
    if not slots:
        return text
    return NATIVE_PLACEHOLDER_PATTERN.sub(lambda m: slots.get(m.group(1), m.group(0)), text)


# ── URL / Path helpers ─────────────────────────────────────────────────────
#
# Δομή URLs:
#   Κύρια κεφάλαια:  /el/1.html, /el/10.html
#   Υποφάκελοι:      /el/10/1/1.html  (κεφ.κλάδος/σελίδα)
#   Αγγλικά:         /en/1.html, /en/10/1/1.html

def chapter_url(num, lang="el"):
    """
    num="1"       → el/1.html
    num="10"      → el/10.html
    num="10.1.1"  → el/10/1/1.html
    num="10.2.3"  → el/10/2/3.html
    """
    prefix = "en/" if lang == "en" else "el/"
    parts = num.split(".")

    if len(parts) == 1:
        # Κύριο κεφάλαιο
        return f"{prefix}{num}.html"
    elif len(parts) == 3:
        # Υποφάκελος: κεφ / κλάδος / σελίδα
        main, branch, page = parts
        return f"{prefix}{main}/{branch}/{page}.html"
    else:
        # Fallback για μη αναμενόμενη δομή
        return f"{prefix}{'/'.join(parts)}.html"

def chapter_output_path(output_dir, num, lang="el"):
    return Path(output_dir) / chapter_url(num, lang)


# ── Breadcrumb ─────────────────────────────────────────────────────────────

def build_breadcrumb(num, lang="el"):
    pref = "/en" if lang == "en" else "/el"
    parts = num.split(".")

    crumbs = [f'<a href="/">ROOT</a>']
    crumbs.append(f'<a href="{pref}/">ΑΡΧΕΙΟ</a>' if lang == "el" else f'<a href="{pref}/">ARCHIVE</a>')

    if len(parts) == 3:
        main, branch, page = parts
        crumbs.append(f'<a href="{pref}/{main}.html">ΚΕΦ. {main}</a>')
        crumbs.append(f'<a href="{pref}/{main}/{branch}/1.html">ΚΛΑΔΟΣ {branch}</a>')
        crumbs.append(f'<span class="current">FILE #{num}</span>')
    else:
        crumbs.append(f'<span class="current">FILE #{num}</span>')

    return '<span class="sep">›</span>'.join(crumbs)


# ── Parent info (↩ button) ─────────────────────────────────────────────────

def parent_info(num, lang):
    pref = "/en" if lang == "en" else "/el"
    parts = num.split(".")

    if len(parts) == 3:
        main, branch, page = parts
        # Αν είναι η πρώτη σελίδα του κλάδου, πήγαινε στο κεντρικό κεφάλαιο
        if page == "1":
            return f"{pref}/{main}.html", f"ΚΕΦ. {main}"
        else:
            return f"{pref}/{main}/{branch}/1.html", f"ΚΛΑΔΟΣ {branch}"
    else:
        return f"{pref}/", "ΑΡΧΕΙΟ" if lang == "el" else "ARCHIVE"


# ── Status ─────────────────────────────────────────────────────────────────

STATUS_CLASSES = {
    "ΕΝΕΡΓΟ":      "status-active",
    "ACTIVE":      "status-active",
    "ΣΕ ΕΞΕΛΙΞΗ": "status-progress",
    "IN PROGRESS": "status-progress",
    "ΕΚΚΡΕΜΕΙ":   "status-pending",
    "PENDING":     "status-pending",
    "REDACTED":    "status-pending",
    "ΥΠΟ ΠΑΡΑΚΟΛΟΥΘΗΣΗ": "status-active",
}


# ── Content split ──────────────────────────────────────────────────────────

def split_content(paragraphs, split_after=CONTENT_SPLIT_WORDS):
    html = [f"<p>{p}</p>" for p in paragraphs]
    total, split_idx = 0, len(html)
    for i, p in enumerate(paragraphs):
        total += word_count(p)
        if total >= split_after:
            split_idx = i + 1
            break
    return "\n".join(html[:split_idx]), "\n".join(html[split_idx:])


# ── Block builders ─────────────────────────────────────────────────────────

def build_analyst_notes(notes):
    if not notes or not notes.strip():
        return ""
    return (f'<div class="analyst-note">'
            f'<div class="analyst-note-label">ΠΑΡΑΤΗΡΗΣΗ ΑΝΑΛΥΤΗ</div>'
            f'<p>{notes}</p></div>')

def build_intel_request(text):
    if not text or not text.strip():
        return ""
    return (f'<div class="intel-request">'
            f'<div class="intel-request-label">&#9888; ΑΠΑΙΤΟΥΝΤΑΙ ΠΛΗΡΟΦΟΡΙΕΣ</div>'
            f'<p>{text}</p>'
            f'<p>Επικοινωνία: <a href="mailto:intel@omnifiles.org">intel@omnifiles.org</a></p>'
            f'</div>')

def build_nav_prev(prev_num, lang):
    if not prev_num:
        return '<span class="nav-link disabled">← ΔΕΝ ΥΠΑΡΧΕΙ ΠΡΟΗΓΟΥΜΕΝΟ</span>'
    return f'<a href="/{chapter_url(prev_num, lang)}" class="nav-link">← {prev_num}</a>'

def build_nav_next(next_num, lang):
    if not next_num:
        return '<span class="nav-link disabled">ΤΕΛΟΣ →</span>'
    return f'<a href="/{chapter_url(next_num, lang)}" class="nav-link">ΕΠΟΜΕΝΟ {next_num} →</a>'

def build_related_files(related, lang="el"):
    if not related:
        return '<span style="font-family:var(--mono);font-size:.6rem;color:var(--text-sec)">—</span>'
    items = []
    for r in related[:6]:
        url = "/" + chapter_url(r["num"], lang)
        items.append(
            f'<a class="related-file" href="{url}">'
            f'#{r["num"]} {r.get("subject","")}'
            f'<span class="related-file-country">{r.get("country","")}</span>'
            f'</a>'
        )
    return "\n".join(items)


# ── Lang toggle URL ────────────────────────────────────────────────────────

def lang_toggle(num, lang):
    """Αντίστοιχο URL στην άλλη γλώσσα."""
    other = "en" if lang == "el" else "el"
    return chapter_url(num, other), ("EN" if lang == "el" else "GR")


# ── Page info ──────────────────────────────────────────────────────────────

def build_page_info(num, total_in_branch):
    parts = num.split(".")
    page = parts[-1]
    return f"{page} / {total_in_branch}" if str(total_in_branch) != "?" else page


# ── Registry ───────────────────────────────────────────────────────────────

def load_registry(output_dir):
    p = Path(output_dir) / "registry.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def save_registry(output_dir, reg):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / "registry.json").write_text(
        json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

def update_registry(output_dir, num, lang, data, wc):
    reg = load_registry(output_dir)
    reg[f"{lang}:{num}"] = {
        "file_number": num, "lang": lang,
        "subject":  data.get("subject", ""),
        "country":  data.get("country", ""),
        "date":     data.get("date", date.today().isoformat()),
        "word_count": wc,
        "url": "/" + chapter_url(num, lang),
    }
    entries = {k: v for k, v in reg.items() if not k.startswith("_")}
    reg["_totals"] = {
        "total_chapters":  len(entries),
        "total_words_el":  sum(v["word_count"] for v in entries.values() if v.get("lang") == "el"),
        "total_words_en":  sum(v["word_count"] for v in entries.values() if v.get("lang") == "en"),
        "total_countries": len(set(v.get("country","") for v in entries.values() if v.get("country"))),
        "last_updated":    datetime.now().isoformat(),
    }
    save_registry(output_dir, reg)
    t = reg["_totals"]
    print(f"  φάκελοι: {t['total_chapters']} | "
          f"GR: {t['total_words_el']:,} | EN: {t['total_words_en']:,} | "
          f"χώρες: {t['total_countries']}")
    return reg


# ── Sitemap ────────────────────────────────────────────────────────────────

def update_sitemap(output_dir, canonical):
    sm = Path(output_dir) / "sitemap.xml"
    entry = f"  <url><loc>https://omnifiles.org/{canonical}</loc><changefreq>never</changefreq></url>"
    if sm.exists():
        txt = sm.read_text(encoding="utf-8")
        if canonical in txt:
            return
        txt = txt.replace("</urlset>", entry + "\n</urlset>")
    else:
        txt = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               '  <url><loc>https://omnifiles.org/</loc><changefreq>weekly</changefreq></url>\n'
               + entry + "\n</urlset>")
    sm.write_text(txt, encoding="utf-8")


# ── Guinness Log ───────────────────────────────────────────────────────────

def update_guinness_log(output_dir, num, lang, data, wc, html_path):
    log_path = Path(output_dir) / "guinness_log.json"
    file_hash = ""
    if Path(html_path).exists():
        file_hash = hashlib.sha256(Path(html_path).read_bytes()).hexdigest()

    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else {}

    if "_meta" not in log:
        log["_meta"] = {
            "project":               "OMNIFILES",
            "record_attempt":        "Longest work of fiction — human or AI",
            "target_words_per_lang": 12000000,
            "target_total":          24000000,
            "languages":             ["el", "en"],
            "started":               datetime.now().isoformat(),
            "domain":                "https://omnifiles.org",
            "contact":               "intel@omnifiles.org",
        }

    log[f"{lang}:{num}"] = {
        "file_number":  num, "lang": lang,
        "subject":      data.get("subject", ""),
        "country":      data.get("country", ""),
        "word_count":   wc,
        "timestamp":    datetime.now().isoformat(),
        "date_written": data.get("date", date.today().isoformat()),
        "url":          f"https://omnifiles.org/{chapter_url(num, lang)}",
        "sha256":       file_hash,
    }

    entries = {k: v for k, v in log.items() if not k.startswith("_")}
    el_w = sum(v["word_count"] for v in entries.values() if v.get("lang") == "el")
    en_w = sum(v["word_count"] for v in entries.values() if v.get("lang") == "en")
    log["_totals"] = {
        "total_files":    len(entries),
        "total_words_el": el_w,
        "total_words_en": en_w,
        "total_words":    el_w + en_w,
        "pct_el":         round(el_w / 12000000 * 100, 6),
        "pct_en":         round(en_w / 12000000 * 100, 6),
        "pct_total":      round((el_w + en_w) / 24000000 * 100, 6),
        "last_updated":   datetime.now().isoformat(),
    }
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  guinness: {len(entries)} αρχεία | GR {el_w:,} | EN {en_w:,}")


# ── Main generator ─────────────────────────────────────────────────────────

def generate_chapter(data, output_dir, tpl_dir):
    output_dir = Path(output_dir)
    num   = data["file_number"]
    lang  = data.get("lang", "el")
    today = date.today().isoformat()

    tpl = load_template(str(Path(tpl_dir) / "template_chapter_final.html"))

    sponsor_slots = data.get("sponsor_slots", {})
    paragraphs = [apply_native_ads(p, sponsor_slots)
                  for p in data.get("content_paragraphs", [])]

    all_text = " ".join(paragraphs)
    wc = data.get("word_count") or word_count(all_text)

    part1, part2    = split_content(paragraphs)
    parent_url, parent_label = parent_info(num, lang)
    status          = data.get("status", "ΕΝΕΡΓΟ")
    status_cls      = STATUS_CLASSES.get(status.upper(), "")
    canonical       = chapter_url(num, lang)
    og_title        = f"FILE #{num} — {data.get('subject','')}"
    meta_desc       = (all_text[:155] + "…") if len(all_text) > 155 else all_text
    page_title      = f"#{num} {data.get('subject','')}"
    toggle_url, toggle_label = lang_toggle(num, lang)

    reg = update_registry(output_dir, num, lang, data, wc)
    t   = reg.get("_totals", {})

    for k, v in {
        "LANG":               lang,
        "PAGE_TITLE":         page_title,
        "OG_TITLE":           og_title,
        "META_DESC":          meta_desc,
        "CANONICAL":          canonical,
        "DATE":               data.get("date", today),
        "YEAR":               str(date.today().year),
        "FILE_NUMBER":        num,
        "CLASSIFICATION":     data.get("classification", "RESTRICTED"),
        "COUNTRY":            data.get("country", ""),
        "SUBJECT":            data.get("subject", ""),
        "CATEGORY":           data.get("category", ""),
        "STATUS":             status,
        "STATUS_CLASS":       status_cls,
        "PAGE_INFO":          build_page_info(num, data.get("total_in_branch", "?")),
        "BREADCRUMB":         build_breadcrumb(num, lang),
        "CONTENT_PART_1":     part1,
        "CONTENT_PART_2":     part2,
        "ANALYST_NOTES_BLOCK": build_analyst_notes(data.get("analyst_notes", "")),
        "INTEL_REQUEST_BLOCK": build_intel_request(data.get("intel_request", "")),
        "PREV_BLOCK":         build_nav_prev(data.get("prev_num"), lang),
        "PARENT_URL":         parent_url,
        "PARENT_LABEL":       parent_label,
        "NEXT_BLOCK":         build_nav_next(data.get("next_num"), lang),
        "WORD_COUNT":         str(wc),
        "LANG_TOGGLE_URL":    toggle_url,
        "LANG_TOGGLE_LABEL":  toggle_label,
        "ADSENSE_CLIENT_ID":      ADSENSE_CLIENT_ID,
        "ADSENSE_SLOT_HEADER":    ADSENSE_SLOT_HEADER,
        "ADSENSE_SLOT_INCONTENT": ADSENSE_SLOT_INCONTENT,
        "ADSENSE_SLOT_FOOTER":    ADSENSE_SLOT_FOOTER,
        "ADSENSE_SLOT_SIDEBAR":   ADSENSE_SLOT_SIDEBAR,
        "RELATED_FILES":      build_related_files(data.get("related_files", []), lang),
        "TOTAL_CHAPTERS":     str(t.get("total_chapters", 0)),
        "TOTAL_COUNTRIES":    str(t.get("total_countries", 0)),
        "TOTAL_WORDS":        f"{t.get('total_words_el',0) + t.get('total_words_en',0):,}",
    }.items():
        tpl = sub(tpl, k, v)

    out_path = chapter_output_path(output_dir, num, lang)
    write_file(out_path, tpl)
    update_sitemap(output_dir, canonical)
    update_guinness_log(output_dir, num, lang, data, wc, str(out_path))
    print(f"  λέξεις: {wc}")
    return wc


# ── Batch ──────────────────────────────────────────────────────────────────

def batch_generate(chapters, output_dir, tpl_dir):
    total_wc = 0
    for i, ch in enumerate(chapters, 1):
        print(f"\n[{i}/{len(chapters)}] #{ch['file_number']}")
        total_wc += generate_chapter(ch, output_dir, tpl_dir)
    print(f"\n{'─'*40}")
    print(f"Σύνολο: {len(chapters)} κεφάλαια, {total_wc:,} λέξεις")


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OMNIFILES Generator v3")
    parser.add_argument("--input",      required=True,  help="JSON αρχείο (single ή batch array)")
    parser.add_argument("--output-dir", required=True,  help="Root output directory")
    parser.add_argument("--tpl-dir",    default=".",    help="Φάκελος με template αρχεία")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    tpl_dir    = Path(args.tpl_dir).resolve()

    print(f"\nOMNIFILES Generator v3")
    print(f"Output: {output_dir}")
    print(f"{'─'*40}")

    data = load_json(args.input)
    if isinstance(data, list):
        batch_generate(data, output_dir, tpl_dir)
    else:
        print(f"#{data['file_number']}")
        generate_chapter(data, output_dir, tpl_dir)

    print("\nΕτοιμο.")

if __name__ == "__main__":
    main()
