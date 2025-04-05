import csv
import requests
import re
import xml.etree.ElementTree as ET
from typing import List, Optional

NON_ACADEMIC_KEYWORDS = ["pharma", "biotech", "inc", "ltd", "corp", "company", "llc", "co."]
ACADEMIC_KEYWORDS = ["university", "college", "institute", "school", "department", "centre", "hospital"]


def is_non_academic(affil: str) -> bool:
    affil_lower = affil.lower()
    return (any(k in affil_lower for k in NON_ACADEMIC_KEYWORDS)
            and not any(k in affil_lower for k in ACADEMIC_KEYWORDS))


def extract_company(affil: str) -> str:
    return affil.split(",")[0].strip()


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[\w.-]+@[\w.-]+", text)
    return match.group(0) if match else None


def fetch_pubmed_ids(query: str, max_results: int) -> List[str]:
    response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"})
    response.raise_for_status()
    return response.json()['esearchresult']['idlist']


def fetch_pubmed_details(pubmed_ids: List[str]) -> ET.Element:
    response = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                            params={"db": "pubmed", "id": ",".join(pubmed_ids), "retmode": "xml"})
    response.raise_for_status()
    return ET.fromstring(response.content)


def parse_pubmed_xml(root: ET.Element, debug: bool = False) -> List[dict]:
    papers = []
    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID")
            title = article.findtext(".//ArticleTitle")
            date = article.findtext(".//PubDate/Year") or article.findtext(".//PubDate/MedlineDate")

            non_academic_authors, companies, emails = set(), set(), set()
            for author in article.findall(".//Author"):
                forename = author.findtext("ForeName") or ""
                lastname = author.findtext("LastName") or ""
                name = f"{forename} {lastname}".strip()

                for affil in author.findall("AffiliationInfo"):
                    affil_text = affil.findtext("Affiliation") or ""
                    if is_non_academic(affil_text):
                        non_academic_authors.add(name)
                        companies.add(extract_company(affil_text))
                    email = extract_email(affil_text)
                    if email:
                        emails.add(email)

            if non_academic_authors:
                papers.append({
                    "PubmedID": pmid,
                    "Title": title,
                    "Publication Date": date,
                    "Non-academic Author(s)": "; ".join(non_academic_authors),
                    "Company Affiliation(s)": "; ".join(companies),
                    "Corresponding Author Email": next(iter(emails), "")
                })

            if debug:
                print(f"Parsed paper {pmid}")
        except Exception as e:
            if debug:
                print(f"Error parsing paper: {e}")

    return papers


def save_to_csv(data: list, filename: str):
    if not data:
        print("No data to write.")
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Results saved to {filename}")
