import os, re, csv, glob
SRC="/tmp/ssti_src"
DELIM = re.compile(r"(\{\{|\}\})|(\$\{)|(\{%)|(<%)|(#\{)|(\[\[)|(\{php)|(@\{)|(\*\{)|(~\{)|(#set)|(#foreach)|(\{system)|(\{[A-Za-z_])")
STRUCT_ONLY = re.compile(r"^[\s{}\$%<>#\[\]@*~()|.:_\-`'\"=/\\]+$")

def looks_payload(s):
    s=s.strip().strip("`").strip()
    if not s or len(s)>400: return None
    if s.startswith("|") or s.startswith("#!") or s.startswith("//"): return None
    if not DELIM.search(s): return None
    if STRUCT_ONLY.match(s): return None            # bare delimiters like {{ }}
    # need some alnum beyond a lone digit-delimiter reference
    inner=re.sub(r"[{}\[\]$%<>#@*~()`'\"|]", "", s)
    if len(inner.strip())<2: return None
    return s

rows=[]
ENG={"ejs":"EJS","erb-ruby":"ERB","freemarker":"FreeMarker","jinja2-flask":"Jinja2",
     "polyglot":"polyglot","pug-jade":"Pug/Jade","smarty":"Smarty","thymeleaf":"Thymeleaf",
     "twig":"Twig","velocity":"Velocity"}

# 1) payload-box advanced list (per-engine, pre-labeled)
for f in glob.glob(f"{SRC}/ssti-advanced-payload-list/Intruder/*.txt"):
    name=os.path.splitext(os.path.basename(f))[0]
    if name=="all-payloads": continue
    eng=ENG.get(name,"unknown")
    for line in open(f,encoding="utf-8",errors="ignore"):
        p=looks_payload(line)
        if p: rows.append((p,eng,"payload-box/ssti-advanced-payload-list"))

# 2) PATT ssti.fuzz
ff=f"{SRC}/PATT/Server Side Template Injection/Intruder/ssti.fuzz"
if os.path.exists(ff):
    for line in open(ff,encoding="utf-8",errors="ignore"):
        p=looks_payload(line)
        if p: rows.append((p,"mixed","PayloadsAllTheThings/ssti.fuzz"))

# 3) PATT markdown fenced code blocks
LANG={"Python":"python","Java":"java","PHP":"php","JavaScript":"javascript",
      "Ruby":"ruby","ASP":"asp","Elixir":"elixir"}
for md in glob.glob(f"{SRC}/PATT/Server Side Template Injection/*.md"):
    base=os.path.splitext(os.path.basename(md))[0]
    eng=LANG.get(base,"mixed")
    infence=False
    for line in open(md,encoding="utf-8",errors="ignore"):
        if line.strip().startswith("```"):
            infence=not infence; continue
        if infence:
            p=looks_payload(line)
            if p: rows.append((p,eng,"PayloadsAllTheThings/"+base+".md"))

# within-source raw dedup (exact string) just to shrink; real norm-dedup happens on device
seen=set(); out=[]
for p,e,s in rows:
    k=p
    if k in seen: continue
    seen.add(k); out.append((p,e,s))

with open("/mnt/user-data/outputs/ssti_candidates.tsv","w",newline="",encoding="utf-8") as fh:
    w=csv.writer(fh,delimiter="\t"); w.writerow(["payload","engine","source"])
    for p,e,s in out: w.writerow([p,e,s])

from collections import Counter
print("raw candidate lines:",len(rows)," exact-unique:",len(out))
print("by source:",dict(Counter(s for _,_,s in out)))
print("by engine:",dict(Counter(e for _,e,s in out)))
