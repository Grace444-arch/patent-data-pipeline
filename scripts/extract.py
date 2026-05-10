import pandas as pd

# Read small samples (VERY IMPORTANT)
patents = pd.read_csv("data/raw/g_patent.tsv", sep="\t", nrows=50000)
abstracts = pd.read_csv("data/raw/g_patent_abstract.tsv", sep="\t", nrows=50000)
inventors = pd.read_csv("data/raw/g_inventor_disambiguated.tsv", sep="\t", nrows=50000)
companies = pd.read_csv("data/raw/g_assignee_disambiguated.tsv", sep="\t", nrows=50000)

print(patents.head())
print(inventors.head())
