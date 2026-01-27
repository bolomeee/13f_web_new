import requests
import json
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def debug_cik(cik):
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {
        "User-Agent": "MyCustomAgent/1.0 (debug@example.com)",
        "Accept-Encoding": "gzip, deflate",
    }

    logger.info(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        name = data.get("name")
        print(f"Company Name: {name}")

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])

        print(f"Total recent filings found: {len(forms)}")

        # Check for 13F related forms
        found_13f = False
        print("\n--- Recent 13F Filings ---")
        for i, form in enumerate(forms):
            if "13F" in form:
                print(f"Date: {dates[i]}, Form: {form}")
                found_13f = True

        if not found_13f:
            print("No 13F forms found in 'recent' list.")
            print("First 10 forms found:", forms[:10])

    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    # Test with CIKs mentioned in logs
    ciks = ["0000916119", "0001738693"]
    for cik in ciks:
        print(f"\nChecking CIK: {cik}")
        debug_cik(cik)
