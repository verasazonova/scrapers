# This Python file uses the following encoding: utf-8
import requests
from bs4 import BeautifulSoup
import glob
import pandas as pd
import re
import os.path
from utils import process_single_image
import cv2
import json
import demjson

url_base = "https://www.bareminerals.com"
http_prefix = "https:"


def get_text(r, class_tag, tag='div'):
    x = r.find(tag, class_=class_tag)
    if x is not None:
        return x.get_text().strip().encode('utf-8')
    return ""


def process_product_page(page_):
    soup = BeautifulSoup(page_.content, 'html.parser')
    d = {}

    r = soup.find('div', class_="product-col-2 col-xs-12 col-sm-6 col-lg-6 product-detail")
    if r is not None:
        d["name"] = get_text(r, "h2 product-name", 'h1')
        d["short_description"] = get_text(r, "h3 sub-header", 'h2')
        d["price"] = get_text(r, "product-price")
        d["size"] = get_text(r, "row size-label")
        d["long_desription"] = get_text(r, "product-long-description")
        d["long_description_2"] = get_text(r, "product-tab-main content-mod-sub-04")
        d["ingredients"] = get_text(r, "tab-ingredients")

    r = soup.find('div', class_="product-image-container")
    if r is not None:
        d["image"] = http_prefix + r.find('img')["src"]

    return d


def process_listings(page_):
    soup = BeautifulSoup(page_.content, "html.parser")
    x = soup.find('div', id="products1")

    results = []
    for r in x.find_all('div', class_="product-tile"):
        slug = r.find('a')["href"]
        url = url_base + slug
        d = {}
        d["URL"] = url
        d["product_id"] = r["data-itemid"]
        d["name"] = get_text(r, "product-name")
        results.append(d)

    return results


def scrape(name):
    print("Scraping listing pages")

    # url = "https://www.bareminerals.com/skincare/cleansers/oil-obsessed-total-cleansing-oil/US78850.html"
    url = "https://www.bareminerals.com/skincare/allskincare/?sz=30&amp;start=0&amp"
    page = requests.get(url)
    listings = process_listings(page)

    results = []
    for d in listings:
        page = requests.get(d["URL"])
        page_results = process_product_page(page)
        page_results["URL"] = d["URL"]
        page_results["product_id"] = d["product_id"]
        results.append(page_results)

    df = pd.DataFrame(results)

    print("Donwloaded a total of {} products".format(len(df)))
    df.to_csv("{}.csv".format(name))



def process_filters(name):
    url_base = "https://www.bareminerals.com/skincare/allskincare/"

    params = {"format" : ["Moisturizer", "Cleanser", "Kit", "Mask", "Serum"],
              "areaOfUse": ["Body", "Eyes", "Face", "Neck"],
              "skinType": ["Combination", "Dry", "Normal", "Oily"]}

    params_list = [(key, value) for key, value_list in params.items() for value in value_list]

    for key, value in params_list:
        url = url_base + "?prefn1={}&prefv1={}".format(key, value)
        print(url)
        page = requests.get(url)
        listings = process_listings(page)
        df = pd.DataFrame(listings)
        df["{}:{}".format(key, value)] = True
        print("Donwloaded a total of {} products with {}, {}".format(len(df), key, value))
        df.to_csv("{}_{}_{}.csv".format(name, key, value))


def join(name):

    df = pd.read_csv("{}.csv".format(name), dtype=str)
    df = df.drop(df.columns[0], axis=1)
    print(df.columns)
    for filename in glob.glob("{}_*.csv".format(name)):
        print(filename)
        df1 = pd.read_csv(filename, dtype=str)
        df1 = df1.drop(df1.columns[0], axis=1)
        df = pd.merge(df1, df, how='outer', on=['product_id', 'URL', 'name'])
        print(df1.columns)
        print(df.columns)

    df.to_csv('{}_full.csv'.format(name))


name = "bareminerals/bareminerals"
#scrape(name)
#process_filters(name)
join(name)