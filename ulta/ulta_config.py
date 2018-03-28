import re

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


def correct_row(row):

    if row[key2col["description"]]:
        short_description = re.split(r'[.!?]', row[key2col["description"]])[0]
    else:
        short_description = ""

    if row[key2col["size"]]:
        display_name = u"{} | {} {}".format(row[key2col["name"]].strip(),
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

    warning = ".Please be aware that ingredient lists may change or vary from time to time. Please refer to the ingredient list on the product package you receive for the most up to date list of ingredients."
    ingredients = row[key2col["ingredients"]].replace(warning, "")

    if row[key2col["function"]].lower() in ["moisturizers", "cleansers"]:
        function_ = row[key2col["function"]][:-1].lower()
    else:
        function_ = "skincare"

    return {"display_name": display_name,
            "short_description": short_description,
            "price": price,
            "sku": sku,
            "ingredients": ingredients,
            "function_": function_,
            "url": url,
            "unit_pricing_measure": unit_pricing_measure}