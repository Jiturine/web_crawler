import matplotlib.pyplot as plt
import numpy
import jieba
from wordcloud import WordCloud
from emotion_classification import classify
import time
import os

# 配置matplotlib的字体和大小
def configure():
    plt.rcParams["font.sans-serif"] = ['SimHei']
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["font.size"] = 14
    plt.figure(figsize=(16, 9))

# 获取停用词列表
def get_stop_words():
    with open(os.path.dirname(os.path.abspath(__file__))+ '/stopwords.txt', 'r', encoding='utf-8') as f:
        stopWords = f.read()
    stopWords = ['\n', '', ' '] + stopWords.split()
    return stopWords

# 绘制书籍评论数量和情感分析结果的柱状图
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
    plt.bar(x - width, comments, width, label='评论总数')
    plt.bar(x, positives, width, label='正向评论')
    plt.bar(x + width, negatives, width, label='负向评论')
    plt.xlabel('数量')
    plt.title('书籍评论详情')
    plt.xticks(x, labels=book_names)
    plt.legend()
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    save_path = os.path.join("static", f"book_comment_histogram_{book_data['book_id']}.png")
    plt.savefig(save_path)
    return save_path

# 绘制书籍评论词云
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
    stopWords.append(book_data["book_name"])
    cloudword = WordCloud(width=400, height=300, scale=1, margin=2, 
                            font_path='fonts/NotoSansCJK-Regular.ttc', 
                            background_color='white', max_words=200, random_state=100, 
                            stopwords=stopWords).generate(cut_text)
    plt.imshow(cloudword)
    plt.axis("off")
    save_path = os.path.join("static", f"book_comment_wordcloud_{book_data['book_id']}.png")
    plt.savefig(save_path)
    return save_path

# 绘制电影评论数量和情感分析结果的柱状图
def plot_movie_comment_histogram(movie_data_list):
    configure()
    movie_names = []
    comments = []
    positives = []
    negatives = []
    for movie_data in movie_data_list:
        comment_list = movie_data["comment_list"]
        movie_names.append(movie_data["movie_name"])
        comment_num = len(comment_list)
        comment_texts = [comment["comment_content"] for comment in comment_list]
        classify_result = classify(comment_texts)
        positive_num = len([comment for comment in classify_result if comment["is_positive"] == 1])
        negative_num = len([comment for comment in classify_result if comment["is_positive"] == 0])
        comments.append(comment_num)
        positives.append(positive_num)
        negatives.append(negative_num)
    x = numpy.arange(len(movie_names))
    width = 0.1
    plt.bar(x - width, comments, width, label='评论总数')
    plt.bar(x, positives, width, label='正向评论')
    plt.bar(x + width, negatives, width, label='负向评论')
    plt.xlabel('数量')
    plt.title('电影评论详情')
    plt.xticks(x, labels=movie_names)
    plt.legend()
    save_path = os.path.join("static", f"movie_comment_histogram_{movie_data['movie_id']}.png")
    plt.savefig(save_path)
    return save_path

# 绘制电影评论词云
def plot_movie_comment_wordcloud(movie_data):
    configure()
    comment_text = ""
    for comment in movie_data["comment_list"]:
        comment_text += comment["comment_content"]
    if comment == "":
        print({"code": -1, "message": "无对应ID的电影或该电影无评论信息"})
        return
    cut_text = " ".join(jieba.lcut(comment_text))
    stopWords = get_stop_words()
    stopWords.append(movie_data["movie_name"])
    cloudword = WordCloud(width=400, height=300, scale=1, margin=2, 
                            font_path='fonts/NotoSansCJK-Regular.ttc', 
                            background_color='white', max_words=200, random_state=100, 
                            stopwords=stopWords).generate(cut_text)
    plt.imshow(cloudword)
    plt.axis("off")
    save_path = os.path.join("static", f"movie_comment_wordcloud_{movie_data['movie_id']}.png")
    plt.savefig(save_path)
    return save_path