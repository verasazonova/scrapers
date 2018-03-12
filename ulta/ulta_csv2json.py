import pandas as pd
import re
import json

PROD_KEY = "prod-id"
tags = ["prod-title", "prod-desc", PROD_KEY]
url_base = "https://www.ulta.com"
image_base = "https://s3.amazonaws.com/vortex.bot-brain.com/research-images/ulta/"

key2col = {
    "id": PROD_KEY,
    "brand": "prod-title",
    "name": "prod-desc",
    "sku": "itemNumber",
    "size": "itemSize",
    "sizeUnit": "itemSizeUOM",
    "description": "product-catalog-content current-longDescription",
    "price": "price",
    "ingredients": "product-catalog-content current-ingredients",
    "rating": "sr-only",
    "function": "category",
    "specific_function": "prod_type",
    "image": "image",
    "url": "url"
}

filter2ontology = {
    "concerns:Acne&Blemishes": ["Imperfections:AcneMarks", "Imperfections:General"],
    "concerns:Blackheads&VisiblePores": ["Imperfections:Blackheads", "Imperfections:VisiblePores"],
    "concerns:DarkSpots&UnevenSkinTone": ["Blemish", "Aging:Pigmentation"],
    "concerns:Dryness": ["Dehydration:Discomfort", "Dehydration:General"],
    "concerns:FineLines&Wrinkles": ["Aging:Wrinkles", "Dehydration:Lines"],
    "concerns:Redness": ["Sensitiveness:Redness"],
    "concerns:Shine": ["Imperfections:Shine"],

    "concerns:Damaged": ["Dehydration:General"],
    "concerns:DarkCircles": ["Aging:General"],
    "concerns:Oiliness": ["SkinType:OilySkin","Imperfections:Shine"],

    "skintype:All": ["SkinType:CombinationSkin", "SkinType:DrySkin", "SkinType:NormalSkin", "SkinType:OilySkin", "FaceSkinCondition:Sensitiveness"],
    "skintype:Combination": ["SkinType:CombinationSkin"],
    "skintype:Dry": ["SkinType:DrySkin"],
    "skintype:Normal": ["SkinType:NormalSkin"],
    "skintype:Oily": ["SkinType:OilySkin"],
    "skintype:Sensitive": ["FaceSkinCondition:Sensitiveness"]
}


def process_single_row(row):
    if not row[key2col["name"]] or not row[key2col["sku"]]:
        return []

    if row[key2col["description"]]:
        short_description = re.split(r'[.!?]', row[key2col["description"]])[0]
    else:
        short_description = ""

    if row[key2col["size"]]:
        display_name = "{} | {} {}".format(row[key2col["name"]].strip(),
                                           row[key2col["size"]].strip(),
                                           row[key2col["sizeUnit"]].strip())
    else:
        display_name = row[key2col["name"]].strip()

    unit_pricing_measure = "{} {}".format(row[key2col["size"]], row[key2col["sizeUnit"]]).strip()

    url = url_base + row[key2col["url"]]
    if row[key2col["sku"]]:
        sku = row[key2col["sku"]].replace("Item", '').strip()
    else:
        sku = ""

    if row[key2col["price"]]:
        price = float(row[key2col["price"]].strip().replace("$", "").split("-")[0].strip())
    else:
        price = None

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

    warning = ".Please be aware that ingredient lists may change or vary from time to time. Please refer to the ingredient list on the product package you receive for the most up to date list of ingredients."
    ingredients = row[key2col["ingredients"]].replace(warning, "").split(", ")

    if row[key2col["function"]].lower() in ["moisturizers", "cleansers"]:
        function_ = row[key2col["function"]][:-1].lower()
    else:
        function_ = "skincare"

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