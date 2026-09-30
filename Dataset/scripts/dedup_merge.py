import re, csv, json, urllib.parse
from collections import Counter

U="/mnt/user-data/uploads/research"
CAND="/mnt/user-data/outputs/ssti_candidates.tsv"

def norm(s):
    prev=None
    while prev!=s:
        prev=s; s=urllib.parse.unquote(s)
    return re.sub(r"\s+"," ",s.strip().lower())

def skeleton(s):
    s=norm(s)
    s=re.sub(r"'[^']*'","'S'",s); s=re.sub(r'"[^"]*"','"S"',s)
    s=re.sub(r"\d+","N",s); s=re.sub(r"\s+","",s)
    return s

def load_lines(p):
    return [l.strip() for l in open(p,encoding="utf-8",errors="ignore") if l.strip()]

train=load_lines(f"{U}/Dataset/raw payloads text files/ssti.txt")
benign=load_lines(f"{U}/Dataset/raw payloads text files/benign.txt")
tn=set(norm(x) for x in train)
bn=set(norm(x) for x in benign)
test=[]
for line in open(f"{U}/external_test_set/ssti_test_positives.jsonl",encoding="utf-8"):
    test.append(json.loads(line)["payload"])
te=set(norm(x) for x in test)

cand=[]
with open(CAND,encoding="utf-8") as f:
    r=csv.DictReader(f,delimiter="\t")
    for row in r: cand.append(row)

seen=set(); new=[]; dup_train=0; leak_test=0; conflict_benign=0; within_dup=0
for row in cand:
    n=norm(row["payload"])
    if n in seen: within_dup+=1; continue
    seen.add(n)
    if n in te: leak_test+=1; continue          # never train on test
    if n in bn: conflict_benign+=1; continue     # labeled benign elsewhere -> skip
    if n in tn: dup_train+=1; continue            # already in training
    new.append(row)

for row in new: row["base_id"]=skeleton(row["payload"])

# outputs
with open("/mnt/user-data/outputs/new_training_positives.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(["payload","engine","source","base_id"])
    for row in new: w.writerow([row["payload"],row["engine"],row["source"],row["base_id"]])

# merged full training positives (existing + new), with provenance
with open("/mnt/user-data/outputs/train_positives_merged.tsv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f,delimiter="\t"); w.writerow(["payload","engine","source","base_id","label"])
    for x in train:
        w.writerow([x,"unknown","existing/ssti.txt",skeleton(x),1])
    for row in new:
        w.writerow([row["payload"],row["engine"],row["source"],row["base_id"],1])

exist_uni=len(tn); new_uni=len(new)
merged_norm=set(tn); [merged_norm.add(norm(r["payload"])) for r in new]
exist_skel=set(skeleton(x) for x in train)
merged_skel=set(exist_skel); [merged_skel.add(r["base_id"]) for r in new]

print("=== candidates:",len(cand))
print("dropped within-candidate dup :",within_dup)
print("dropped already in training   :",dup_train)
print("dropped test-set leakage      :",leak_test)
print("dropped benign conflict       :",conflict_benign)
print("NEW unique training positives :",new_uni)
print("-"*50)
print("existing unique positives     :",exist_uni)
print("MERGED unique positives       :",len(merged_norm))
print("existing unique skeletons(base_id):",len(exist_skel))
print("MERGED unique skeletons(base_id)  :",len(merged_skel),"  <-- true group count for splitting")
print("-"*50)
print("NEW by source:",dict(Counter(r["source"] for r in new)))
print("NEW by engine:",dict(Counter(r["engine"] for r in new)))
