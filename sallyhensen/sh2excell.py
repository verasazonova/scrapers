import xlsxwriter
import pandas as pd
import numpy as np

titles = {'': 'Color', 'merged_hex':'HEX', 'Shade Name': 'Name', 'Product name': 'Product Line', 'EAN': 'EAN', 'slug': 'URL', 'number':'number'}
N = 10


def create_excell(df):
    # Create a workbook and add a worksheet.
    workbook = xlsxwriter.Workbook('sh.xlsx')
    bold = workbook.add_format({'bold': True})

    worksheet = workbook.add_worksheet(name='Shades')

    for col, title in enumerate(titles.values()):
        worksheet.write(0, col, title, bold)

    for row_num, row in df.iterrows():
        print(row['EAN'], row_num, row['merged_hex'])
        for col, colname in enumerate(titles.keys()):
            if colname == '':
                if row['merged_hex'] != '':
                    format_dict = {'bg_color': '#{}'.format(row['merged_hex'])}
                    worksheet.write(row_num + 1, col, '', workbook.add_format(format_dict))
            else:
                format_dict = {'text_wrap': True}
                if colname == 'slug':
                    worksheet.write_url(row_num + 1, col, row[colname])
                else:
                    worksheet.write_string(row_num + 1, col, row[colname], workbook.add_format(format_dict))

    worksheet.set_column('A:H', 30)
    workbook.close()


df = pd.read_csv("SH_spring_full.csv", encoding='utf-8', dtype=str).dropna(subset=['EAN']).reset_index(drop=True).fillna('')
df['merged_hex'] = df['SH_HEX'].str.lower().str.replace('\s+', '')
print(df[df['Shade Name'] == 'Heavy Metal']['merged_hex'])
df.loc[(df['SH_HEX'] == '') | ((df['SH_HEX'] == 'ffffff') & (df['SH_HEX'] != df['hex'])), 'merged_hex'] = df['hex']
print(df[df['Shade Name'] == 'Heavy Metal']['merged_hex'])
df['number'] = df['name'].str.split('-', expand=True, n=1)[0]


# sh_hex = df['SH_HEX']
# hex = df['hex'].str.values
# inds = np.where(sh_hex == 'n/a' | ((sh_hex == '#ffffff') & (sh_hex != hex)))
# print(inds)

create_excell(df)
