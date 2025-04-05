# 📚 Paper Fetcher CLI Tool

This is a command-line tool to fetch research papers from PubMed based on a user-specified query.  
The tool identifies papers that have at least one author affiliated with a pharmaceutical or biotech company and outputs the results in a structured CSV file.

---

## 🗂️ Project Structure – How the Code is Organized

```
paper-fetcher/ 
├── fetch/                  # Python module that contains logic to fetch, parse, and filter papers 
│   ├── __init__.py 
│   └── fetch.py                      # Functions to fetch paper data from PubMed                      # Utility functions 
├── cli.py                            # Command-line interface script 
├── pyproject.toml                    # Poetry configuration file 
├── poetry.lock                       # Lock file for dependencies 
├── README.md                         # Project documentation 
├── .gitignore
└── results.csv                       # Output file with filtered paper details
```

---

## ⚙️ Installation & Usage

### 1. Clone the Repository

```bash
git clone https://github.com/21A91A05A8/paper-fetcher.git
cd paper-fetcher
```

### 2. Set Up Environment Using Poetry
Make sure you have Poetry installed.
```bash
poetry install
```
### 3. Activate Virtual Environment (Optional but Recommended)
```bash
poetry shell
```
### 4. Run the Tool
```bash
python cli.py "your search query" --max 5 --file results.csv --debug
```
CLI Options:
* **query** – The PubMed search query (required)
* **--max or -m** – Maximum number of papers to fetch (default: 10)
* **--file or -f** – Filename to save the CSV results (if not provided, prints to console)
* **--debug or -d** – Enable debug output for additional logs

**Example:**
```bash
python -m cli "biotech clinical trial" --max 10 --file results.csv --debug
```
This will fetch 10 papers related to "biotech clinical trial", print debug information, and save the results to a CSV file named **results.csv**.

## 🧰 Tools & Libraries Used
* **Poetry** – for dependency management and packaging  
* **Biopython** – for interacting with the PubMed API  
* **argparse** – for command-line argument parsing  
* **xml.etree.ElementTree** – to parse XML from PubMed
* **re** – for regular expressions to extract author emails
* **VS Code & GitHub** – used for development and version control  

## 📌 Note
The CSV file (results.csv) is optional and will be generated only if the --file option is provided.If no file is specified, the output will be printed to the console.
Ensure your internet connection is active while fetching from PubMed.
