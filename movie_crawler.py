import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers

# 根据关键词搜索电影对应的url列表
def movie_searcher(search_text):
    url = f"https://search.douban.com/movie/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

# 根据id生成电影的url
def generate_movie_url(id):
    return f"https://movie.douban.com/subject/{id}/"

# 获取电影的爬虫数据 (包括电影基本信息和评论信息)
def get_movie_data(id):
    data = get_movie_info(id)
    data["comment_list"] = get_movie_comments(id, 100)
    return data

# 获取电影的基本信息
def get_movie_info(id):
    base_url = generate_movie_url(id)
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

# 获取电影的评论信息
def get_movie_comments(id, count):
    urls = []
    i = 0
    base_url = generate_movie_url(id)
    while (i < count):
        urls.append(base_url + "comments?start={0}&limit=20&status=P&sort=new_score".format(i))
        i += 20
    comments = []
    comment_count = 0
    for url in urls:
        resp = requests.get(url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        comment_items = bs.find_all("div", {"class": "comment-item"})
        for comment_item in comment_items:
            comment_id = comment_item["data-cid"]
            comment_time_str = comment_item.find('span', {"class": "comment-time"}).get_text(strip=True)
            comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
            comment_timestamp = int(time.mktime(comment_time))
            comment_content = comment_item.find('span', {"class": "short"}).get_text(strip=True)
            comment_username = ((comment_item.find('div', {"class": "avatar"})).find("a"))["title"]
            try:
                star_class = comment_item.find('span', {"class": lambda x: x and x.startswith('allstar')})['class'][0]
                comment_rating = int(star_class[-2])
            except:
                comment_rating = None
            comment_isuseful = comment_item.find("span", {"class": "votes vote-count"}).get_text()
            match = re.search(r'allstar(\d{2})', str(comment_item.find("span", {"class": "comment-info"})))
            comment_rating = int((match.group(1))) // 10 if match else 0
            comments.append({
                "comment_id": comment_id,
                "comment_username": comment_username,
                "comment_timestamp": comment_timestamp,
                "comment_rating": comment_rating,
                "comment_content": comment_content,
                "comment_isuseful": comment_isuseful
            })
            comment_count += 1
            if comment_count >= count:
                break
    return comments