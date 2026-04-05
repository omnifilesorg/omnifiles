#!/usr/bin/env python3
"""
OMNIFILES · Page Generator v2
Χρήση: python generate.py --input chapter.json --output-dir /var/www/omnifiles.org
"""

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path


# ── Config ─────────────────────────────────────────────────────────────────

# Αντίγραψε εδώ τα IDs σου από το Google AdSense
ADSENSE_CLIENT_ID   = "ca-pub-XXXXXXXXXXXXXXXX"   # ← το δικό σου
ADSENSE_SLOT_HEADER    = "1234567890"              # Header leaderboard
ADSENSE_SLOT_INCONTENT = "0987654321"              # In-content
ADSENSE_SLOT_FOOTER    = "1122334455"              # Footer
ADSENSE_SLOT_SIDEBAR   = "5544332211"              # Sidebar

# Native ad placeholder — αντικαθίσταται στο κείμενο
# Παράδειγμα JSON: "sponsor_slots": {"COFFEE_BRAND": "Nespresso", "COMPANY_NAME": "Cybernetica"}
NATIVE_PLACEHOLDER_PATTERN = re.compile(r'\{\{([A-Z_]+)\}\}')

# Λέξεις ανά παράγραφο για split περιεχομένου (in-content ad μετά από αυτές)
CONTENT_SPLIT_WORDS = 400


# ── Helpers ────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_template(tpl_path):
    with open(tpl_path, encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✓  {path}")

def sub(tpl, key, val):
    return tpl.replace(f"{{{{{key}}}}}", str(val))

def word_count(text):
    return len(re.findall(r'\S+', text))


# ── Native ad replacement ──────────────────────────────────────────────────

def apply_native_ads(text, sponsor_slots):
    """Αντικαθιστά {{COFFEE_BRAND}} κλπ με τα ονόματα των χορηγών."""
    if not sponsor_slots:
        return text
    def replacer(m):
        key = m.group(1)
        return sponsor_slots.get(key, m.group(0))
    return NATIVE_PLACEHOLDER_PATTERN.sub(replacer, text)


# ── Content split ──────────────────────────────────────────────────────────

def split_content(paragraphs, split_after_words=CONTENT_SPLIT_WORDS):
    """
    Χωρίζει τις παραγράφους σε δύο μέρη για το in-content ad.
    Κόβει μετά από ~split_after_words λέξεις.
    """
    html_parts = [f"<p>{p}</p>" for p in paragraphs]
    total = 0
    split_idx = len(html_parts)  # default: όλα στο part1

    for i, p in enumerate(paragraphs):
        total += word_count(p)
        if total >= split_after_words:
            split_idx = i + 1
            break

    part1 = "\n".join(html_parts[:split_idx])
    part2 = "\n".join(html_parts[split_idx:])
    return part1, part2


# ── URL helpers ────────────────────────────────────────────────────────────

def chapter_url(num, lang="el"):
    prefix = "en/" if lang == "en" else ""
    parts = num.split(".")
    if len(parts) == 1:
        return f"{prefix}{num}.html"
    main = parts[0]
    branch = ".".join(parts[:2])
    page = parts[-1]
    return f"{prefix}{main}/{branch}/{page}.html"

def chapter_output_path(output_dir, num, lang="el"):
    return Path(output_dir) / chapter_url(num, lang)


# ── Breadcrumb ─────────────────────────────────────────────────────────────

def build_breadcrumb(num, lang="el"):
    pref = "/en" if lang == "en" else ""
    parts = num.split(".")
    crumbs = [f'<a href="{pref}/">ROOT</a>']

    if len(parts) >= 2:
        main = parts[0]
        crumbs.append(f'<a href="{pref}/{main}/index.html">CHAPTER {main}</a>')
    if len(parts) >= 3:
        branch = ".".join(parts[:2])
        crumbs.append(f'<a href="{pref}/{parts[0]}/{branch}/index.html">BRANCH {branch}</a>')

    crumbs.append(f'<span class="current">FILE #{num}</span>')
    return '<span class="sep">›</span>'.join(crumbs)


# ── Status ─────────────────────────────────────────────────────────────────

STATUS_CLASSES = {
    "ΕΝΕΡΓΟ": "status-active", "ACTIVE": "status-active",
    "ΣΕ ΕΞΕΛΙΞΗ": "status-progress", "IN PROGRESS": "status-progress",
    "ΕΚΚΡΕΜΕΙ": "status-pending", "PENDING": "status-pending",
}


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
            f'<p>Εάν διαθέτετε σχετικές πληροφορίες: '
            f'<a href="mailto:intel@omnifiles.org">intel@omnifiles.org</a></p>'
            f'</div>')

