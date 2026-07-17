#!/usr/bin/env python3
"""Weekly Summary Generator — compiles Sribuu agent activity for past week."""
import subprocess, json, urllib.request
from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))
SITE = "https://sribuu.pages" + ".dev"

def main():
    repo = "lafuan/Sribuu"
    now = datetime.now(WIB)
    print(f"= Sribuu Weekly Summary — {now.strftime('%d %B %Y %H:%M WIB')}\n")
    print("## CI/CD Health")
    ci = subprocess.run(["gh","run","list","-R",repo,"--workflow","deploy",
        "--limit","5","--json","conclusion,headBranch,createdAt,displayTitle"],
        capture_output=True,text=True,timeout=30).stdout.strip()
    try:
        for r in json.loads(ci):
            s = "PASS" if r["conclusion"]=="success" else "FAIL"
            print(f"  [{s}] {r['displayTitle'][:60]} ({r['createdAt'][:10]})")
    except: print(f"  CI: {ci[:200]}")
    print("\n## Site Health")
    try:
        req = urllib.request.Request(SITE,method="HEAD")
        r = urllib.request.urlopen(req,timeout=10)
        print(f"  OK — HTTP {r.status}")
    except Exception as e: print(f"  ERROR — {e}")
    print("\n## Agent Activity (7 days)")
    issues = subprocess.run(["gh","issue","list","-R",repo,"--label","agent-recommendation",
        "--state","all","--limit","10","--json","number,title,state,labels,updatedAt"],
        capture_output=True,text=True,timeout=30).stdout.strip()
    try:
        for i in json.loads(issues):
            labs = ",".join(l["name"] for l in i.get("labels",[]))
            ic = "OPEN" if i["state"]=="open" else "CLOSED"
            print(f"  [{ic}] #{i['number']} {i['title'][:60]} [{labs}] ({i['updatedAt'][:10]})")
    except: print(f"  Issues: {issues[:200]}")
    print(f"\n--- Generated: {now.strftime('%Y-%m-%d %H:%M WIB')} ---")

if __name__=="__main__": main()
