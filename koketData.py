import requests
import traceback
from recipe_scrapers._exceptions import SchemaOrgException
from recipe_scrapers import scrape_me
import os
import sys


class KoketData():

    def __init__(self, url):
        self.url = url
        self.recipe_dict = {}
        self.recipe_dict["url"] = self.url

    def extract(self):
        try:
            try:
                scraper = scrape_me(self.url)
                self.recipe_dict["title"] = scraper.title()
                self.recipe_dict["total_time"] = scraper.total_time()
                self.recipe_dict["yields"] = scraper.yields()
                self.recipe_dict["ingredients"] = scraper.ingredients()
                self.recipe_dict["instructions"] = scraper.instructions()
                self.recipe_dict["image"] = scraper.image()
                #self.recipe_dict["host"] = scraper.host()
                #self.recipe_dict["links"] = scraper.links()
                #self.recipe_dict["nutrients"] = scraper.nutrients()
                self.recipe_dict["author"] = scraper.author()
                self.recipe_dict["ratings"] = scraper.ratings()
            except (requests.exceptions.ConnectionError, RecursionError) as e:
                print(e, self.url)
                sys.exit(0)
        except Exception as e:
            print(e, self.url)
            return

    def clean(self):
        pass
