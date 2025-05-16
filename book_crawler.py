import json
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
from emotion_classification import classify_text

def book_searcher(search_text):
    '''根据关键词搜索书籍对应的url列表'''
    url = f"https://search.douban.com/book/subject_search?search_text={search_text}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://book.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def generate_book_url(id):
    '''根据id生成书籍的url'''
    return f"https://book.douban.com/subject/{id}/"

def get_book_data(id):
    '''获取书籍的爬虫数据 (包括书籍基本信息和评论信息)'''
    data = get_book_info(id)
    data["comment_list"] = get_book_comments(id, 100)
    return data

def get_book_info(id):
    '''获取书籍的基本信息'''
    try:
        base_url = generate_book_url(id)
        resp = requests.get(base_url, headers=headers)
        bs = BeautifulSoup(resp.text, 'html.parser')
        
        # 获取基本信息
        try:
            book_info_json_str = bs.find("script", {"type": "application/ld+json"}).get_text()
            book_info_json = json.loads(book_info_json_str)
            book_url = book_info_json["url"]
            book_id = book_url.split("/")[-2]
            book_name = book_info_json["name"]
        except (AttributeError, KeyError, json.JSONDecodeError):
            book_id = id
            book_name = "未知书名"
        
        # 获取详细信息
        book_infos = bs.find("div", {"id" : "info"})
        
        # 作者
        try:
            author_span = book_infos.find('span', {"class": "pl"}, string=' 作者')
            book_author = author_span.parent.get_text(strip=True).replace('作者:', '').strip()
        except (AttributeError, TypeError):
            book_author = "未知作者"
            
        # 出版社
        try:
            book_publisher = book_infos.find('span', {"class": "pl"}, string='出版社:').find_next_sibling('a').get_text().strip()
        except (AttributeError, TypeError):
            book_publisher = "未知出版社"
            
        # 价格
        try:
            book_price = book_infos.find('span', {"class": "pl"}, string='定价:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_price = "暂无价格"
            
        # 出版日期
        try:
            book_date = book_infos.find('span', {"class": "pl"}, string='出版年:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_date = "未知出版日期"
            
        # ISBN
        try:
            book_isbn = book_infos.find('span', {"class": "pl"}, string='ISBN:').next_sibling.get_text().strip()
        except (AttributeError, TypeError):
            book_isbn = "未知ISBN"
            
        # 评分
        try:
            book_rating = bs.find("div", {"id": "interest_sectl"}).find("strong").get_text().strip()
        except (AttributeError, TypeError):
            book_rating = "暂无评分"
        
        # 获取书籍图片URL
        try:
            img = bs.find("div", {"id": "mainpic"}).find("a").find("img")
            if img and img.get('src'):
                book_image = img['src']
            else:
                book_image = "/static/no_image.png"
        except (AttributeError, KeyError):
            book_image = "/static/no_image.png"
        
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
        print(f"获取书籍信息时出错: {e}")
        # 返回一个包含默认值的基本信息
        return {
            "book_id": id,
            "book_name": "未知书名",
            "book_author": "未知作者",
            "book_isbn": "未知ISBN",
            "book_publisher": "未知出版社",
            "book_price": "暂无价格",
            "book_date": "未知出版日期",
            "book_rating": "暂无评分",
            "book_image": "/book_image/no_book_image.png"
        }

def get_book_comments(id, count):
    '''获取书籍的评论信息'''
    try:
        urls = []
        i = 0
        base_url = generate_book_url(id)
        while (i < count):
            urls.append(base_url + "comments/" + "?start={0}&limit=20&status=P&sort=hotest".format(i))
            i += 20
        comments = []
        comment_count = 0
        for url in urls:
            try:
                resp = requests.get(url, headers=headers)
                bs = BeautifulSoup(resp.text, 'html.parser')
                comment_items = bs.find_all("li", {"class": "comment-item"})
                for comment_item in comment_items:
                    try:
                        comment_id = comment_item["data-cid"]
                    except KeyError:
                        comment_id = f"comment_{comment_count}"
                        
                    try:
                        avatar = comment_item.find("div", {"class": "avatar"})
                        comment_username = avatar.find("a")["title"]
                    except (AttributeError, KeyError):
                        comment_username = "匿名用户"
                        
                    try:
                        comment = comment_item.find("div", {"class": "comment"})
                        comment_isuseful = int(comment.find("span", {"class": "vote-count"}).get_text())
                    except (AttributeError, ValueError):
                        comment_isuseful = 0
                        
                    try:
                        comment_time_str = comment.find("a", {"class": "comment-time"}).get_text()
                        comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
                        comment_timestamp = int(time.mktime(comment_time))
                    except (AttributeError, ValueError):
                        comment_timestamp = int(time.time())
                        
                    try:
                        comment_content = comment.find("p", {"class": "comment-content"}).get_text().strip()
                    except AttributeError:
                        comment_content = "评论内容获取失败"
                        
                    try:
                        match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
                        comment_rating = int((match.group(1))) // 10 if match else 0
                    except (AttributeError, ValueError):
                        comment_rating = 0
                        
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
