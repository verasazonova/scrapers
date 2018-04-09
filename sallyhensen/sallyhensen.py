import requests
from bs4 import BeautifulSoup
import glob
import pandas as pd
import re
from utils import process_single_image

filter_type = ["skintype", "ingredients", "concerns"]
PROD_KEY = "prod-id"
tags = ["prod-title", "prod-desc", PROD_KEY]
url_base = "https://www.sallyhansen.com"
http_prefix = "https:"

product_lines = ["color-therapy", "complete-salon-manicure", "miracle-gel", "insta-dri", "xtreme-wear"]


def scrape_image(url, dirname, prod_id, with_images=False):
    print(url)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    r = soup.find('div', class_="product__carousel-container").find("picture")
    x = r.find("img")
    image_url = x["data-src"]
    if with_images:
        process_single_image(image_url, dirname + "/{}.jpg".format(prod_id))
    return image_url


def process_product_line_page(page_, prod_line, with_images=False):
    soup = BeautifulSoup(page_.content, 'html.parser')

    r = soup.find('div', class_="product-radio__wrapper")

    p = re.compile(r"background-color:(#.+)")

    results = []
    if r is not None:
        for x in r.find_all("div", class_="product-radio__input-wrapper"):
            d = {"prod_line": prod_line}
            y = x.find('label')
            m = p.search(y["style"])
            if m:
                d["color_hash"] = m.group(1)
            else:
                d["color_hash"] = None
            d["name"] = y["for"].strip().encode('utf-8')
            d["slug"] = y["data-slug"]
            d["image"] = scrape_image(url_base + d["slug"], 'data/{}'.format(prod_line), d["name"], with_images)
            results.append(d)
    return results


def scrape(name, with_images=True):
    print("Scraping listing pages")

    results = []
    for prod_line in product_lines:
        page = requests.get(url_base + '/us/nail-color/' + prod_line)
        page_results = process_product_line_page(page, prod_line, with_images)
        results += page_results
        print("Got {} products for {} line".format(len(page_results), prod_line))

    df = pd.DataFrame(results)
    print("Donwloaded a total of {} products".format(len(df)))
    df.to_csv("{}.csv".format(name))


scrape("sallyhensen")
