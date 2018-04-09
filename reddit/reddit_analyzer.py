import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import io
import argparse

# ['id' 'created' 'title' 'text' 'subredit' 'tags' 'type' 'parent_id']


def get_submissions_stats(df_sub, unique_tags):
    print("Number of submissions: by tag")
    sizes = []
    for tag in unique_tags:
        sizes.append((tag[5:], df_sub[tag].sum()))

    for k, v in sorted(sizes, key=lambda x: x[1], reverse=True):
        print('|{}|{}|'.format(k, v))



def get_general_stats(df):
    print(df.columns.values)

    print("Unique tags:")

    unique_tags = list(set(["TAG__{}".format(tag) for tag_list in df['tags'].unique() for tag in str(tag_list).split("|")]))
    print(len(unique_tags))

    print("Number of submissions: ")
    print(len(df[df['type'] == 'submission']))
    print("Number of comments: ")
    print(len(df[df['type'] == 'comment']))

    for tag in unique_tags:
        df[tag] = 0

    for indx, row in df.iterrows():
        local_tags = str(row['tags']).split("|")
        for tag in unique_tags:
            if tag[5:] in local_tags:
                df.set_value(indx, tag, 1)

        df.set_value(indx, 'num_title_words', len(re.split(r'\s+', str(row["title"]))))
        df.set_value(indx, 'num_text_sents', len(re.split(r'[.?!]+', str(row["text"]))))

    df_sub = df[df['type'] == 'submission']

    df_skin = df_sub[df_sub['TAG__skin_concerns'] == 1]

    print("Number of words in the title")
    print(df_skin["num_title_words"].mean(), df_skin["num_title_words"].std(), df_skin["num_title_words"].max(), df_skin["num_title_words"].min())

    print("Number of sents in the test")
    print(df_skin["num_text_sents"].mean(), df_skin["num_text_sents"].std(),  df_skin["num_text_sents"].max(),  df_skin["num_text_sents"].min())

    # print("Number of words in the title")
    # df_skin.hist(column="num_title_words")
    # plt.show()

    df_skin[(df_skin["num_title_words"] < 20) & (df_skin["num_title_words"] > 2)]["title"].to_csv("short_sents.csv")


def create_corpus_to_annotate(df, base_name="sample", sents_per_page=20, sents_to_annotate=200, col_name="title"):
    fout = None
    df_extract = df.sample(n=sents_to_annotate)[col_name]

    file_ind = 0
    for ind, val in enumerate(df_extract):
        if ind % sents_per_page == 0:
            if fout:
                fout.close()
            fout = io.open('{}_{}.ann'.format(base_name, file_ind), 'w', encoding='utf-8')
            fout.close()
            fout = io.open('{}_{}.txt'.format(base_name, file_ind), 'w', encoding='utf-8')
            file_ind += 1
            print("new page")
        fout.write(u"INTENT {}\n".format(unicode(val, 'utf-8')))


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-f", "--filename", required=True, help="Path")
    arg_parser.add_argument("-o", "--outpath", required=True, help="Path to output base")
    args = arg_parser.parse_args()

    df = pd.read_csv(args.filename)
    create_corpus_to_annotate(df, args.outpath)


if __name__ == "__main__":
    main()
