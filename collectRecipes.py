import os
import requests
import pandas as pd
from koketData import KoketData
from bs4 import BeautifulSoup
import sys
sys.setrecursionlimit(30000)


def parse_sitemap(sitemap_url):
    headers = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"}
    url_list = []
    soup = BeautifulSoup(requests.get(
        sitemap_url, headers=headers).text, 'lxml')
    for loc in soup.select('url > loc'):
        url = loc.text
        url_list.append(url)
    return url_list


def collect_recipes_list(url_list):
    recipe_dict_list = []
    for url in url_list:
        recipe_object = KoketData(url)
        recipe_object.extract()
        recipe_dict_list.append(recipe_object.recipe_dict)
    return recipe_dict_list


def collect_recipes():
    current_urls = parse_sitemap("https://www.koket.se/sitemap.xml")
    if(len(current_urls) == 0):
        print("Sitemap could not be parsed")
        return

    recipes = pd.read_csv("recipe_data_final.csv")
    print(len(recipes))
    # Keep only recipes on the site currently
    recipes = recipes[recipes['url'].isin(current_urls)]
    print(len(recipes))
    recipes.to_csv("recipe_data_final.csv", index=False)
    old_collected_urls = recipes['url'].tolist()
    new_urls = list(set(current_urls).difference(set(old_collected_urls)))
    print(f"{len(new_urls)} new recipes")
    chunksize = 20
    for ind in range(0, len(new_urls), chunksize):
        recipes_list = collect_recipes_list(new_urls[ind:ind + chunksize])

        pd.DataFrame(recipes_list, columns=recipes.columns).to_csv("recipe_data_final.csv", index=False,
                                                                   header=not os.path.exists("recipe_data_final.csv"), mode='a')
        print(f"{ind+chunksize}\\{len(new_urls)}")


if __name__ == "__main__":
    collect_recipes()
