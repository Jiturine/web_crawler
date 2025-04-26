import json
import sys
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers


def get_movie_data(base_url):
    data = get_movie_info(base_url)
    data["comment_list"] = get_movie_comments(base_url, 100)
    return data

def get_movie_info(base_url):
    resp = requests.get(base_url, headers=headers)
    bs = BeautifulSoup(resp.text, 'html.parser')
    movie_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
    movie_info_json = json.loads(movie_info_json_str)
    movie_url = movie_info_json["url"]
    movie_id = movie_url.split("/")[-2]
    movie_name = movie_info_json["name"]

    movie_infos = bs.find("div", {"id" : "info"})
    movie_director = movie_infos.find('span', {"class": "pl"}, string='导演').parent.get_text(strip=True).replace('导演:', '').strip()
    movie_scriptwriter = movie_infos.find('span', {"class": "pl"}, string='编剧').parent.get_text(strip=True).replace('编剧:', '').strip()
    movie_star = movie_infos.find('span', {"class": "pl"}, string='主演').parent.get_text(strip=True).replace('主演:', '').strip()
    movie_types = movie_infos.find_all('span', {"property": "v:genre"})
    movie_type = ""
    for type in movie_types:
        movie_type += type.get_text().strip() + "/"
    movie_type = movie_type[:-1]
    movie_date = movie_infos.find('span', {"property": "v:initialReleaseDate"}).get_text().strip()
    movie_IMDb = movie_infos.find('span', {"class": "pl"}, string='IMDb:').next_sibling.get_text().strip()
    movie_rating =  bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()

    movie_info = {
        "movie_id": movie_id,
        "movie_name": movie_name,
        "movie_director": movie_director,
        "movie_scriptwriter": movie_scriptwriter,
        "movie_star": movie_star,
        "movie_type": movie_type,
        "movie_date": movie_date,
        "movie_rating": movie_rating,
        "movie_IMDb": movie_IMDb
    }
    return movie_info

def get_movie_comments(base_url, count):
    urls = []
    i = 0
    while (i < count):
        urls.append(base_url + "comments/" + "?start={0}&limit=20&status=P&sort=hotest".format(i))
        i += 20
    comments = []
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
            comment_location = comment.find("span", {"class": "comment-location"}).get_text()
            match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
            comment_rating = int((match.group(1))) // 10 if match else 0
            comments.append({
                "comment_id": comment_id,
                "comment_username": comment_username,
                "comment_timestamp": comment_timestamp,
                "comment_location": comment_location,
                "comment_rating": comment_rating,
                "comment_content": comment_content,
                "comment_isuseful": comment_isuseful
            })
            comment_count += 1
            if comment_count >= count:
                break
    return comments

print(get_movie_data('https://movie.douban.com/subject/35267208/'))