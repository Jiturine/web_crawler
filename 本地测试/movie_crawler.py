import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
from emotion_classification import classify_text, classify
from sanic import Sanic, request
from sanic.response import json as json_response
from sanic.exceptions import Unauthorized
import pymysql
from db_config import DB_CONFIG
import httpx
import csv
import os
from datetime import datetime
from auth import verify_token

app = Sanic("MovieCrawler")

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

@app.route("/v1/movie/search", methods=["POST"])
async def search_movies(request):
    data = request.json
    search_text = data.get('search_text')
    
    if not search_text:
        return json_response({"error": "搜索关键词不能为空"}, status=400)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://movie.douban.com/j/subject_suggest?q={search_text}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            )
            results = response.json()
            
            # 处理搜索结果
            processed_results = []
            for item in results:
                if 'title' in item and 'id' in item:
                    processed_results.append({
                        'id': item['id'],
                        'name': item['title'],
                        'image': item.get('img', ''),
                        'director': item.get('directors', ['未知'])[0] if 'directors' in item else '未知',
                        'type': item.get('type', '未知'),
                        'release_date': item.get('year', '未知')
                    })
            
            return json_response({"results": processed_results})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/movie/crawl", methods=["POST"])
async def crawl_movie(request):
    # 验证用户身份
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Unauthorized('未授权访问')
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    if not user_id:
        raise Unauthorized('无效的token')

    data = request.json
    movie_id = data.get('id')
    
    if not movie_id:
        return json_response({"error": "电影ID不能为空"}, status=400)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://movie.douban.com/subject/{movie_id}/",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取电影信息
            title = soup.find('h1').find('span').text.strip()
            rating = soup.find('strong', class_='ll rating_num').text.strip()
            info = soup.find('div', id='info').text.strip()
            
            # 解析导演、类型、上映日期等信息
            director = '未知'
            movie_type = '未知'
            release_date = '未知'
            
            for line in info.split('\n'):
                if '导演' in line:
                    director = line.split(':')[1].strip()
                elif '类型' in line:
                    movie_type = line.split(':')[1].strip()
                elif '上映日期' in line:
                    release_date = line.split(':')[1].strip()
            
            # 保存到数据库
            conn = get_db_connection()
            try:
                with conn.cursor() as cursor:
                    # 检查电影是否已存在
                    sql = "SELECT id FROM movies WHERE id = %s"
                    cursor.execute(sql, (movie_id,))
                    if not cursor.fetchone():
                        # 插入电影数据
                        sql = """
                            INSERT INTO movies (id, name, director, type, release_date, rating, info)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(sql, (movie_id, title, director, movie_type, release_date, rating, info))
                    
                    # 关联用户数据
                    sql = """
                        INSERT INTO user_data (user_id, data_id, data_type)
                        VALUES (%s, %s, 'movie')
                        ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
                    """
                    cursor.execute(sql, (user_id, movie_id))
                conn.commit()
            finally:
                conn.close()
            
            return json_response({"movie_id": movie_id})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/movie/data/<movie_id>", methods=["GET"])
async def get_movie_data(request, movie_id):
    # 验证用户身份
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Unauthorized('未授权访问')
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    if not user_id:
        raise Unauthorized('无效的token')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查用户是否有权限访问该数据
            sql = """
                SELECT m.* FROM movies m
                INNER JOIN user_data ud ON m.id = ud.data_id AND ud.data_type = 'movie'
                WHERE m.id = %s AND ud.user_id = %s
            """
            cursor.execute(sql, (movie_id, user_id))
            movie = cursor.fetchone()
            
            if not movie:
                return json_response({"error": "未找到电影数据或无权访问"}, status=404)
            
            return json_response(movie)
    finally:
        conn.close()

@app.route("/v1/movie/csv/<movie_id>", methods=["GET"])
async def get_movie_csv(request, movie_id):
    # 验证用户身份
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Unauthorized('未授权访问')
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    if not user_id:
        raise Unauthorized('无效的token')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查用户是否有权限访问该数据
            sql = """
                SELECT m.* FROM movies m
                INNER JOIN user_data ud ON m.id = ud.data_id AND ud.data_type = 'movie'
                WHERE m.id = %s AND ud.user_id = %s
            """
            cursor.execute(sql, (movie_id, user_id))
            movie = cursor.fetchone()
            
            if not movie:
                return json_response({"error": "未找到电影数据或无权访问"}, status=404)
            
            # 创建CSV文件
            csv_filename = f"movie_{movie_id}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['字段', '值'])
                for key, value in movie.items():
                    writer.writerow([key, value])
            
            # 读取CSV文件内容
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                csv_content = csvfile.read()
            
            # 删除临时文件
            os.remove(csv_filename)
            
            return json_response({"csv": csv_content})
    finally:
        conn.close()

def movie_searcher(search_text):
    '''根据关键词搜索电影并返回url列表'''
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
    '''获取电影数据（包括电影信息和评论信息）'''
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
            movie_name = "未知电影"
        
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
            movie_rating = "未知评分"

        # 获取电影图片URL
        try:
            img = bs.find("div", {"id": "mainpic"}).find("a").find("img")
            if img and img.get('src'):
                movie_image = img['src']
            else:
                movie_image = "/movie_image/no_movie_image.png"
        except (AttributeError, KeyError):
            movie_image = "/movie_image/no_movie_image.png"
        
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
        # 返回一个默认值的默认电影信息
        return {
            "movie_id": id,
            "movie_name": "未知电影",
            "movie_director": "未知导演",
            "movie_scriptwriter": "未知编剧",
            "movie_star": "未知主演",
            "movie_type": "未知类型",
            "movie_date": "未知上映日期",
            "movie_rating": "未知评分",
            "movie_IMDb": "未知IMDb",
            "movie_image": "/movie_image/no_movie_image.png"
        }

def get_movie_comments(id, count):
    '''获取电影评论信息'''
    try:
        urls = []
        i = 0
        base_url = generate_movie_url(id)
        while (i < count):
            urls.append(base_url + "comments?start={0}&limit=20&status=P&sort=new_score".format(i))
            i += 20
        comments = []
        comment_count = 0
        comment_texts = {}
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
                        comment_content = "获取评论内容失败"
                        
                    try:
                        avatar = comment_item.find('div', {"class": "avatar"})
                        comment_username = avatar.find("a")["title"]
                    except (AttributeError, KeyError):
                        comment_username = "未知用户"
                        
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
                        comment_texts[comment_id] = comment_content
                    except Exception:
                        pass
                    comments.append({
                        "comment_id": comment_id,
                        "comment_username": comment_username,
                        "comment_timestamp": comment_timestamp,
                        "comment_rating": comment_rating,
                        "comment_content": comment_content,
                        "comment_isuseful": comment_isuseful,
                        "comment_ispositive": 1
                    })
                    comment_count += 1
                    if comment_count >= count:
                        break
            except Exception as e:
                print(f"获取评论页面时出错: {e}")
                continue
                
        classify_results = classify(comment_texts)
        for result in classify_results:
            for comment in comments:
                if result['comment_id'] == comment['comment_id']:
                    comment['comment_ispositive'] = result['is_positive']
        
        return comments
    except Exception as e:
        print(f"获取评论列表时出错: {e}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
