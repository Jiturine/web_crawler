import matplotlib.pyplot as plt
import numpy
import jieba
from wordcloud import WordCloud
from emotion_classification import classify
import time
import os

def configure():
    plt.rcParams["font.sans-serif"] = ['AR PL UMing CN']
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 14
    plt.figure(figsize=(16, 9))

def get_stop_words():
    with open(os.path.dirname(os.path.abspath(__file__))+ '/stopwords.txt', 'r', encoding='utf-8') as f:
        stopWords = f.read()
    stopWords = ['\n', '', ' '] + stopWords.split()
    return stopWords

def plot_book_comment_histogram(book_data_list):
    configure()
    book_names = []
    comments = []
    positives = []
    negatives = []
    for book_data in book_data_list:
        comment_list = book_data["comment_list"]
        book_names.append(book_data["book_name"])
        comment_num = len(comment_list)
        comment_texts = [comment["comment_content"] for comment in comment_list]
        classify_result = classify(comment_texts)
        positive_num = len([comment for comment in classify_result if comment["is_positive"] == 1])
        negative_num = len([comment for comment in classify_result if comment["is_positive"] == 0])
        comments.append(comment_num)
        positives.append(positive_num)
        negatives.append(negative_num)
    x = numpy.arange(len(book_names))
    width = 0.1
    plt.bar(x - width, comments, width, label='评论个数')
    plt.bar(x, positives, width, label='正向评论')
    plt.bar(x + width, negatives, width, label='负向评论')
    plt.xlabel('个数')
    plt.title('书籍评论详情')
    plt.xticks(x, labels=book_names)
    plt.legend()
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    save_path = os.path.join("static", f"book_comment_wordcloud_{now_time}.png")
    plt.savefig(save_path)
    return save_path

def plot_book_comment_wordcloud(book_data):
    configure()
    comment_text = ""
    for comment in book_data["comment_list"]:
        comment_text += comment["comment_content"]
    if comment == "":
        print({"code": -1, "message": "无对应ID的图书或该图书无评论信息"})
        return
    cut_text = " ".join(jieba.lcut(comment_text))
    stopWords = get_stop_words()
    cloudword = WordCloud(width=400, height=300, scale=1, margin=2, 
                            font_path='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 
                            background_color='white', max_words=200, random_state=100, 
                            stopwords=stopWords).generate(cut_text)
    plt.imshow(cloudword)
    plt.axis("off")
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    save_path = os.path.join("static", f"book_comment_wordcloud_{now_time}.png")
    plt.savefig(save_path)
    return save_path