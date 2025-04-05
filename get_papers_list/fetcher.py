# get_papers_list/fetcher.py

from typing import List, Dict, Tuple
import requests
from xml.etree import ElementTree as ET


ACADEMIC_KEYWORDS = ['university', 'institute', 'college', 'school', 'faculty', 'department']
COMPANY_KEYWORDS = ['pharma', 'biotech', 'inc', 'corp', 'ltd', 'gmbh', 'llc', 'therapeutics', 'laboratories']

def is_company_affiliation(affiliation: str) -> bool:
    """Check if affiliation likely belongs to a company."""
    affil_lower = affiliation.lower()
    return any(keyword in affil_lower for keyword in COMPANY_KEYWORDS) and not any(keyword in affil_lower for keyword in ACADEMIC_KEYWORDS)

def fetch_pubmed_ids(query: str, retmax: int = 20) -> List[str]:
    """Fetch list of PubMed IDs matching the query."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json"
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()
    return data["esearchresult"]["idlist"]

def fetch_details(pubmed_ids: List[str]) -> List[Dict]:
    """Fetch paper details for given PubMed IDs."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    results = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID")
        title = article.findtext(".//ArticleTitle")
        pub_date = article.findtext(".//PubDate/Year") or "Unknown"

        non_academic_authors = []
        company_affiliations = []
        corresponding_email = "Not found"

        for author in article.findall(".//Author"):
            affil_info = author.find(".//AffiliationInfo")
            if affil_info is not None:
                affil_text = affil_info.findtext("Affiliation", default="").strip()
                if is_company_affiliation(affil_text):
                    name_parts = [
                        author.findtext("ForeName", default=""),
                        author.findtext("LastName", default="")
                    ]
                    author_name = " ".join(part for part in name_parts if part)
                    non_academic_authors.append(author_name)
                    company_affiliations.append(affil_text)
                    if "@" in affil_text:
                        corresponding_email = affil_text.split()[-1]

        if non_academic_authors:
            results.append({
                "PubmedID": pmid,
                "Title": title,
                "Publication Date": pub_date,
                "Non-academic Author(s)": "; ".join(non_academic_authors),
                "Company Affiliation(s)": "; ".join(company_affiliations),
                "Corresponding Author Email": corresponding_email
            })

    return results
