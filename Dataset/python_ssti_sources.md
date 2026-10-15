# Trusted sources for Python SSTI payloads (beyond Jinja2)

Ranked by authority for citing in a paper.

| # | Source | What it is | Authority | URL |
|---|--------|------------|-----------|-----|
| 1 | Kettle, PortSwigger (2015) | Original SSTI research paper ("Server-Side Template Injection") | Primary research | https://portswigger.net/research/server-side-template-injection |
| 2 | Hackmanit *template-injection-table* / *-playground* | Academic per-engine detection table + Docker labs | Academic | https://github.com/Hackmanit/template-injection-playground |
| 3 | SonarSource research blog | Vendor security research (engine-specific SSTI writeups) | Vendor research | https://www.sonarsource.com/blog/ |
| 4 | SSTImap (maintained tplmap fork) | Tool; per-engine detect/render payloads in `plugins/` | Tool source | https://github.com/vladko312/SSTImap |
| 5 | PayloadsAllTheThings — *Server Side Template Injection* | Community payload collection, per-engine sections | Community (not verified) | https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection |
| 6 | HackTricks — SSTI | Community reference | Community (custom license) | https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection |

Python engines worth covering: **Mako, Tornado, Django, Cheetah3, Genshi, Chameleon** (plus Jinja2 you already have).

## Reviewer caveats
- A `source_url` proves provenance, not that the payload fires. Validate every collected
  payload through the matching lab server and keep only confirmed ones — otherwise the new
  rows are the same "claimed-vulnerable" quality as the current unlabeled set.
- Community sources (5,6) are broad but noisy; prefer 1–4 for anything you state as fact.
- Check licenses before redistributing collected payloads in your dataset release
  (PayloadsAllTheThings = CC-BY; HackTricks = custom terms).
