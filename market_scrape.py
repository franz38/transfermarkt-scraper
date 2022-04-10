from tscraper.scraper import TScraper
import pandas as pd

if __name__ == '__main__':

    scraper = TScraper()

    df_s = scraper.extract_tables(
        url=[
            # "https://www.transfermarkt.com/juventus-fc/transfers/verein/506/plus/1?saison_id=2021&pos=&detailpos=&w_s=",
            "https://www.transfermarkt.com/juventus-fc/transfers/verein/506/plus/1?saison_id=2020&pos=&detailpos=&w_s=",
            "https://www.transfermarkt.com/juventus-fc/transfers/verein/506/plus/1?saison_id=2019&pos=&detailpos=&w_s=",
            "https://www.transfermarkt.com/juventus-fc/transfers/verein/506/plus/1?saison_id=2018&pos=&detailpos=&w_s=",
            "https://www.transfermarkt.com/juventus-fc/transfers/verein/506/plus/1?saison_id=2017&pos=&detailpos=&w_s="
        ],
        table=["ARRIVALS"],
        # guess_types = True,
        dtypes={"Fee":TScraper.FLOAT64}
    )


    # df = pd.concat(df_s, axis=0)

    print(df_s[0])