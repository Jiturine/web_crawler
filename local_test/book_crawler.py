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
    """鑾峰彇鏁版嵁搴撹繛鎺�"""
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
        return json_response({"error": "鎼滅储鍏抽敭璇嶄笉鑳戒负绌�"}, status=400)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://book.douban.com/j/subject_suggest?q={search_text}",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            )
            results = response.json()
            
            # 澶勭悊鎼滅储缁撴灉
            processed_results = []
            for item in results:
                if 'title' in item and 'id' in item:
                    processed_results.append({
                        'id': item['id'],
                        'name': item['title'],
                        'image': item.get('img', ''),
                        'author': item.get('author', ['鏈煡'])[0] if 'author' in item else '鏈煡',
                        'publisher': item.get('publisher', '鏈煡'),
                        'publish_date': item.get('year', '鏈煡')
                    })
            
            return json_response({"results": processed_results})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/crawl", methods=["POST"])
async def crawl_book(request):
    try:
        # 楠岃瘉鐢ㄦ埛韬唤
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Unauthorized('鏈巿鏉冭闂�')
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            raise Unauthorized('鏃犳晥鐨則oken')
        
        # 纭繚user_id鏄暣鏁扮被鍨�
        user_id = int(user_id)

        data = request.json
        book_id = data.get('id')
        
        if not book_id:
            return json_response({"error": "鍥句功ID涓嶈兘涓虹┖"}, status=400)
            
        print(f"姝ｅ湪鑾峰彇ID涓� {book_id} 鐨勪功鏈暟鎹埌鐢ㄦ埛ID {user_id}...")

        # 鑾峰彇瀹屾暣鐨勫浘涔︽暟鎹�
        book_data = get_book_data(book_id)
        
        # 淇濆瓨鍒版暟鎹簱
        conn = None
        try:
            conn = get_db_connection()
            
            with conn.cursor() as cursor:
                # 妫€鏌ュ浘涔︽槸鍚﹀凡瀛樺湪
                sql = "SELECT book_id FROM books WHERE book_id = %s"
                cursor.execute(sql, (str(book_id),))
                existing_book = cursor.fetchone()
                
                if not existing_book:
                    # 鎻掑叆鍥句功鏁版嵁
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
                    
                    # 淇濆瓨璇勮鏁版嵁
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
                
                # 鍏宠仈鐢ㄦ埛鏁版嵁
                # 鍏堝垹闄ゅ彲鑳藉瓨鍦ㄧ殑璁板綍
                delete_sql = """
                    DELETE FROM user_data 
                    WHERE user_id = %s AND data_id = %s AND data_type = 'book'
                """
                cursor.execute(delete_sql, (user_id, str(book_id)))
                
                # 鎻掑叆鏂拌褰�
                insert_sql = """
                    INSERT INTO user_data (user_id, data_id, data_type, created_at)
                    VALUES (%s, %s, 'book', CURRENT_TIMESTAMP)
                """
                cursor.execute(insert_sql, (user_id, str(book_id)))
                print(f"鎴愬姛澶勭悊鐢ㄦ埛 {user_id} 涓庝功绫� {book_id} 鐨勫叧鑱�")
                
            # 鎵€鏈夋搷浣滈兘鎴愬姛锛屾彁浜や簨鍔�
            conn.commit()
            print(f"鎴愬姛淇濆瓨鍥句功 {book_id} 鐨勬暟鎹�")
            
        except Exception as e:
            if conn:
                conn.rollback()
                print(f"淇濆瓨鍥句功鏁版嵁鏃跺嚭閿欙紝宸插洖婊氫簨鍔�: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
        
        return json_response({"book_id": book_id})
    except Exception as e:
        print(f"鐖彇鍥句功鏁版嵁鏃跺嚭閿�: {str(e)}")
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/data/<book_id>", methods=["GET"])
async def get_book_data(request, book_id):
    try:
        # 楠岃瘉鐢ㄦ埛韬唤
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise Unauthorized('鏈巿鏉冭闂�')
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        if not user_id:
            raise Unauthorized('鏃犳晥鐨則oken')
            
        # 纭繚user_id鏄暣鏁扮被鍨�
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            raise Unauthorized('鏃犳晥鐨勭敤鎴稩D')

        conn = get_db_connection()
        try:
            with conn.cursor() as cursor:
                # 妫€鏌ョ敤鎴锋槸鍚︽湁鏉冮檺璁块棶璇ユ暟鎹�
                sql = """
                    SELECT b.* FROM books b
                    INNER JOIN user_data ud ON b.book_id = ud.data_id AND ud.data_type = 'book'
                    WHERE b.book_id = %s AND ud.user_id = %s
                """
                cursor.execute(sql, (str(book_id), user_id))
                book = cursor.fetchone()
                
                if not book:
                    return json_response({"error": "鏈壘鍒板浘涔︽暟鎹垨鏃犳潈璁块棶"}, status=404)
                
                return json_response(book)
        finally:
            conn.close()
    except Exception as e:
        print(f"鑾峰彇鍥句功鏁版嵁鏃跺嚭閿�: {str(e)}")
        return json_response({"error": str(e)}, status=500)

@app.route("/v1/book/csv/<book_id>", methods=["GET"])
async def get_book_csv(request, book_id):
    # 楠岃瘉鐢ㄦ埛韬唤
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Unauthorized('鏈巿鏉冭闂�')
    
    token = auth_header.split(' ')[1]
    user_id = verify_token(token)
    if not user_id:
        raise Unauthorized('鏃犳晥鐨則oken')

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 妫€鏌ョ敤鎴锋槸鍚︽湁鏉冮檺璁块棶璇ユ暟鎹�
            sql = """
                SELECT b.* FROM books b
                INNER JOIN user_data ud ON b.book_id = ud.data_id AND ud.data_type = 'book'
                WHERE b.book_id = %s AND ud.user_id = %s
            """
            cursor.execute(sql, (book_id, user_id))
            book = cursor.fetchone()
            
            if not book:
                return json_response({"error": "鏈壘鍒板浘涔︽暟鎹垨鏃犳潈璁块棶"}, status=404)
            
            # 鍒涘缓CSV鏂囦欢
            csv_filename = f"book_{book_id}.csv"
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['瀛楁', '鍊�'])
                for key, value in book.items():
                    writer.writerow([key, value])
            
            # 璇诲彇CSV鏂囦欢鍐呭
            with open(csv_filename, 'r', encoding='utf-8') as csvfile:
                csv_content = csvfile.read()
            
            # 鍒犻櫎涓存椂鏂囦欢
            os.remove(csv_filename)
            
            return json_response({"csv": csv_content})
    finally:
        conn.close()

