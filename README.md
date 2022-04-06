# Transfermarkt scraper

## Usage
```python
from tscraper.scraper import TScraper

scraper = TScraper()

dataframes = scraper.extract_tables(
    url=["https://www.transfermarkt.com/ajax-amsterdam/alletransfers/verein/610"],
    table=["ARRIVALS 21/22", "ARRIVALS 20/21"]
)
```