def build_nav_prev(prev_num, lang):
    if not prev_num:
        return '<span class="nav-link disabled">← ΔΕΝ ΥΠΑΡΧΕΙ ΠΡΟΗΓΟΥΜΕΝΟ</span>'
    url = "/" + chapter_url(prev_num, lang)
    return f'<a href="{url}" class="nav-link">← {prev_num}</a>'

def build_nav_next(next_num, lang):
    if not next_num:
        return '<span class="nav-link disabled">ΤΕΛΟΣ ΚΛΑΔΟΥ →</span>'
    url = "/" + chapter_url(next_num, lang)
    return f'<a href="{url}" class="nav-link">ΕΠΟΜΕΝΟ {next_num} →</a>'

def parent_info(num, lang):
    pref = "/en" if lang == "en" else ""
    parts = num.split(".")
    if len(parts) == 3:
        main, branch = parts[0], ".".join(parts[:2])
        return f"{pref}/{main}/{branch}/index.html", f"BRANCH {branch}"
    elif len(parts) == 2:
        return f"{pref}/{parts[0]}/index.html", f"ΚΕΦ. {parts[0]}"
    return f"{pref}/", "ROOT"

def build_related_files(related):
    """related = [{"num": "6.1.2", "subject": "Δρ. Χαν", "country": "ΗΠΑ"}, ...]"""
    if not related:
        return '<span style="font-family:var(--mono);font-size:.6rem;color:var(--text-sec)">—</span>'
    items = []
    for r in related[:6]:  # max 6
        url = "/" + chapter_url(r["num"])
        items.append(
            f'<a class="related-file" href="{url}">'
            f'#{r["num"]} {r.get("subject","")}'
            f'<span class="related-file-country">{r.get("country","")}</span>'
            f'</a>'
        )
    return "\n".join(items)


# ── Registry ───────────────────────────────────────────────────────────────

def load_registry(output_dir):
    reg_path = Path(output_dir) / "registry.json"
    if reg_path.exists():
        return json.loads(reg_path.read_text(encoding="utf-8"))
    return {}

def save_registry(output_dir, reg):
    reg_path = Path(output_dir) / "registry.json"
    reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")

def update_registry(output_dir, num, lang, data, wc):
    reg = load_registry(output_dir)
    key = f"{lang}:{num}"
    reg[key] = {
        "file_number": num, "lang": lang,
        "subject": data.get("subject", ""),
        "country": data.get("country", ""),
        "date": data.get("date", date.today().isoformat()),
        "word_count": wc,
        "url": "/" + chapter_url(num, lang),
    }
    reg["_totals"] = {
        "total_chapters": sum(1 for k in reg if not k.startswith("_")),
        "total_words_el": sum(v["word_count"] for k,v in reg.items()
                              if not k.startswith("_") and v.get("lang")=="el"),
        "total_words_en": sum(v["word_count"] for k,v in reg.items()
                              if not k.startswith("_") and v.get("lang")=="en"),
        "total_countries": len(set(v.get("country","") for k,v in reg.items()
                                   if not k.startswith("_") and v.get("country"))),
        "last_updated": datetime.now().isoformat(),
    }
    save_registry(output_dir, reg)
    t = reg["_totals"]
    print(f"  φάκελοι: {t['total_chapters']} | "
          f"GR: {t['total_words_el']:,} λέξεις | "
          f"EN: {t['total_words_en']:,} λέξεις | "
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
        txt = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            '  <url><loc>https://omnifiles.org/</loc><changefreq>weekly</changefreq></url>\n'
            + entry + "\n</urlset>"
        )
    sm.write_text(txt, encoding="utf-8")


# ── Main generator ─────────────────────────────────────────────────────────

