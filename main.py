import sys
import logging
from pyrox.client import Hyrox
import requests
from bs4 import BeautifulSoup
from pyrox.scrapers.division import DivisionScraper

def main() -> int:
    logging.basicConfig(level=logging.DEBUG)
    
    # client = Hyrox()
    # events = client.events()

    # print(len(events))

    scraper = DivisionScraper(logging.getLogger())
    res = requests.get("https://www.hyresult.com/event/s7-2025-chicago")
    ds = scraper.scrape(BeautifulSoup(res.content, "html.parser"))
    print(len(ds))
    for d in ds:
        print(d.name)

    return 0

if __name__ == "__main__":
    sys.exit(main())