def book_searcher(search_text):
    '''鏍规嵁鍏抽敭璇嶆悳绱㈠浘涔﹀苟杩斿洖url鍒楄〃'''
    url = f"https://search.douban.com/book/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://book.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def generate_book_url(id):
    '''鏍规嵁id鐢熸垚鍥句功鐨剈rl'''
    return f"https://book.douban.com/subject/{id}/"

def get_book_data(id):
    '''鑾峰彇鍥句功鏁版嵁骞惰繑鍥烇紙鍖呮嫭鍥句功淇℃伅鍜岃瘎璁轰俊鎭級'''
    data = get_book_info(id)
    data["comment_list"] = get_book_comments(id, 100)
    return data

def get_book_info(id):
    '''鑾峰彇鍥句功鐨勫熀鏈俊鎭�'''
    try:
        base_url = generate_book_url(id)
        resp = requests.get(base_url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        
        # 鑾峰彇鍩烘湰淇℃伅
        book_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
        book_info_json = json.loads(book_info_json_str)
        book_url = book_info_json["url"]
        book_id = book_url.split("/")[-2]
        book_name = book_info_json["name"]
        
        # 鑾峰彇鍥句功淇℃伅
        book_infos = bs.find("div", {"id" : "info"})
        
        # 瑙ｆ瀽浣滆€呫€佸嚭鐗堢ぞ銆佸嚭鐗堟棩鏈熺瓑淇℃伅
        author_span = book_infos.find('span', {"class": "pl"}, string=' 浣滆€�:')
        if author_span and author_span.parent:
            book_author = author_span.parent.get_text(strip=True).replace('浣滆€�:', '').strip()
        else:
            author_link = book_infos.find('a', {"class": "author"})
            if author_link:
                book_author = author_link.get_text().strip()
            else:
                if 'author' in book_info_json:
                    author_data = book_info_json['author']
                    if isinstance(author_data, list):
                        book_author = author_data[0].get('name', '鏈煡浣滆€�') if isinstance(author_data[0], dict) else author_data[0]
                    elif isinstance(author_data, dict):
                        book_author = author_data.get('name', '鏈煡浣滆€�')
                    else:
                        book_author = str(author_data)
                else:
                    book_author = "鏈煡浣滆€�"
            
        # 瑙ｆ瀽鍑虹増绀句俊鎭�
        try:
            book_publisher = book_infos.find('span', {"class": "pl"}, string='鍑虹増绀�:').find_next_sibling('a').get_text().strip()
        except (AttributeError, TypeError):
            book_publisher = "鏈煡鍑虹増绀�"
            
        # 瑙ｆ瀽浠锋牸淇℃伅
        try:
            book_price = book_infos.find('span', {"class": "pl"}, string='瀹氫环:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_price = "鏈煡浠锋牸"
            
        # 瑙ｆ瀽鍑虹増鏃ユ湡淇℃伅
        try:
            book_date = book_infos.find('span', {"class": "pl"}, string='鍑虹増骞�:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_date = "鏈煡鍑虹増骞�"
            
        # 瑙ｆ瀽ISBN淇℃伅
        try:
            book_isbn = book_infos.find('span', {"class": "pl"}, string='ISBN:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_isbn = "鏈煡ISBN"
            
        # 鑾峰彇鍥句功璇勫垎
        try:
            book_rating = bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()
        except (AttributeError, TypeError):
            book_rating = "鏈煡璇勫垎"
        
        # 鑾峰彇鍥句功灏侀潰鍥剧墖
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
        # 杩斿洖榛樿鐨勫浘涔︿俊鎭�
        return {
            "book_id": id,
            "book_name": "鏈煡涔﹀悕",
            "book_author": "鏈煡浣滆€�",
            "book_isbn": "鏈煡ISBN",
            "book_publisher": "鏈煡鍑虹増绀�",
            "book_price": "鏈煡浠锋牸",
            "book_date": "鏈煡鍑虹増骞�",
            "book_rating": "鏈煡璇勫垎",
            "book_image": "/book_image/no_book_image.png"
        }

def get_book_comments(id, count):
    '''鑾峰彇鍥句功璇勮淇℃伅'''
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
                    # 鑾峰彇璇勮ID
                    try:
                        comment_id = comment_item["data-cid"]
                    except KeyError:
                        comment_id = f"comment_{comment_count}"
                    
                    # 鑾峰彇鐢ㄦ埛鍚�
                    try:
                        avatar = comment_item.find("div", {"class": "avatar"})
                        comment_username = avatar.find("a")["title"]
                    except (AttributeError, KeyError):
                        comment_username = "鏈煡鐢ㄦ埛"
                    
                    # 鑾峰彇鏈夌敤鏁�
                    try:
                        comment = comment_item.find("div", {"class": "comment"})
                        comment_isuseful = int(comment.find("span", {"class": "vote-count"}).get_text())
                    except (AttributeError, ValueError):
                        comment_isuseful = 0
                    
                    # 鑾峰彇璇勮鏃堕棿
                    try:
                        comment_time_str = comment.find("a", {"class": "comment-time"}).get_text()
                        comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
                        comment_timestamp = int(time.mktime(comment_time))
                    except (AttributeError, ValueError):
                        comment_timestamp = int(time.time())
                    
                    # 鑾峰彇璇勮鍐呭
                    try:
                        comment_content = comment.find("p", {"class": "comment-content"}).get_text().strip()
                    except AttributeError:
                        comment_content = "鑾峰彇璇勮鍐呭澶辫触"
                    
                    # 鑾峰彇璇勫垎
                    try:
                        match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
                        comment_rating = int((match.group(1))) // 10 if match else 0
                    except (AttributeError, ValueError):
                        comment_rating = 0
                    
                    # 淇濆瓨璇勮鏁版嵁
                    comment_texts[comment_id] = comment_content
                    comment_data = {
                        "comment_id": comment_id,
                        "comment_username": comment_username,
                        "comment_timestamp": comment_timestamp,
                        "comment_rating": comment_rating,
                        "comment_content": comment_content,
                        "comment_isuseful": comment_isuseful,
                        "comment_ispositive": 1  # 榛樿璁剧疆涓�1
                    }
                    comments.append(comment_data)
                    
                    comment_count += 1
                    if comment_count >= count:
                        break
                        
                except Exception as e:
                    print(f"鑾峰彇璇勮鏁版嵁鏃跺嚭閿�: {str(e)}")
                    continue
            
            # # 鎯呮劅鍒嗘瀽
            # classify_results = classify(comment_texts)
            # for result in classify_results:
            #     for comment in comments:
            #             if result['comment_id'] == comment['comment_id']:
            #                 comment['comment_ispositive'] = result['is_positive']
                    
            if comment_count >= count:
                break
        
        return comments
        
    except Exception as e:
        print(f"鑾峰彇璇勮鏁版嵁鏃跺嚭閿�: {str(e)}")
        return []

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
