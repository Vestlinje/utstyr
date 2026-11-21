"""Lagar éi offentleg fil per eining (p/<offentlegId>.json) frå utstyrsregisteret.
Bruk: python3 verktoy/export.py <innfil> <repo-mappe>
Innfil: JSON-linjer {id, data} (frå db_list) eller ops.json-format ({path, data}).
Berre offentlege felt blir med. Det finst ingen samleliste.
Skriv "Ingen endringar" og avsluttar utan å røre filer viss alt er likt.
"""
import json, sys, os, glob

UTE = {"Meldt feil", "Til reparasjon", "Kassert"}

def load(path):
    raw = open(path, encoding="utf-8").read().strip()
    rows = json.loads(raw) if raw.startswith("[") else [json.loads(l) for l in raw.splitlines() if l.strip().startswith("{")]
    out = []
    for r in rows:
        if "path" in r:
            out.append((r["path"].split("/")[-1], r["data"]))
        elif r.get("data") is not None:
            out.append((r["id"], r["data"]))
    return out

def public(d):
    return {
        "navn": d.get("navn", ""),
        "kategori": d.get("kategori", ""),
        "produsent": d.get("produsent", ""),
        "serienr": d.get("serienr", ""),
        "internnr": d.get("internnr", ""),
        "ute": d.get("tilstand") in UTE,
        "kontrollar": [
            {k: c.get(k) for k in ("type", "intervall", "sist", "neste", "utfortAv", "ref") if c.get(k) not in (None, "")}
            for c in d.get("kontrollar", [])
        ],
        "dokument": [x for x in d.get("offentlegeDokument", []) if x.get("url")],
        **({"bilete": d["offentlegBilete"]} if str(d.get("offentlegBilete", "")).startswith("p/i/") else {}),
    }

if __name__ == "__main__":
    src, repo = sys.argv[1], sys.argv[2]
    pdir = os.path.join(repo, "p")
    os.makedirs(pdir, exist_ok=True)
    want = {}
    for _id, d in load(src):
        tok = d.get("offentlegId")
        if tok and all(c in "0123456789abcdef" for c in tok):
            want[tok + ".json"] = json.dumps(public(d), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    have = {os.path.basename(f) for f in glob.glob(os.path.join(pdir, "*.json"))}
    changed = 0
    for name in have - set(want):
        os.remove(os.path.join(pdir, name)); changed += 1
    for name, body in want.items():
        fp = os.path.join(pdir, name)
        if not os.path.exists(fp) or open(fp, encoding="utf-8").read() != body:
            open(fp, "w", encoding="utf-8").write(body); changed += 1
    print("Ingen endringar" if not changed else f"{changed} filer endra ({len(want)} einingar)")