def generate_chapter(data, output_dir, tpl_dir):
    output_dir = Path(output_dir)
    num     = data["file_number"]
    lang    = data.get("lang", "el")
    today   = date.today().isoformat()

    tpl = load_template(str(Path(tpl_dir) / "template_chapter_final.html"))

    # Native ad replacement
    sponsor_slots = data.get("sponsor_slots", {})
    paragraphs = [apply_native_ads(p, sponsor_slots)
                  for p in data.get("content_paragraphs", [])]

    all_text = " ".join(paragraphs)
    wc = data.get("word_count") or word_count(all_text)

    part1, part2 = split_content(paragraphs)

    parent_url, parent_label = parent_info(num, lang)
    parts = num.split(".")
    total = data.get("total_in_branch", "?")
    page_info = f"{parts[-1]} / {total}"
    status = data.get("status", "ΕΝΕΡΓΟ")
    status_cls = STATUS_CLASSES.get(status.upper(), "")
    canonical = chapter_url(num, lang)
    og_title = f"FILE #{num} — {data.get('subject','')}"
    meta_desc = (all_text[:155] + "…") if len(all_text) > 155 else all_text
    page_title = f"#{num} {data.get('subject','')}"
    lang_toggle_url = ("en/" + canonical) if lang == "el" else canonical.replace("en/", "")
    lang_toggle_label = "EN" if lang == "el" else "GR"

    # Update registry and get totals for sidebar
    reg = update_registry(output_dir, num, lang, data, wc)
    t = reg.get("_totals", {})
    total_chapters = t.get("total_chapters", 0)
    total_countries = t.get("total_countries", 0)
    total_words_label = f"{(t.get('total_words_el',0)+t.get('total_words_en',0)):,}"

    # Apply all substitutions
    for k, v in {
        "LANG":              lang,
        "PAGE_TITLE":        page_title,
        "OG_TITLE":          og_title,
        "META_DESC":         meta_desc,
        "CANONICAL":         canonical,
        "DATE":              data.get("date", today),
        "YEAR":              str(date.today().year),
        "FILE_NUMBER":       num,
        "CLASSIFICATION":    data.get("classification", "RESTRICTED"),
        "COUNTRY":           data.get("country", ""),
        "SUBJECT":           data.get("subject", ""),
        "CATEGORY":          data.get("category", ""),
        "STATUS":            status,
        "STATUS_CLASS":      status_cls,
        "PAGE_INFO":         page_info,
        "BREADCRUMB":        build_breadcrumb(num, lang),
        "CONTENT_PART_1":    part1,
        "CONTENT_PART_2":    part2,
        "ANALYST_NOTES_BLOCK": build_analyst_notes(data.get("analyst_notes", "")),
        "INTEL_REQUEST_BLOCK": build_intel_request(data.get("intel_request", "")),
        "PREV_BLOCK":        build_nav_prev(data.get("prev_num"), lang),
        "PARENT_URL":        parent_url,
        "PARENT_LABEL":      parent_label,
        "NEXT_BLOCK":        build_nav_next(data.get("next_num"), lang),
        "WORD_COUNT":        str(wc),
        "LANG_TOGGLE_URL":   lang_toggle_url,
        "LANG_TOGGLE_LABEL": lang_toggle_label,
        "ADSENSE_CLIENT_ID": ADSENSE_CLIENT_ID,
        "ADSENSE_SLOT_HEADER":    ADSENSE_SLOT_HEADER,
        "ADSENSE_SLOT_INCONTENT": ADSENSE_SLOT_INCONTENT,
        "ADSENSE_SLOT_FOOTER":    ADSENSE_SLOT_FOOTER,
        "ADSENSE_SLOT_SIDEBAR":   ADSENSE_SLOT_SIDEBAR,
        "RELATED_FILES":     build_related_files(data.get("related_files", [])),
        "TOTAL_CHAPTERS":    str(total_chapters),
        "TOTAL_COUNTRIES":   str(total_countries),
        "TOTAL_WORDS":       total_words_label,
    }.items():
        tpl = sub(tpl, k, v)

    out_path = chapter_output_path(output_dir, num, lang)
    write_file(out_path, tpl)
    update_sitemap(output_dir, canonical)
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
    parser = argparse.ArgumentParser(description="OMNIFILES Generator v2")
    parser.add_argument("--input",      required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--tpl-dir",    default=".")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    tpl_dir    = Path(args.tpl_dir).resolve()

    print(f"\nOMNIFILES Generator v2")
    print(f"Output: {output_dir}\n{'─'*40}")

    data = load_json(args.input)
    if isinstance(data, list):
        batch_generate(data, output_dir, tpl_dir)
    else:
        print(f"#{data['file_number']}")
        generate_chapter(data, output_dir, tpl_dir)

    print("\nΕτοιμο.")

if __name__ == "__main__":
    main()
