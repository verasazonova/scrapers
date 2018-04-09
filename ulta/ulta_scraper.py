import requests
from bs4 import BeautifulSoup
import glob
import pandas as pd
from utils import process_single_image

filter_type = ["skintype", "ingredients", "concerns"]
PROD_KEY = "prod-id"
tags = ["prod-title", "prod-desc", PROD_KEY]
url_base = "https://www.ulta.com"
http_prefix = "https:"


def get_filters(page_):
    results_ = []
    soup = BeautifulSoup(page_.content, 'html.parser')
    for r in soup.find_all('div', class_="selection-box-cont pdTB20-30"):
        for li in r.find_all("li", class_=None):
            x = li.find("input")
            for f_type in filter_type:
                if x["id"].startswith(f_type):
                    results_.append((f_type, x["id"][len(f_type)+1:], x["value"]))
    return results_


def get_categories(page_):
    results_ = []
    category_ = "None"
    soup = BeautifulSoup(page_.content, 'html.parser')
    skin_care = [r for r in soup.find_all("a", class_="nav-menu-style-black") if r.get_text() == "SKIN CARE"]
    for r in skin_care[0].parent.find('div', class_="menu-adj").find_all("li"):
        if r.has_key("class"):
            category_ = r.get_text().strip().encode('utf-8')
        else:
            results_.append((category_, r.get_text().strip().encode('utf-8'), r.find("a")["href"]))
    return results_


def process_page(page_, category_, product_type_):
    results_ = []
    soup = BeautifulSoup(page_.content, 'html.parser')
    for r in soup.find_all('div', class_="productQvContainer"):
        d = {"category": category_, "product_type": product_type_}
        for tag in tags:
            d[tag] = r.find(class_=tag).get_text().strip().encode('utf-8')
        d["url"] = (r.find(class_="circleBase1").find("a")["href"])
        d["image"] = r.find(class_="quick-view-prod").find("a").find("img")["src"]
        x = r.find("span", class_="regPrice") or r.find("span", class_="pro-new-price")
        if x is not None:
            d["price"] = x.get_text().encode('utf-8')
        else:
            d["price"] = None
        results_.append(d)
    next_page_ = None
    next_array = [r["href"] for r in soup.find(class_="next-prev").find_all("a") if r.get_text() == "Next"]
    if next_array:
        next_page_ = next_array[0]

    return results_, next_page_


def process_product_page(page_, prod_id):
    product_page_tags_id = ["itemNumber", "itemSize", "itemSizeUOM"]
    product_page_tags_class = ["product-catalog-content current-longDescription", "product-catalog-content current-ingredients"]
    soup = BeautifulSoup(page_.content, 'html.parser')
    d = {PROD_KEY: prod_id}

    r = soup.find('div', class_="product-detail-reviewSummary")
    if r is not None:
        x = r.find("label")
        if x is not None:
            d["rating"] = x.get_text().strip().encode('utf-8')
        else:
            d["rating"] = None
    r = soup.find('div', class_="product-detail-content")
    if r is not None:
        for tag in product_page_tags_id:
            x = r.find("span", id=tag)
            if x is not None:
                d[tag] = x.get_text().strip().encode('utf-8')
            else:
                d[tag] = None
    for tag in product_page_tags_class:
        x = soup.find(class_=tag)
        if x is None:
            d[tag] = None
        else:
            d[tag] = x.get_text().strip().encode("utf-8")
    return d


def scrape(name, with_filters=True):
    print("Scraping listing pages")
    page = requests.get(url_base)
    categories_with_links = get_categories(page)

    results = []
    for category, product_type, next_page in categories_with_links:
        page = requests.get(http_prefix + next_page)
        page_results, next_page = process_page(page, category, product_type)
        results += page_results
        i = 0
        while next_page is not None:
            page = requests.get(url_base + next_page)
            page_results, next_page = process_page(page, category, product_type)
            results += page_results
            i += 1
            print("Processed {} pages in {} / {}".format(i, category, product_type))

    df = pd.DataFrame(results)
    print(len(df))
    df.to_csv("{}.csv".format(name))

    if with_filters:
        for category, product_type, next_page in categories_with_links:
            page = requests.get(http_prefix + next_page)
            filters = get_filters(page)
            print()
            print(filters)

            for f_type, condition, url in filters:

                field = "{}:{}".format(f_type, condition)
                results = []

                page = requests.get(url_base + url)
                print("Processing {} / {}, {} at {}".format(category, product_type, field, url_base + url))

                page_results, next_page = process_page(page, category, product_type)
                results += page_results

                i = 0
                while next_page is not None:
                    page = requests.get(url_base + next_page)
                    page_results, next_page = process_page(page, category, product_type)
                    results += page_results
                i += 1
                print("Processed {} pages in {} / {} with {}".format(i, category, product_type, field))

                df = pd.DataFrame(results)
                df[field] = True
                print("Found a total of : {} products with {} unique numbers".format(len(df), len(df[PROD_KEY].unique())))
                df.to_csv("{}_{}-{}_{}-{}.csv".format(name, category, product_type, f_type, condition))


def join_frames(name, name_filtered):
    df = pd.read_csv("{}.csv".format(name))
    print("Read in a total of : {} products with {} unique numbers".format(len(df), len(df[PROD_KEY].unique())))
    gen_names = df.columns.values
    for filename in glob.glob("{}_*.csv".format(name_filtered)):
        df_filtered = pd.read_csv(filename)
        filter_name = [name for name in df_filtered.columns.values if name not in gen_names][0]
        filtered_ids = df_filtered[PROD_KEY].tolist()
        if filter_name not in df.columns.values:
            df.loc[:, filter_name] = False
        for idx, row in df.iterrows():
            if row[PROD_KEY] in filtered_ids:
                df.set_value(idx, filter_name, True)

    df.fillna(False)
    df.to_csv("ulta_filtered.csv")


def scrape_product_pages(name):
    print("Scraping product pages")
    df = pd.read_csv("{}.csv".format(name))
    results = []
    i = 0
    for idx, row in df.iterrows():
        page = requests.get(url_base + row["url"])
        d = process_product_page(page, row[PROD_KEY])
        results.append(d)
        i += 1
        if i % 200 == 0:
            print("Processed {} products".format(i))

    df_products = pd.DataFrame(results)
    df_products.to_csv("{}_products.csv".format(name))


def scrape_images(name):
    image_base = "images/"
    small_image_base = "small_images/"
    print("Scraping images")
    df = pd.read_csv("{}.csv".format(name))
    i = 0
    for idx, row in df.iterrows():
        process_single_image(row["image"], small_image_base + row[PROD_KEY] + ".jpg")
        process_single_image(row["image"].replace("$md$", ""), image_base + row[PROD_KEY] + ".jpg")
        i += 1
        if i % 200 == 0:
            print("Processed {} images".format(i))


#print("Scaping overall")
#scrape("ulta", with_filters=False)
#print("Joining with filtered")
#join_frames("ulta", "ulta_per_filter/ulta")
#print("Scraping products")
#scrape_product_pages("ulta")
print("Scraping images")
scrape_images("ulta")
