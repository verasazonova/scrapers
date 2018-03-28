import pandas as pd
import json
from ulta_config import *


def process_single_row(row):
    if not row[key2col["name"]] or not row[key2col["sku"]]:
        return []

    corrected_row = correct_row(row)
    unit_pricing_measure = corrected_row["unit_pricing_measure"]
    display_name = corrected_row["display_name"]
    short_description = corrected_row["short_description"]
    url = corrected_row["url"]
    ingredients = corrected_row["ingredients"].split(", ")
    function_ = corrected_row["function_"]
    sku = corrected_row["sku"]
    price = corrected_row["price"]

    d0 = {
        "unitPricingMeasure": unit_pricing_measure,
        "sku": sku,
        "localized": [
          {
            "country": "CA",
            "locale": "EN",
            "displayName": display_name,
            "shortDescription": short_description,
            "description": short_description,
            "explanation": short_description,
            "availability": "In Stock",
            "imageLink": image_base + row[PROD_KEY] + ".jpg",
            "additionalImageLinks": [],
            "link": url,
            "purchaseLink": url,
            "price": {
              "value": price,
              "currency": "CAD"
            }
          }
        ]
      }

    d0 = {key: value for key, value in d0.items() if value}

    d1 = {
    "type": "ProductLine",
    "brand": row[key2col["brand"]],
    "name": row[key2col["name"]],
#    "parentCompany": "",
#    "productRange": "",
    "instances": [
      d0
    ]}



    d2 = {
        "type": "ActiveCosmetic",
        "brand": row[key2col["brand"]],
        "name": row[key2col["name"]],
        "ingredients": ingredients,
        "function": function_,
#        "texture": ""
    }

    d3 = {
        "type": "DiagnosticSkinFace",
        "brand": row[key2col["brand"]],
        "name": row[key2col["name"]],
    }

    d1 = {key: value for key, value in d1.items() if value}
    d2 = {key: value for key, value in d2.items() if value}

    for key, value in row.iteritems():
        if value and key in filter2ontology:
            for node in filter2ontology[key]:
                d3.update({node: "Applies"})

    return [d1, d2, d3]


def create_product_recommendation_json(name):
    df = pd.read_csv("{}_filtered.csv".format(name)).drop(columns=['Unnamed: 0'])
    print(df.columns.values)
    df_product = pd.read_csv("{}_products.csv".format(name)).drop(columns=['Unnamed: 0']).drop_duplicates()
    print(df_product.columns.values)
    print("Read in a total of : {} products with {} unique numbers".format(len(df), len(df[PROD_KEY].unique())))
    print("Read in a total of : {} products with {} unique numbers".format(len(df_product), len(df_product[PROD_KEY].unique())))
    df = pd.merge(df, df_product, left_on='prod-id', right_on='prod-id', how='outer').fillna('')

    for idx, row in df.iterrows():
        if row['category'] == 'Moisturizers':
            row['category'] = 'moisturizer'
        elif row['category'] == 'Cleansers':
            row['category'] = 'cleanser'
        else:
            row['category'] = 'skincare'

    df = df.drop_duplicates([PROD_KEY, "prod-title", "prod-desc"])
    df.to_csv("ulta_merged.csv")
    print("Merged into a total of : {} products with {} unique numbers".format(len(df), len(df[PROD_KEY].unique())))
    result = []
    for idx, row in df.iterrows():
        jsons = process_single_row(row)
        result += jsons

    with open("{}.json".format(name), 'w') as f:
        f.write("{}".format(json.dumps(result, indent=2)))
    print("done with {} products".format(len(result)/3))


create_product_recommendation_json("ulta")