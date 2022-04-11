# Transfermarkt scraper
A simple python package that facilitates transfermarkt scraping
## Usage
```python
from tscraper.scraper import TScraper

scraper = TScraper()

dataframes = scraper.extract_tables(
    url=["https://www.transfermarkt.com/ajax-amsterdam/alletransfers/verein/610"],
    table=["ARRIVALS 21/22", "ARRIVALS 20/21"]
)
```

## DataTypes

The default value of ```auto_dtypes``` is ```False```, 
in this way TScraper will just return the text found 
in the columns, however for certain column types this behavior 
could create problems.

Setting ```auto_dtypes``` to ```True``` will allow TScraper to automatically
detect the column format and parse it accordingly.

Through the ```dtypes``` parameter it is also possible to 
directly define the way in which the column will be analyzed.

```python
dataframes = scraper.extract_tables(
    url = [ ... ],
    table = [ ... ],
    auto_dtypes = True,
    dtypes = {
        "column_1":TScraper.PLAYER,
        "column_2":TScraper.DATE,
              }
)
```

Available values are: ```DEFAULT```, ```NUMERIC```, 
```DATETIME```, ```TEAM```, ```PLAYER```


## Parameters
| parameter | type                       | default value |
|--------|----------------------------|---------------|
| url    | string or array of strings | ```[]```      |
| table  | string or array of strings | ```[]```      |
| auto_dtypes | boolean                    | ```False```   |
| dtypes | dictionary                 | ```{}```      |

