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
        if s["title"] == title and s.get("parent_id") == parent_id:
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

def parse_markdown_cases(md_filename, section_names):
    md_path = os.path.abspath(f"docs/test-cases/{md_filename}")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    sections = {s: [] for s in section_names}

    lines = content.splitlines()
    current_section = None

    for line in lines:
        if line.startswith("## "):
            matched = False
            for s_name in section_names:
                if s_name.lower() in line.lower():
                    current_section = s_name
                    matched = True
                    break
            if not matched:
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
                
                if "Edge Cases" in current_section or "Contract" in current_section:
                    preconditions = "Edge case / Contract scenario"
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
    print("Initializing Favorites & Tags Qase sync...")
    
    all_created_cases = []

    # --- FAVORITES ---
    fav_parent_id = get_or_create_suite("Favorites")
    print(f"Parent Suite 'Favorites' ID: {fav_parent_id}")

    fav_sub_suites = {
        "Smoke": get_or_create_suite("Smoke", parent_id=fav_parent_id),
        "Negative & Security": get_or_create_suite("Negative & Security", parent_id=fav_parent_id),
        "Edge Cases": get_or_create_suite("Edge Cases", parent_id=fav_parent_id)
    }

    fav_sections = parse_markdown_cases("favorites.md", ["Smoke", "Negative & Security", "Edge Cases"])
    for sec_name, cases in fav_sections.items():
        suite_id = fav_sub_suites[sec_name]
        print(f"\nProcessing Favorites -> '{sec_name}' ({len(cases)} cases)...")
        for c in cases:
            sev_num = map_severity(c["severity"])
            payload = {
                "title": c["title"],
                "suite_id": suite_id,
                "severity": sev_num,
                "preconditions": c["preconditions"],
                "steps": [{
                    "action": c["steps_text"].replace("<br>", "\n"),
                    "expected_result": c["expected"].replace("<br>", "\n")
                }]
            }
            res = qase_request("POST", f"case/{PROJECT_CODE}", payload)
            case_id = res["result"]["id"]
            url = f"https://app.qase.io/case/{PROJECT_CODE}-{case_id}"
            all_created_cases.append((c["title"], url))
            print(f"  Created: {c['title']} -> {url}")

    # --- TAGS ---
    tags_parent_id = get_or_create_suite("Tags")
    print(f"\nParent Suite 'Tags' ID: {tags_parent_id}")

    tags_sub_suites = {
        "Smoke": get_or_create_suite("Smoke", parent_id=tags_parent_id),
        "Contract & Edge Cases": get_or_create_suite("Contract & Edge Cases", parent_id=tags_parent_id)
    }

    tags_sections = parse_markdown_cases("tags.md", ["Smoke", "Contract & Edge Cases"])
    for sec_name, cases in tags_sections.items():
        suite_id = tags_sub_suites[sec_name]
        print(f"\nProcessing Tags -> '{sec_name}' ({len(cases)} cases)...")
        for c in cases:
            sev_num = map_severity(c["severity"])
            payload = {
                "title": c["title"],
                "suite_id": suite_id,
                "severity": sev_num,
                "preconditions": c["preconditions"],
                "steps": [{
                    "action": c["steps_text"].replace("<br>", "\n"),
                    "expected_result": c["expected"].replace("<br>", "\n")
                }]
            }
            res = qase_request("POST", f"case/{PROJECT_CODE}", payload)
            case_id = res["result"]["id"]
            url = f"https://app.qase.io/case/{PROJECT_CODE}-{case_id}"
            all_created_cases.append((c["title"], url))
            print(f"  Created: {c['title']} -> {url}")

    print("\n" + "="*60)
    print("FINAL IMPORT REPORT: Favorites & Tags Test Cases exported to Qase.io")
    print("="*60)
    print(f"Total exported cases: {len(all_created_cases)}")
    for title, url in all_created_cases:
        print(f"- {title}: {url}")

if __name__ == "__main__":
    main()
