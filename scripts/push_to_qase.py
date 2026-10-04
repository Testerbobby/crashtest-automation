import os
import re
import json
import urllib.request
import urllib.error

QASE_TOKEN = "7ed95479cc03812f7e0ec3feef87e60880c4427eb57fb98c6a888d032967082e"
PROJECT_CODE = "CRASHTEST"
API_BASE = "https://api.qase.io/v1"

HEADERS = {
    "Token": QASE_TOKEN,
    "Content-Type": "application/json",
    "accept": "application/json"
}

def qase_request(method, endpoint, data=None):
    url = f"{API_BASE}/{endpoint}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} for {url}: {err_body}")
        raise

def get_or_create_suite(title, parent_id=None):
    res = qase_request("GET", f"suite/{PROJECT_CODE}?limit=100")
    suites = res.get("result", {}).get("entities", [])
    for s in suites:
        if s["title"] == title:
            return s["id"]
    
    payload = {"title": title}
    if parent_id:
        payload["parent_id"] = parent_id
    res = qase_request("POST", f"suite/{PROJECT_CODE}", payload)
    return res["result"]["id"]

def map_severity(sev_str):
    sev_lower = sev_str.lower()
    if "blocker" in sev_lower:
        return 2
    elif "critical" in sev_lower:
        return 3
    elif "major" in sev_lower:
        return 4
    elif "minor" in sev_lower:
        return 5
    return 4

def parse_markdown_cases():
    md_path = os.path.abspath("docs/test-cases/user-and-authentication.md")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = {
        "Smoke": [],
        "Negative & Boundary": [],
        "Mobile Edge Cases": []
    }

    lines = content.splitlines()
    current_section = None

    for line in lines:
        if "## 1. Smoke Tests" in line:
            current_section = "Smoke"
            continue
        elif "## 2. Boundary & Negative Tests" in line:
            current_section = "Negative & Boundary"
            continue
        elif "## 3. Android & Contract Edge Cases" in line:
            current_section = "Mobile Edge Cases"
            continue
        elif line.startswith("## "):
            current_section = None
            continue

        if current_section and line.startswith("|") and "---" not in line:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 4:
                tc_id = parts[0].replace("**", "").strip()
                
                # Skip header rows
                if not tc_id or not tc_id.startswith("TC-"):
                    continue

                title = parts[1].replace("**", "").strip()
                
                if current_section == "Mobile Edge Cases":
                    preconditions = "Mobile client integration scenario"
                    steps_text = parts[2]
                    expected = parts[3]
                    severity = "Major"
                else:
                    if len(parts) == 5:
                        preconditions = "None"
                        steps_text = parts[2]
                        expected = parts[3]
                        severity = parts[4]
                    elif len(parts) >= 6:
                        preconditions = parts[2]
                        steps_text = parts[3]
                        expected = parts[4]
                        severity = parts[5]
                    else:
                        preconditions = "None"
                        steps_text = parts[2]
                        expected = parts[-2]
                        severity = parts[-1]

                sections[current_section].append({
                    "id": tc_id,
                    "title": f"[{tc_id}] {title}",
                    "preconditions": preconditions,
                    "steps_text": steps_text,
                    "expected": expected,
                    "severity": severity
                })

    return sections

def main():
    print("Initializing Qase sync...")
    
    # 1. Parent suite
    parent_suite_id = get_or_create_suite("User & Authentication")
    print(f"Parent Suite 'User & Authentication' ID: {parent_suite_id}")

    # 2. Sub-suites
    sub_suites = {
        "Smoke": get_or_create_suite("Smoke", parent_id=parent_suite_id),
        "Negative & Boundary": get_or_create_suite("Negative & Boundary", parent_id=parent_suite_id),
        "Mobile Edge Cases": get_or_create_suite("Mobile Edge Cases", parent_id=parent_suite_id)
    }
    for name, sid in sub_suites.items():
        print(f"Sub-suite '{name}' ID: {sid}")

    # 3. Parse and create test cases
    sections = parse_markdown_cases()
    created_cases = []

    for section_name, cases in sections.items():
        suite_id = sub_suites[section_name]
        print(f"\nProcessing section '{section_name}' ({len(cases)} cases)...")
        
        for c in cases:
            sev_num = map_severity(c["severity"])
            
            payload = {
                "title": c["title"],
                "suite_id": suite_id,
                "severity": sev_num,
                "preconditions": c["preconditions"],
                "steps": [
                    {
                        "action": c["steps_text"].replace("<br>", "\n"),
                        "expected_result": c["expected"].replace("<br>", "\n")
                    }
                ]
            }
            
            res = qase_request("POST", f"case/{PROJECT_CODE}", payload)
            case_db_id = res["result"]["id"]
            case_url = f"https://app.qase.io/case/{PROJECT_CODE}-{case_db_id}"
            created_cases.append((c["title"], case_url))
            print(f"  Created: {c['title']} -> {case_url}")

    print("\n" + "="*50)
    print("SUCCESS: Test cases exported to Qase.io!")
    print("="*50)
    for title, url in created_cases:
        print(f"- {title}: {url}")

if __name__ == "__main__":
    main()
