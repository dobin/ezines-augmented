import requests
from bs4 import BeautifulSoup
import json
from time import sleep

def fetch_issue_data(issue_number):
    url = f"https://phrack.org/issues/{issue_number}/1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch issue #{issue_number}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", {"type": "application/ld+json"})
    if not script_tag:
        print(f"No JSON-LD metadata found for issue #{issue_number}")
        return None

    try:
        data = json.loads(script_tag.string)
        editor = data.get("author", {}).get("name", "Unknown")
        release_date = data.get("datePublished", "Unknown")
        return {
            "issue": issue_number,
            "editor": editor,
            "release_date": release_date
        }
    except json.JSONDecodeError:
        print(f"JSON parse error for issue #{issue_number}")
        return None


def main():
    print("Fetching Phrack issues...\n")
    results = []

    for i in range(1, 73):  # Issues 1–72
        data = fetch_issue_data(i)
        if data:
            results.append(data)
            print(f"Current issue : #{data['issue']} | Release date : {data['release_date']} | Editor : {data['editor']}")
        sleep(0.5)  # polite delay to avoid hammering the site

    # Optional: Save to CSV file
    with open("phrack_issues.csv", "w", encoding="utf-8") as f:
        f.write("Issue,Release Date,Editor\n")
        for d in results:
            f.write(f"{d['issue']},{d['release_date']},{d['editor']}\n")

    print("\n✅ Done! Results saved to phrack_issues.csv")

if __name__ == "__main__":
    main()
