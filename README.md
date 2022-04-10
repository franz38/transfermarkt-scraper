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

## Parameters
| parameter | type                                             | default value |
|--------|--------------------------------------------------|---------------|
| url    | array of string                                  | ```[]```      |
| table  | array of string                                  | ```[]```      |
| auto_dtypes | boolean                                          | ```False```   |
| dtypes | dictionary {```column name```:```dtype```, ... } | ```{}```      |

