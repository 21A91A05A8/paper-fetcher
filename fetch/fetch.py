# # get_papers_list/fetcher.py

# from typing import List, Dict, Tuple
# import requests
# from xml.etree import ElementTree as ET


# ACADEMIC_KEYWORDS = ['university', 'institute', 'college', 'school', 'faculty', 'department']
# COMPANY_KEYWORDS = ['pharma', 'biotech', 'inc', 'corp', 'ltd', 'gmbh', 'llc', 'therapeutics', 'laboratories']

# def is_company_affiliation(affiliation: str) -> bool:
#     """Check if affiliation likely belongs to a company."""
#     affil_lower = affiliation.lower()
#     return any(keyword in affil_lower for keyword in COMPANY_KEYWORDS) and not any(keyword in affil_lower for keyword in ACADEMIC_KEYWORDS)

# def fetch_pubmed_ids(query: str, retmax: int = 20) -> List[str]:
#     """Fetch list of PubMed IDs matching the query."""
#     base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
#     params = {
#         "db": "pubmed",
#         "term": query,
#         "retmax": retmax,
#         "retmode": "json"
#     }
#     response = requests.get(base_url, params=params)
#     response.raise_for_status()
#     data = response.json()
#     return data["esearchresult"]["idlist"]

# def fetch_details(pubmed_ids: List[str]) -> List[Dict]:
#     """Fetch paper details for given PubMed IDs."""
#     base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
#     params = {
#         "db": "pubmed",
#         "id": ",".join(pubmed_ids),
#         "retmode": "xml"
#     }
#     response = requests.get(base_url, params=params)
#     response.raise_for_status()
#     root = ET.fromstring(response.content)

#     results = []
#     for article in root.findall(".//PubmedArticle"):
#         pmid = article.findtext(".//PMID")
#         title = article.findtext(".//ArticleTitle")
#         pub_date = article.findtext(".//PubDate/Year") or "Unknown"

#         non_academic_authors = []
#         company_affiliations = []
#         corresponding_email = "Not found"

#         for author in article.findall(".//Author"):
#             affil_info = author.find(".//AffiliationInfo")
#             if affil_info is not None:
#                 affil_text = affil_info.findtext("Affiliation", default="").strip()
#                 if is_company_affiliation(affil_text):
#                     name_parts = [
#                         author.findtext("ForeName", default=""),
#                         author.findtext("LastName", default="")
#                     ]
#                     author_name = " ".join(part for part in name_parts if part)
#                     non_academic_authors.append(author_name)
#                     company_affiliations.append(affil_text)
#                     if "@" in affil_text:
#                         corresponding_email = affil_text.split()[-1]

#         if non_academic_authors:
#             results.append({
#                 "PubmedID": pmid,
#                 "Title": title,
#                 "Publication Date": pub_date,
#                 "Non-academic Author(s)": "; ".join(non_academic_authors),
#                 "Company Affiliation(s)": "; ".join(company_affiliations),
#                 "Corresponding Author Email": corresponding_email
#             })

#     return results


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
