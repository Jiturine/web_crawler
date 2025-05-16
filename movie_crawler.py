import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
from emotion_classification import classify_text

def movie_searcher(search_text):
    '''根据关键词搜索电影对应的url列表'''
    url = f"https://search.douban.com/movie/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def generate_movie_url(id):
    '''根据id生成电影的url'''
    return f"https://movie.douban.com/subject/{id}/"

def get_movie_data(id):
    '''获取电影的爬虫数据 (包括电影基本信息和评论信息)'''
    data = get_movie_info(id)
    data["comment_list"] = get_movie_comments(id, 100)
    return data

def get_movie_info(id):
    '''获取电影的基本信息'''
    try:
        base_url = generate_movie_url(id)
        resp = requests.get(base_url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        
        # 获取基本信息
        try:
            movie_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
            movie_info_json = json.loads(movie_info_json_str)
            movie_url = movie_info_json["url"]
            movie_id = movie_url.split("/")[-2]
            movie_name = movie_info_json["name"]
        except (AttributeError, KeyError, json.JSONDecodeError):
            movie_id = id
            movie_name = "未知电影名"
        
        movie_infos = bs.find("div", {"id": "info"})
        
        # 导演
        try:
            movie_director = movie_infos.find('span', {"class": "pl"}, string='导演').parent.get_text(strip=True).replace('导演:', '').strip()
        except (AttributeError, TypeError):
            movie_director = "未知导演"
            
        # 编剧
        try:
            movie_scriptwriter = movie_infos.find('span', {"class": "pl"}, string='编剧').parent.get_text(strip=True).replace('编剧:', '').strip()
        except (AttributeError, TypeError):
            movie_scriptwriter = "未知编剧"
            
        # 主演
        try:
            movie_star = movie_infos.find('span', {"class": "pl"}, string='主演').parent.get_text(strip=True).replace('主演:', '').strip()
        except (AttributeError, TypeError):
            movie_star = "未知主演"
            
        # 类型
        try:
            movie_types = movie_infos.find_all('span', {"property": "v:genre"})
            movie_type = ""
            for type in movie_types:
                movie_type += type.get_text().strip() + "/"
            movie_type = movie_type[:-1] if movie_type else "未知类型"
        except (AttributeError, TypeError):
            movie_type = "未知类型"
            
        # 上映日期
        try:
            movie_date = movie_infos.find('span', {"property": "v:initialReleaseDate"}).get_text().strip()
        except (AttributeError, TypeError):
            movie_date = "未知上映日期"
            
        # IMDb
        try:
            movie_IMDb = movie_infos.find('span', {"class": "pl"}, string='IMDb:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            movie_IMDb = "未知IMDb"
            
        # 评分
        try:
            movie_rating = bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()
        except (AttributeError, TypeError):
            movie_rating = "暂无评分"

        # 获取电影图片URL
        try:
            img = bs.find("div", {"id": "mainpic"}).find("a").find("img")
            if img and img.get('src'):
                movie_image = img['src']
            else:
                movie_image = "/static/no_movie_image.png"
        except (AttributeError, KeyError):
            movie_image = "/static/no_movie_image.png"
        
        movie_info = {
            "movie_id": movie_id,
            "movie_name": movie_name,
            "movie_director": movie_director,
            "movie_scriptwriter": movie_scriptwriter,
            "movie_star": movie_star,
            "movie_type": movie_type,
            "movie_date": movie_date,
            "movie_rating": movie_rating,
            "movie_IMDb": movie_IMDb,
            "movie_image": movie_image
        }
        return movie_info
    except Exception as e:
        print(f"获取电影信息时出错: {e}")
        # 返回一个包含默认值的基本信息
        return {
            "movie_id": id,
            "movie_name": "未知电影名",
            "movie_director": "未知导演",
            "movie_scriptwriter": "未知编剧",
            "movie_star": "未知主演",
            "movie_type": "未知类型",
            "movie_date": "未知上映日期",
            "movie_rating": "暂无评分",
            "movie_IMDb": "未知IMDb",
            "movie_image": "/movie_image/no_movie_image.png"
        }

def get_movie_comments(id, count):
    '''获取电影的评论信息'''
    try:
        urls = []
        i = 0
        base_url = generate_movie_url(id)
        while (i < count):
            urls.append(base_url + "comments?start={0}&limit=20&status=P&sort=new_score".format(i))
            i += 20
        comments = []
        comment_count = 0
        for url in urls:
            try:
                resp = requests.get(url, headers=headers)
                bs = BeautifulSoup(resp.text, 'html.parser')
                comment_items = bs.find_all("div", {"class": "comment-item"})
                for comment_item in comment_items:
                    try:
                        comment_id = comment_item["data-cid"]
                    except KeyError:
                        comment_id = f"comment_{comment_count}"
                        
                    try:
                        comment_time_str = comment_item.find('span', {"class": "comment-time"}).get_text(strip=True)
                        comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
                        comment_timestamp = int(time.mktime(comment_time))
                    except (AttributeError, ValueError):
                        comment_timestamp = int(time.time())
                        
                    try:
                        comment_content = comment_item.find('span', {"class": "short"}).get_text(strip=True)
                    except AttributeError:
                        comment_content = "评论内容获取失败"
                        
                    try:
                        avatar = comment_item.find('div', {"class": "avatar"})
                        comment_username = avatar.find("a")["title"]
                    except (AttributeError, KeyError):
                        comment_username = "匿名用户"
                        
                    try:
                        star_class = comment_item.find('span', {"class": lambda x: x and x.startswith('allstar')})['class'][0]
                        comment_rating = int(star_class[-2])
                    except (AttributeError, KeyError, ValueError):
                        try:
                            match = re.search(r'allstar(\d{2})', str(comment_item.find("span", {"class": "comment-info"})))
                            comment_rating = int((match.group(1))) // 10 if match else 0
                        except (AttributeError, ValueError):
                            comment_rating = 0
                            
                    try:
                        comment_isuseful = int(comment_item.find("span", {"class": "votes vote-count"}).get_text())
                    except (AttributeError, ValueError):
                        comment_isuseful = 0
                        
                    try:
                        comment_ispositive = classify_text(comment_content)
                    except Exception:
                        comment_ispositive = 0
                        
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
            except Exception as e:
                print(f"获取评论页面时出错: {e}")
                continue
                
        return comments
    except Exception as e:
        print(f"获取评论列表时出错: {e}")
        return []
