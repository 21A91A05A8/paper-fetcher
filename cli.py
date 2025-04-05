import argparse
from pathlib import Path
from fetch import fetch_pubmed_ids, fetch_pubmed_details, parse_pubmed_xml, save_to_csv

def main():
    parser = argparse.ArgumentParser(description="Fetch non-academic papers from PubMed")
    parser.add_argument("query", type=str, help="Search query for PubMed")
    parser.add_argument("--max", type=int, default=10, help="Maximum number of papers to fetch")
    parser.add_argument("-f", "--file", type=str, help="Output CSV filename")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")

    args = parser.parse_args()

    try:
        pubmed_ids = fetch_pubmed_ids(args.query, args.max)
        if not pubmed_ids:
            print("⚠️ No PubMed IDs found for the given query.")
            return

        xml_root = fetch_pubmed_details(pubmed_ids)
        paper_data = parse_pubmed_xml(xml_root, args.debug)

        if args.file:
            save_to_csv(paper_data, args.file)
        else:
            for paper in paper_data:
                print(paper)

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
