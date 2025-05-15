import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
from emotion_classification import classify_text

def book_searcher(search_text):
    url = f"https://search.douban.com/book/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://book.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def generate_book_url(id):
    return f"https://book.douban.com/subject/{id}/"

def get_book_data(id):
    data = get_book_info(id)
    data["comment_list"] = get_book_comments(id, 100)
    return data

def get_book_info(id):
    base_url = generate_book_url(id)
    resp = requests.get(base_url, headers=headers)
    bs = BeautifulSoup(resp.text, 'html.parser')
    book_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
    book_info_json = json.loads(book_info_json_str)
    book_url = book_info_json["url"]
    book_id = book_url.split("/")[-2]
    book_name = book_info_json["name"]
    book_infos = bs.find("div", {"id" : "info"})
    author_span = book_infos.find('span', {"class": "pl"}, string=' 作者')
    book_author = author_span.parent.get_text(strip=True).replace('作者:', '').strip()
    book_publisher = book_infos.find('span', {"class": "pl"}, string='出版社:').find_next_sibling('a').get_text().strip()
    book_price = book_infos.find('span', {"class": "pl"}, string='定价:').next_sibling.get_text().strip()
    book_date = book_infos.find('span', {"class": "pl"}, string='出版年:').next_sibling.get_text().strip()
    book_isbn = book_infos.find('span', {"class": "pl"}, string='ISBN:').next_sibling.get_text().strip()
    book_rating =  bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()
    book_info = {
        "book_id": book_id,
        "book_name": book_name,
        "book_author": book_author,
        "book_isbn": book_isbn,
        "book_publisher": book_publisher,
        "book_price": book_price,
        "book_date": book_date,
        "book_rating": book_rating
    }
    return book_info

def get_book_comments(id, count):
    urls = []
    i = 0
    base_url = generate_book_url(id)
    while (i < count):
        urls.append(base_url + "comments/" + "?start={0}&limit=20&status=P&sort=hotest".format(i))
        i += 20
    comments = []
    comment_count = 0
    for url in urls:
        resp = requests.get(url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        comment_items = bs.find_all("li", {"class": "comment-item"})
        for comment_item in comment_items:
            comment_id = comment_item["data-cid"]
            avatar = comment_item.find("div", {"class": "avatar"})
            comment_username = avatar.find("a")["title"]
            comment = comment_item.find("div", {"class": "comment"})
            comment_isuseful = int(comment.find("span", {"class": "vote-count"}).get_text())
            comment_time_str = comment.find("a", {"class": "comment-time"}).get_text()
            comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
            comment_timestamp = int(time.mktime(comment_time))
            comment_content = comment.find("p", {"class": "comment-content"}).get_text().strip()
            match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
            comment_rating = int((match.group(1))) // 10 if match else 0
            comment_ispositive = classify_text(comment_content)
            comments.append({
                "comment_id": comment_id,
                "comment_username": comment_username,
                "comment_timestamp": comment_timestamp,
                "comment_rating": comment_rating,
                "comment_content": comment_content,
                "comment_isuseful": comment_isuseful,
                "comment_ispositive": comment_ispositive
            })
            comment_count += 1
            if comment_count >= count:
                break
    return comments
