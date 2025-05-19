import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
from emotion_classification import classify_text, classify
from sanic import Sanic
from sanic.response import json as json_response
from sanic.exceptions import Unauthorized
import pymysql
from db_config import DB_CONFIG
import httpx
import csv
import os
from datetime import datetime
from auth import verify_token

app = Sanic("BookCrawler")

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=DB_CONFIG['host'],
        port=int(DB_CONFIG['port']),
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/v1/book/search", methods=["POST"])
async def search_books(request):
    data = request.json
    search_text = data.get('search_text')
    
    if not search_text:
        return json_response({"error": "搜索关键词不能为空"}, status=400)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://book.douban.com/j/subject_suggest?q={search_text}",
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
                        'author': item.get('author', ['未知'])[0] if 'author' in item else '未知',
                        'publisher': item.get('publisher', '未知'),
                        'publish_date': item.get('year', '未知')
                    })
            
            return json_response({"results": processed_results})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/crawl", methods=["POST"])
async def crawl_book(request):
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Unauthorized('未授权访问')
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            raise Unauthorized('无效的token')
        
        # 确保user_id是整数类型
        user_id = int(user_id)

        data = request.json
        book_id = data.get('id')
        
        if not book_id:
            return json_response({"error": "图书ID不能为空"}, status=400)
            
        print(f"正在获取ID为 {book_id} 的书本数据到用户ID {user_id}...")

        # 获取完整的图书数据
        book_data = get_book_data(book_id)
        
        # 保存到数据库
        conn = None
        try:
            conn = get_db_connection()
            
            with conn.cursor() as cursor:
                # 检查图书是否已存在
                sql = "SELECT book_id FROM books WHERE book_id = %s"
                cursor.execute(sql, (str(book_id),))
                existing_book = cursor.fetchone()
                
                if not existing_book:
                    # 插入图书数据
                    sql = """
                        INSERT INTO books (
                            book_id, book_name, book_author, book_publisher, 
                            book_date, book_rating, book_image
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        str(book_id),
                        book_data["book_name"],
                        book_data["book_author"],
                        book_data["book_publisher"],
                        book_data["book_date"],
                        book_data["book_rating"],
                        book_data["book_image"]
                    ))
                    
                    # 保存评论数据
                    if "comment_list" in book_data and book_data["comment_list"]:
                        sql = """
                            INSERT INTO book_comments (
                                comment_id, book_id, comment_username, comment_timestamp,
                                comment_rating, comment_content, comment_isuseful, is_positive
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        for comment in book_data["comment_list"]:
                            cursor.execute(sql, (
                                comment["comment_id"],
                                str(book_id),
                                comment["comment_username"],
                                comment["comment_timestamp"],
                                comment["comment_rating"],
                                comment["comment_content"],
                                comment["comment_isuseful"],
                                comment["comment_ispositive"]
                            ))
                
                # 关联用户数据
                # 先删除可能存在的记录
                delete_sql = """
                    DELETE FROM user_data 
                    WHERE user_id = %s AND data_id = %s AND data_type = 'book'
                """
                cursor.execute(delete_sql, (user_id, str(book_id)))
                
                # 插入新记录
                insert_sql = """
                    INSERT INTO user_data (user_id, data_id, data_type, created_at)
                    VALUES (%s, %s, 'book', CURRENT_TIMESTAMP)
                """
                cursor.execute(insert_sql, (user_id, str(book_id)))
                print(f"成功处理用户 {user_id} 与书籍 {book_id} 的关联")
                
            # 所有操作都成功，提交事务
            conn.commit()
            print(f"成功保存图书 {book_id} 的数据")
            
        except Exception as e:
            if conn:
                conn.rollback()
                print(f"保存图书数据时出错，已回滚事务: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
        
        return json_response({"book_id": book_id})
    except Exception as e:
        print(f"爬取图书数据时出错: {str(e)}")
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/data/<book_id>", methods=["GET"])
async def get_book_data(request, book_id):
    try:
        # 验证用户身份
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Unauthorized('未授权访问')
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            raise Unauthorized('无效的token')
            
        # 确保user_id是整数类型
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise Unauthorized('无效的用户ID')

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 检查用户是否有权限访问该数据
                sql = """
                    SELECT b.* FROM books b
                    INNER JOIN user_data ud ON b.book_id = ud.data_id AND ud.data_type = 'book'
                    WHERE b.book_id = %s AND ud.user_id = %s
                """
                cursor.execute(sql, (str(book_id), user_id))
                book = cursor.fetchone()
                
                if not book:
                    return json_response({"error": "未找到图书数据或无权访问"}, status=404)
                
                return json_response(book)
        finally:
            conn.close()
    except Exception as e:
        print(f"获取图书数据时出错: {str(e)}")
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/csv/<book_id>", methods=["GET"])
async def get_book_csv(request, book_id):
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
                SELECT b.* FROM books b
                INNER JOIN user_data ud ON b.book_id = ud.data_id AND ud.data_type = 'book'
                WHERE b.book_id = %s AND ud.user_id = %s
            """
            cursor.execute(sql, (book_id, user_id))
            book = cursor.fetchone()
            
            if not book:
                return json_response({"error": "未找到图书数据或无权访问"}, status=404)
            
            # 创建CSV文件
            csv_filename = f"book_{book_id}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['字段', '值'])
                for key, value in book.items():
                    writer.writerow([key, value])
            
            # 读取CSV文件内容
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                csv_content = csvfile.read()
            
            # 删除临时文件
            os.remove(csv_filename)
            
            return json_response({"csv": csv_content})
    finally:
        conn.close()

def book_searcher(search_text):
    '''根据关键词搜索图书并返回url列表'''
    url = f"https://search.douban.com/book/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://book.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def generate_book_url(id):
    '''根据id生成图书的url'''
    return f"https://book.douban.com/subject/{id}/"

def get_book_data(id):
    '''获取图书数据并返回（包括图书信息和评论信息）'''
    data = get_book_info(id)
    data["comment_list"] = get_book_comments(id, 100)
    return data

def get_book_info(id):
    '''获取图书的基本信息'''
    try:
        base_url = generate_book_url(id)
        resp = requests.get(base_url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        
        # 获取基本信息
        book_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
        book_info_json = json.loads(book_info_json_str)
        book_url = book_info_json["url"]
        book_id = book_url.split("/")[-2]
        book_name = book_info_json["name"]
        
        # 获取图书信息
        book_infos = bs.find("div", {"id" : "info"})
        
        # 解析作者、出版社、出版日期等信息
        author_span = book_infos.find('span', {"class": "pl"}, string=' 作者:')
        if author_span and author_span.parent:
            book_author = author_span.parent.get_text(strip=True).replace('作者:', '').strip()
        else:
            author_link = book_infos.find('a', {"class": "author"})
            if author_link:
                book_author = author_link.get_text().strip()
            else:
                if 'author' in book_info_json:
                    author_data = book_info_json['author']
                    if isinstance(author_data, list):
                        book_author = author_data[0].get('name', '未知作者') if isinstance(author_data[0], dict) else author_data[0]
                    elif isinstance(author_data, dict):
                        book_author = author_data.get('name', '未知作者')
                    else:
                        book_author = str(author_data)
                else:
                    book_author = "未知作者"
            
        # 解析出版社信息
        try:
            book_publisher = book_infos.find('span', {"class": "pl"}, string='出版社:').find_next_sibling('a').get_text().strip()
        except (AttributeError, TypeError):
            book_publisher = "未知出版社"
            
        # 解析价格信息
        try:
            book_price = book_infos.find('span', {"class": "pl"}, string='定价:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_price = "未知价格"
            
        # 解析出版日期信息
        try:
            book_date = book_infos.find('span', {"class": "pl"}, string='出版年:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_date = "未知出版年"
            
        # 解析ISBN信息
        try:
            book_isbn = book_infos.find('span', {"class": "pl"}, string='ISBN:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_isbn = "未知ISBN"
            
        # 获取图书评分
        try:
            book_rating = bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()
        except (AttributeError, TypeError):
            book_rating = "未知评分"
        
        # 获取图书封面图片
        try:
            img = bs.find("div", {"id": "mainpic"}).find("a").find("img")
            if img and img.get('src'):
                book_image = img['src']
            else:
                book_image = "/book_image/no_book_image.png"
        except (AttributeError, KeyError):
            book_image = "/book_image/no_book_image.png"
        
        book_info = {
            "book_id": book_id,
            "book_name": book_name,
            "book_author": book_author,
            "book_isbn": book_isbn,
            "book_publisher": book_publisher,
            "book_price": book_price,
            "book_date": book_date,
            "book_rating": book_rating,
            "book_image": book_image
        }
        return book_info
    except Exception as e:
        # 返回默认的图书信息
        return {
            "book_id": id,
            "book_name": "未知书名",
            "book_author": "未知作者",
            "book_isbn": "未知ISBN",
            "book_publisher": "未知出版社",
            "book_price": "未知价格",
            "book_date": "未知出版年",
            "book_rating": "未知评分",
            "book_image": "/book_image/no_book_image.png"
        }

def get_book_comments(id, count):
    '''获取图书评论信息'''
    try:
        urls = []
        i = 0
        base_url = generate_book_url(id)
        while (i < count):
            url = base_url + "comments/" + "?start={0}&limit=20&status=P&sort=hotest".format(i)
            urls.append(url)
            i += 20
        
        comments = []
        comment_count = 0
        comment_texts = {}
        
        for url in urls:
            resp = requests.get(url, headers=headers)
            bs = BeautifulSoup(resp.text, 'html.parser')
            comment_items = bs.find_all("li", {"class": "comment-item"})
            
            for comment_item in comment_items:
                try:
                    # 获取评论ID
                    try:
                        comment_id = comment_item["data-cid"]
                    except KeyError:
                        comment_id = f"comment_{comment_count}"
                    
                    # 获取用户名
                    try:
                        avatar = comment_item.find("div", {"class": "avatar"})
                        comment_username = avatar.find("a")["title"]
                    except (AttributeError, KeyError):
                        comment_username = "未知用户"
                    
                    # 获取有用数
                    try:
                        comment = comment_item.find("div", {"class": "comment"})
                        comment_isuseful = int(comment.find("span", {"class": "vote-count"}).get_text())
                    except (AttributeError, ValueError):
                        comment_isuseful = 0
                    
                    # 获取评论时间
                    try:
                        comment_time_str = comment.find("a", {"class": "comment-time"}).get_text()
                        comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
                        comment_timestamp = int(time.mktime(comment_time))
                    except (AttributeError, ValueError):
                        comment_timestamp = int(time.time())
                    
                    # 获取评论内容
                    try:
                        comment_content = comment.find("p", {"class": "comment-content"}).get_text().strip()
                    except AttributeError:
                        comment_content = "获取评论内容失败"
                    
                    # 获取评分
                    try:
                        match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
                        comment_rating = int((match.group(1))) // 10 if match else 0
                    except (AttributeError, ValueError):
                        comment_rating = 0
                    
                    # 保存评论数据
                    comment_texts[comment_id] = comment_content
                    comment_data = {
                        "comment_id": comment_id,
                        "comment_username": comment_username,
                        "comment_timestamp": comment_timestamp,
                        "comment_rating": comment_rating,
                        "comment_content": comment_content,
                        "comment_isuseful": comment_isuseful,
                        "comment_ispositive": 1  # 默认设置为1
                    }
                    comments.append(comment_data)
                    
                    comment_count += 1
                    if comment_count >= count:
                        break
                        
                except Exception as e:
                    print(f"获取评论数据时出错: {str(e)}")
                    continue
            
            # # 情感分析
            # classify_results = classify(comment_texts)
            # for result in classify_results:
            #     for comment in comments:
            #             if result['comment_id'] == comment['comment_id']:
            #                 comment['comment_ispositive'] = result['is_positive']
                    
            if comment_count >= count:
                break
        
        return comments
        
    except Exception as e:
        print(f"获取评论数据时出错: {str(e)}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
