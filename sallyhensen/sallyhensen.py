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


filter_type = ["skintype", "ingredients", "concerns"]
PROD_KEY = "prod-id"
tags = ["prod-title", "prod-desc", PROD_KEY]
url_base = "https://www.sallyhansen.com"
http_prefix = "https:"

product_lines = ["color-therapy", "complete-salon-manicure", "miracle-gel", "insta-dri", "hard-nails-xtreme-wear", "insta-dri-crayola", "salon-gel-polish-gel-nail-color-starter-kit", "salon-gel-polish-gel-nail-color", "i-heart-nail-art-pen"]


htor = lambda h: tuple(int(h.replace('#', '')[i:i+2], 16) for i in (0, 2 ,4))

rtoh = lambda rgb: '%s' % ''.join(('%02x' % p for p in rgb))


def get_color(url, dirname):
    path = os.path.join(dirname, 'temp_color.jpg')
    process_single_image(url, path)
    img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    i, j, _ = img.shape
    color = img[i/2, j/2, :]
    return rtoh(color)


def process_product_line_page(page_, prod_line, dirname):
    soup = BeautifulSoup(page_.content, 'html.parser')

    r = soup.find('div', class_="product-radio__wrapper")

    with open('{}/{}.html'.format(dirname, prod_line), 'w') as f:
        f.write(page_.content)

    results = []

    p = re.compile(r"background-color:(#.+)")
    pimage = re.compile(r"background-image: url\((.+)\)")
    p_images = re.compile(r"\s+window\.product\s+=")
    images = None

    for x in soup.find_all('script'):
        if p_images.search(x.get_text()):
            s = p_images.sub('', x.get_text())
            s = s.replace('.trim()', '')
            with open('{}/{}.json'.format(dirname, prod_line), 'w') as f:
                f.write(s.encode('utf-8'))
            images = demjson.decode(s)

    if r is not None:
        for x in r.find_all("div", class_="product-radio__input-wrapper"):
            d = {"prod_line": prod_line}
            y = x.find('label')
            m = p.search(y["style"])
            mimage = pimage.search(y["style"])
            d["name"] = y["for"].strip().encode('utf-8')
            if mimage:
                d["hex"] = get_color(mimage.group(1), dirname)
                d["colr_swatch_image"] = mimage.group(1)
            elif m:
                d["hex"] = m.group(1).replace("#", "")
            else:
                d["hex"] = None  #images["skus"][d["name"]]["colors"][0]["hex"] or None
            d["slug"] = url_base + y["data-slug"]
            if images:
                d["image"] = images["skus"][d["name"]]["gallery"][0]["thumbnailImage"]
            results.append(d)
    return results


def scrape(name):
    print("Scraping listing pages")

    results = []
    for prod_line in product_lines:
        page = requests.get(url_base + '/us/nail-color/' + prod_line)
        page_results = process_product_line_page(page, prod_line, 'data_may')
        results += page_results
        print("Got {} products for {} line".format(len(page_results), prod_line))

    df = pd.DataFrame(results)

    print("Donwloaded a total of {} products".format(len(df)))
    df.to_csv("{}.csv".format(name))
    return df


def join(filename1, filename2):

    df1 = pd.read_csv(filename1, dtype=str)
    df2 = pd.read_csv(filename2, dtype=str)
    df1['simplified_name'] = df1['name'].str.split('-', expand=True, n=1)[1].str.replace('-', '')
    df1['simplified_prod_line'] = df1['prod_line'].str.replace('-as-', '')

    df2['simplified_name'] = df2['Shade Name'].str.replace('[\s+-]', '').str.replace('[.,?!\']', '').str.lower().str.replace('é', 'e').str.replace('è', 'e').str.replace('ç', 'c')
    df2['simplified_prod_line'] = df2['Product name'].str.replace('\s+', '-').str.lower().str.replace('-as', '').str.replace('®-\+', '')

    df = pd.merge(df1, df2, how='outer', on=['simplified_name', 'simplified_prod_line'])
    print(df)
    df.to_csv('SH_spring_full.csv')


scrape("sallyhansen_may")
join("sallyhansen_may.csv", "SH-8.05.csv")
