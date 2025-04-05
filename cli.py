from typing import List, Optional
import requests
import xml.etree.ElementTree as ET
import csv
import re
import argparse
from pathlib import Path

# Heuristics to identify non-academic affiliations
def is_non_academic(affil: str) -> bool:
    non_academic_keywords = ["pharma", "biotech", "inc", "ltd", "corp", "company", "llc", "co."]
    academic_keywords = ["university", "college", "institute", "school", "department", "centre", "hospital"]

    affil_lower = affil.lower()
    return (any(k in affil_lower for k in non_academic_keywords) and
            not any(k in affil_lower for k in academic_keywords))

def extract_company(affil: str) -> str:
    affil = affil.strip()
    if "," in affil:
        return affil.split(",")[0].strip()
    return affil

def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w.-]+@[\w.-]+", text)
    return match.group(0) if match else None

def fetch_pubmed_ids(query: str, max_results: int, debug: bool) -> List[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=params)
    response.raise_for_status()
    ids = response.json()['esearchresult']['idlist']
    if debug:
        print(f"Fetched PubMed IDs: {ids}")
    return ids

def fetch_pubmed_details(pubmed_ids: List[str], debug: bool):
    params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "xml"
    }
    response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", params=params)
    response.raise_for_status()
    if debug:
        print("Fetched paper details XML")
    return ET.fromstring(response.content)

def parse_pubmed_xml(root, debug: bool) -> List[dict]:
    papers = []
    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle")
            date = article.findtext(".//PubDate/Year") or article.findtext(".//PubDate/MedlineDate")

            non_academic_authors = set()
            companies = set()
            emails = set()

            author_list = article.findall(".//Author")
            for author in author_list:
                lastname = author.findtext("LastName") or ""
                forename = author.findtext("ForeName") or ""
                full_name = f"{forename} {lastname}".strip()

                for affil in author.findall("AffiliationInfo"):
                    affil_text = affil.findtext("Affiliation") or ""
                    if is_non_academic(affil_text):
                        non_academic_authors.add(full_name)
                        companies.add(extract_company(affil_text))
                    email = extract_email(affil_text)
                    if email:
                        emails.add(email)

            if debug:
                print(f"Paper {pmid} parsed")

            if non_academic_authors:
                papers.append({
                    "PubmedID": pmid,
                    "Title": title,
                    "Publication Date": date,
                    "Non-academic Author(s)": "; ".join(non_academic_authors),
                    "Company Affiliation(s)": "; ".join(companies),
                    "Corresponding Author Email": next(iter(emails), "")
                })
        except Exception as e:
            if debug:
                print(f"Error parsing article: {e}")

    return papers

def save_to_csv(data: List[dict], filename: str):
    if not data:
        print("No data to write.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Results saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Fetch non-academic papers from PubMed")
    parser.add_argument("query", type=str, help="Search query for PubMed")
    parser.add_argument("--max", type=int, default=10, help="Max number of papers to fetch")
    parser.add_argument("--file", type=str, help="Output CSV filename")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    pubmed_ids = fetch_pubmed_ids(args.query, args.max, args.debug)
    xml_root = fetch_pubmed_details(pubmed_ids, args.debug)
    paper_data = parse_pubmed_xml(xml_root, args.debug)

    if args.file:
        save_to_csv(paper_data, args.file)
    else:
        for paper in paper_data:
            print(paper)

if __name__ == "__main__":
    main()
