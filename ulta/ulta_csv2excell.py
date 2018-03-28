import xlsxwriter
from ulta_config import *
import pandas as pd
from collections import OrderedDict

sheet_names = OrderedDict([
    ("Product_Base", ["Brand", "Name", "Price", "Size", "Display Name", "Short Description", "Image Link", "Web Link", "Mobile Link", "Availability", "GTIN", "SKU", "Locale", "Country"]),
    ("Product_ActiveCosmetics", ["Brand", "Name", "Function", "Texture", "Ingredients", "Scent", "Gender", "Recommended usage"]),
    ("Product_Diagnostic_Skin_Face", ["Brand", "Name", "SkinType:DrySkin", "SkinType:NormalSkin", "SkinType:OilySkin", "SkinType:VeryOilySkin", "Sensitiveness:Reactiveness", "Sensitiveness:Redness", "Sensitiveness:Generic", "Dehydration:Dullness", "Dehydration:Roughness", "Dehydration:Tightness", "Imperfections:AcneMarks", "Imperfections:Pimples", "Imperfections:VisiblePores", "Aging:FirmnessLoss", "Aging:Sagging", "Aging:Wrinkles"]),
    ("Product_Extra", ["Brand", "Name", "Short Description"]),
    ("Product_Ontology", []),
    ("Regimen", []),
    ("ActiveCosmetics_Ontolgy", []),
    ("Diagnostic_Skin_Face_Ontology", []),
    ("Regimen_Ontology", [])])

title2key = OrderedDict([
    ("Brand", "brand"),
    ("Name", "name"),
    ("Price", "price"),
    ("Size", "unit_pricing_measure"),
    ("Display Name", "display_name"),
    ("Short Description", "short_description"),
    ("Image Link", "image"),
    ("Web Link", "url"),
    ("Mobile Link", ""),
    ("Availability", "In Stock"),
    ("GTIN", ""),
    ("SKU", "sku"),
    ("Locale", "EN"),
    ("Country", "CA"),
    ("Function", "function_"),
    ("Ingredients", "ingredients")])

ontology2filter = dict([(node, filter) for filter, ont_list in filter2ontology.items() for node in ont_list])


def get_product_item(title, row):
    corrected_row = correct_row(row)

    key = title2key.get(title, "")
    if key:
        if key in corrected_row:
            item = corrected_row[key]
        elif key in key2col:
            item = row[key2col[key]]
        else:
            item = key
    else:
        item = ""
    return item


def get_diagnostic_item(title, row):
    key = ontology2filter.get(title, "")
    if key:
        if row[key]:
            item = "Applies"
        else:
            item = "Unrelated"
    else:
        item = "Unrelated"
    return item


def create_excell(df):
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('ulta.xlsx')
    bold = workbook.add_format({'bold': True})

    for name in sheet_names:
        workbook.add_worksheet(name=name)

    for sheet_name, titles in sheet_names.items()[:3]:
        worksheet = workbook.get_worksheet_by_name(sheet_name)

        for col, title in enumerate(titles):
            worksheet.write(0, col, title, bold)

        for row_num, row in df[:N].iterrows():
            for col, title in enumerate(titles):
                if ':' in title:
                    item = get_diagnostic_item(title, row)
                else:
                    item = get_product_item(title, row)
                worksheet.write(row_num + 1, col, item)

    workbook.close()


df = pd.read_csv("ulta_merged.csv", encoding='utf-8').fillna('')
N = 1000
create_excell(df)

