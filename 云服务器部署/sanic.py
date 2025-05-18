#!/usr/bin/env python
# -*- coding: utf-8 -*-
from auth import generate_token, verify_token
from sanic import Sanic, html, response
from sanic.response import text, json as json_response
from sanic.exceptions import Unauthorized
import time
import json as json_lib
from json.decoder import JSONDecodeError
from jinja2 import Environment, FileSystemLoader
import plot
import os
import requests
from db_operations import DatabaseOperations
from datetime import datetime, timedelta
import book_crawler, movie_crawler
import requests
import httpx
from urllib.parse import urlparse
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
import aiohttp
import asyncio

app = Sanic("mySanic")
app.static("/static", "./static", name="static_files")
app.static("/book_image", "./book_image", name="book_images")
app.static("/movie_image", "./movie_image", name="movie_image")

env = Environment(
    loader=FileSystemLoader("templates", encoding='utf-8'),
    auto_reload=True
)
db = DatabaseOperations()

def save_to_file(data, type):
    path = os.path.dirname(os.path.abspath(__file__)) + f"/upload/{type}"
    if not os.path.exists(path):
        os.makedirs(path)
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    filename = now_time + ".json"
    with open(path + "/" + filename, 'w', encoding='utf-8') as f:
        json_lib.dump(data, f, ensure_ascii=False, indent=4)

def download_search_cache_image(image_url, item_id, is_book=True):
    try:
        if not image_url or image_url in ["None", None]:
            return "/book_image/no_book_image.png" if is_book else "/movie_image/no_movie_image.png"
            
        # 如果是本地路径，直接返回
        if image_url.startswith('/'):
            return image_url
            
        # 创建search_cache目录
        cache_dir = "static/search_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
            
        # 将图片url和item_id拼接生成唯一文件名，防止重复
        ext = os.path.splitext(image_url)[1]
        if not ext or len(ext) > 5:
            ext = ".jpg"
        filename = f"{item_id}{ext}"
        local_path = os.path.join(cache_dir, filename)
        
        if not os.path.exists(local_path):
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://book.douban.com/' if is_book else 'https://movie.douban.com/'
            }
            resp = requests.get(image_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(resp.content)
            else:
                return "/book_image/no_book_image.png" if is_book else "/movie_image/no_movie_image.png"
                
        return f"/static/search_cache/{filename}"
    except Exception as e:
        print(f"搜索缓存图片失败: {e}")
        return "/book_image/no_book_image.png" if is_book else "/movie_image/no_movie_image.png"

@app.route("/v1/index", methods=["GET"])
async def index(request):
    template = env.get_template("index.html")
    return html(template.render())

@app.route("/login", methods=["GET"])
async def home(request):
    template = env.get_template("login.html")
    return html(template.render())

@app.route("/register", methods=["GET"])
async def register_page(request):
    template = env.get_template("register.html")
    return html(template.render())

@app.route("/v1/book/search", methods=["POST"])
async def search_book(request):
    try:
        data = request.json
        search_text = data["search_text"]
        book_ids = book_crawler.book_searcher(search_text)
        
        # 获取每本书的详细信息
        search_results = []
        for book_id in book_ids:
            try:
                book_info = book_crawler.get_book_info(book_id)
                # 获取图片并保存到search_cache
                image_url = book_info.get("book_image")
                if not image_url or image_url == "None":
                    cache_img = "/book_image/no_book_image.png"
                else:
                    cache_img = download_search_cache_image(image_url, book_id, is_book=True)
                
                search_results.append({
                    "id": book_id,
                    "name": book_info["book_name"],
                    "image": cache_img,
                    "author": book_info["book_author"],
                    "publisher": book_info["book_publisher"],
                    "rating": book_info["book_rating"],
                    "publish_date": book_info["book_date"]
                })
            except Exception as e:
                print(f"获取书籍 {book_id} 信息时出�?: {str(e)}")
                continue
                
        return response.json({
            "status": "success",
            "results": search_results
        })
    except Exception as e:
        print(f"搜索书籍时出�?: {str(e)}")
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/movie/search", methods=["POST"])
async def search_movie(request):
    try:
        data = request.json
        search_text = data["search_text"]
        movie_ids = movie_crawler.movie_searcher(search_text)
        
        # 获取每部电影的详细信�?
        search_results = []
        for movie_id in movie_ids:
            try:
                movie_info = movie_crawler.get_movie_info(movie_id)
                # 获取图片并保存到search_cache
                image_url = movie_info.get("movie_image")
                if not image_url or image_url == "None":
                    cache_img = "/movie_image/no_movie_image.png"
                else:
                    cache_img = download_search_cache_image(image_url, movie_id, is_book=False)
                
                search_results.append({
                    "id": movie_id,
                    "name": movie_info["movie_name"],
                    "image": cache_img,
                    "director": movie_info["movie_director"],
                    "rating": movie_info["movie_rating"],
                    "release_date": movie_info["movie_date"],
                    "type": movie_info["movie_type"]
                })
            except Exception as e:
                print(f"获取电影 {movie_id} 信息时出�?: {e}")
                continue
                
        return response.json({
            "status": "success",
            "results": search_results
        })
    except Exception as e:
        print(f"搜索电影时出�?: {e}")
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/book/crawl", methods=["POST"])
async def crawl_book(request):
    try:
        # 从请求头获取token并验证用�?
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return response.json({"error": "未提供有效的token"}, status=401)
        
        user_id = verify_token(token.split(' ')[1])
        if not user_id:
            return response.json({"error": "无效的token"}, status=401)
            
        # 获取用户�?
        sql = "SELECT username FROM users WHERE id = %s"
        result = db.execute_query(sql, (user_id,))
        if not result:
            return response.json({"error": "用户不存�?"}, status=404)
        username = result[0]['username']
            
        data = request.json
        book_id = data["id"]
        
        print(f"正在获取ID�? {book_id} 的书本数据到用户 {username}...")
        book_data = book_crawler.get_book_data(id=book_id)
        
        # 保存书本数据
        async with httpx.AsyncClient() as client:
            upload_response = await client.post(
                "http://106.52.139.242:8000/v1/book/crawled/upload",
                json=book_data, 
                timeout=5.0
            )
            upload_response.raise_for_status()
            
        # 保存用户数据关联
        sql = """
            INSERT INTO user_data (user_id, data_id, data_type, created_at)
            VALUES (%s, %s, 'book', CURRENT_TIMESTAMP)
        """
        db.execute_query(sql, (user_id, book_id))
        print(f"用户 {username} 成功爬取并保存了书籍 {book_id} 的数�?")
            
        return response.json({
            "status": "success",
            "book_id": book_id,
            "upload_status": "completed"
        })
    except Exception as e:
        print(f"爬取书籍时出�?: {str(e)}")
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/movie/crawl", methods=["POST"])
async def crawl_movie(request):
    try:
        # 从请求头获取token并验证用�?
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return response.json({"error": "未提供有效的token"}, status=401)
        
        user_id = verify_token(token.split(' ')[1])
        if not user_id:
            return response.json({"error": "无效的token"}, status=401)
            
        # 获取用户�?
        sql = "SELECT username FROM users WHERE id = %s"
        result = db.execute_query(sql, (user_id,))
        if not result:
            return response.json({"error": "用户不存�?"}, status=404)
        username = result[0]['username']
            
        data = request.json
        movie_id = data["id"]
        
        print(f"正在获取ID�? {movie_id} 的电影数据到用户 {username}...")
        movie_data = movie_crawler.get_movie_data(id=movie_id)
        
        # 保存电影图片路径
        movie_image = movie_data.get('movie_image')
        if movie_image is None or movie_image == "None":
            movie_data['movie_image'] = "/movie_image/no_movie_image.png"
        else:
            movie_data['movie_image'] = download_movie_image(movie_image, movie_id)
            
        # 保存电影数据
        async with httpx.AsyncClient() as client:
            upload_response = await client.post(
                "http://106.52.139.242:8000/v1/movie/crawled/upload",
                json=movie_data, 
                timeout=5.0
            )
            upload_response.raise_for_status()
            
        # 保存用户数据关联
        sql = """
            INSERT INTO user_data (user_id, data_id, data_type, created_at)
            VALUES (%s, %s, 'movie', CURRENT_TIMESTAMP)
        """
        db.execute_query(sql, (user_id, movie_id))
        print(f"用户 {username} 成功爬取并保存了电影 {movie_id} 的数�?")
            
        return response.json({
            "status": "success",
            "movie_id": movie_id,
            "upload_status": "completed"
        })
    except Exception as e:
        print(f"爬取电影时出�?: {str(e)}")
        return response.json({"error": str(e)}, status=500)

def download_book_image(image_url, book_id):
    try:
        # 默认图片路径None，直接返回默认图�?
        if image_url == "/book_image/no_book_image.png" or image_url is None or image_url == "None":
            return "/book_image/no_book_image.png"
            
        # 如果用户图片URL为None，返回默认图�?
        if not image_url:
            return "/book_image/no_book_image.png"
            
        # 如果book_image目录不存在，创建目录
        if not os.path.exists("book_image"):
            os.makedirs("book_image")
            
        # 从URL提取文件扩展�?
        parsed_url = urlparse(image_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'
            
        # 构建本地路径
        local_path = f"book_image/{book_id}{file_ext}"
        
        # 如果文件存在，直接返回路�?
        if os.path.exists(local_path):
            return f"/book_image/{book_id}{file_ext}"
            
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://book.douban.com/'
        }
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        
        # 保存图片
        with open(local_path, 'wb') as f:
            f.write(response.content)
            
        return f"/book_image/{book_id}{file_ext}"
    except Exception as e:
        print(f"下载图片时出�?: {e}")
        return "/book_image/no_book_image.png"

def download_movie_image(image_url, movie_id):
    try:
        # 默认图片路径None，直接返回默认图�?
        if image_url == "/movie_image/no_movie_image.png" or image_url is None or image_url == "None":
            return "/movie_image/no_movie_image.png"
            
        # 如果用户图片URL为None，返回默认图�?
        if not image_url:
            return "/movie_image/no_movie_image.png"
            
        # 如果movie_image目录不存在，创建目录
        if not os.path.exists("movie_image"):
            os.makedirs("movie_image")
            
        # 从URL提取文件扩展�?
        parsed_url = urlparse(image_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'
            
        # 构建本地路径
        local_path = f"movie_image/{movie_id}{file_ext}"
        
        # 如果文件存在，直接返回路�?
        if os.path.exists(local_path):
            return f"/movie_image/{movie_id}{file_ext}"
            
        # 下载图片
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://movie.douban.com/'
        }
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        
        # 保存图片
        with open(local_path, 'wb') as f:
            f.write(response.content)
            
        return f"/movie_image/{movie_id}{file_ext}"
    except Exception as e:
        print(f"下载图片时出�?: {e}")
        return "/movie_image/no_movie_image.png"

@app.route("/v1/book/crawled/upload", methods=["POST"])
async def upload_book(request):
    if not request.json:
        return response.json({"error": "未提�? JSON 数据"}, status=400)
    
    # 保存到文件系�?
    save_to_file(request.json, "book")
    
    # 保存到数据库
    if db.save_book_data(request.json):
        plot.plot_book_comment_wordcloud(request.json)
        return response.json({"code": 1, "message": "上传成功"})
    else:
        return response.json({"code": -1, "message": "数据库保存失�?"}, status=500)

@app.route("/v1/book/data/<book_id>", methods=["GET"])
async def get_book_data(request, book_id):
    try:
        user_id = request.ctx.user_id  # 获取之前用户的ID
        
        # 检查用户是否有权限访问该数�?
        sql = "SELECT 1 FROM user_data WHERE user_id = %s AND data_id = %s AND data_type = 'book'"
        result = db.execute_query(sql, (user_id, book_id))
        if not result:
            return response.json({"error": "未找到该数据或用户权限不�?"}, status=404)
            
        # 获取书籍数据
        sql = "SELECT * FROM books WHERE id = %s"
        result = db.execute_query(sql, (book_id,))
        if not result:
            return response.json({"error": "未找到该书籍"}, status=404)
            
        book_data = result[0]
        # 获取书籍图片路径
        book_image = book_data.get('book_image')
        if book_image is None or book_image == "None":
            book_data['book_image'] = "/book_image/no_book_image.png"
        else:
            book_data['book_image'] = download_book_image(book_image, book_id)
            
        # 生成词云
        plot.plot_book_comment_wordcloud(book_data)
        wordcloud_path = f"static/book_comment_wordcloud_{book_id}.png"
        
        # 生成统计
        total_comments = len(book_data['comment_list'])
        positive_comments = len([c for c in book_data['comment_list'] if c.get('is_positive', 0) == 1])
        negative_comments = total_comments - positive_comments
        
        # 渲染模板
        template = env.get_template("book_detail.html")
        rendered = template.render(
            title=f"{book_data['book_name']} - 详情",
            book=book_data,
            wordcloud_path=wordcloud_path,
            total_comments=total_comments,
            positive_comments=positive_comments,
            negative_comments=negative_comments
        )
        
        return html(rendered)
    except Exception as e:
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/book/data/<book_id>/csv", methods=["GET"])
async def get_book_csv(request, book_id):
    book_data = db.get_book_data(book_id)
    if book_data:
        import csv
        import io
        
        # 创建CSV文件
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入基本信息
        writer.writerow(['基本信息'])
        writer.writerow(['书名', book_data['book_name']])
        writer.writerow(['作�?', book_data['book_author']])
        writer.writerow(['出版�?', book_data['book_publisher']])
        writer.writerow(['出版日期', book_data['book_publish_date']])
        writer.writerow(['评分', book_data['book_rating']])
        writer.writerow([])  # 空行
        
        # 写入评论信息
        writer.writerow(['评论信息'])
        writer.writerow(['评论时间', '评论内容', '评论评分', '是否正面'])
        for comment in book_data['comment_list']:
            writer.writerow([
                comment['comment_time'].strftime('%Y-%m-%d %H:%M:%S'),
                comment['comment_content'],
                comment['comment_rating'],
                '正面' if comment.get('is_positive', 0) == 1 else '负面'
            ])
        
        # 设置响应�?
        headers = {
            'Content-Type': 'text/csv; charset=utf-8-sig',
            'Content-Disposition': f'attachment; filename=book_{book_id}.csv'
        }
        
        return response.raw(output.getvalue().encode('utf-8-sig'), headers=headers)
    else:
        return response.json({"code": -1, "message": "未找到该书籍"}, status=404)

@app.route("/v1/movie/crawled/upload", methods=["POST"])
async def upload_movie(request):
    if not request.json:
        return response.json({"error": "未提�? JSON 数据"}, status=400)
    
    # 保存到文件系�?
    save_to_file(request.json, "movie")

    # 保存到数据库
    if db.save_movie_data(request.json):
        plot.plot_movie_comment_wordcloud(request.json)
        return response.json({"code": 1, "message": "上传成功"})
    else:
        return response.json({"code": -1, "message": "数据库保存失�?"}, status=500)

@app.route("/v1/movie/data/<movie_id>", methods=["GET"])
async def get_movie_data(request, movie_id):
    try:
        movie_data = db.get_movie_data(movie_id)
        if movie_data:
            # 获取电影图片路径
            movie_image = movie_data.get('movie_image')
            if movie_image is None or movie_image == "None":
                movie_data['movie_image'] = "/movie_image/no_movie_image.png"
            else:
                movie_data['movie_image'] = download_movie_image(movie_image, movie_id)
                
            # 生成词云
            plot.plot_movie_comment_wordcloud(movie_data)
            wordcloud_path = f"static/movie_comment_wordcloud_{movie_id}.png"
            
            # 生成统计
            total_comments = len(movie_data['comment_list'])
            positive_comments = len([c for c in movie_data['comment_list'] if c.get('is_positive', 0) == 1])
            negative_comments = total_comments - positive_comments
            
            # 渲染模板
            template = env.get_template("movie_detail.html")
            rendered = template.render(
                title=f"{movie_data['movie_name']} - 详情",
                movie=movie_data,
                wordcloud_path=wordcloud_path,
                total_comments=total_comments,
                positive_comments=positive_comments,
                negative_comments=negative_comments
            )
            
            return html(rendered)
        else:
            return response.json({"error": "未找到电影数�?"}, status=404)
    except Exception as e:
        print(f"获取电影数据时出�?: {str(e)}")
        return response.json({"error": "获取电影数据失败"}, status=500)

@app.route("/v1/movie/data/<movie_id>/csv", methods=["GET"])
async def get_movie_csv(request, movie_id):
    movie_data = db.get_movie_data(movie_id)
    if movie_data:
        import csv
        import io
        
        # 创建CSV文件
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入基本信息
        writer.writerow(['基本信息'])
        writer.writerow(['电影�?', movie_data['movie_name']])
        writer.writerow(['导演', movie_data['movie_director']])
        writer.writerow(['类型', movie_data['movie_type']])
        writer.writerow(['上映日期', movie_data['movie_date']])
        writer.writerow(['评分', movie_data['movie_rating']])
        writer.writerow([])  # 空行
        
        # 写入评论信息
        writer.writerow(['评论信息'])
        writer.writerow(['评论时间', '评论内容', '评论评分', '是否正面'])
        for comment in movie_data['comment_list']:
            writer.writerow([
                comment['comment_time'],
                comment['comment_content'],
                comment['comment_rating'],
                '正面' if comment.get('is_positive', 0) == 1 else '负面'
            ])
        
        # 设置响应�?
        headers = {
            'Content-Type': 'text/csv; charset=utf-8-sig',
            'Content-Disposition': f'attachment; filename=movie_{movie_id}.csv'
        }
        
        return response.raw(output.getvalue().encode('utf-8-sig'), headers=headers)
    else:
        return response.json({"code": -1, "message": "未找到该电影"}, status=404)

@app.route("/v1/crawled/items", methods=["GET"])
async def get_crawled_items(request):
    try:
        # 从请求头获取token并验证用�?
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return response.json({"error": "未提供有效的token"}, status=401)
        
        user_id = verify_token(token.split(' ')[1])
        if not user_id:
            return response.json({"error": "无效的token"}, status=401)

        # 获取用户�?
        sql = "SELECT username FROM users WHERE id = %s"
        result = db.execute_query(sql, (user_id,))
        if not result:
            return response.json({"error": "用户不存�?"}, status=404)
        username = result[0]['username']
            
        # 获取用户已爬取的书籍
        sql = """
            SELECT b.book_id as id, b.book_name as name, 'book' as type, b.book_image as image,
                   b.book_author as author, b.book_publisher as publisher, b.book_date as publish_date,
                   b.book_rating as rating
            FROM user_data ud
            JOIN books b ON ud.data_id = b.book_id
            WHERE ud.user_id = %s AND ud.data_type = 'book'
        """
        books = db.execute_query(sql, (user_id,))
        
        # 获取用户已爬取的电影
        sql = """
            SELECT m.movie_id as id, m.movie_name as name, 'movie' as type, m.movie_image as image,
                   m.movie_director as director, m.movie_type as type, m.movie_date as release_date,
                   m.movie_rating as rating
            FROM user_data ud
            JOIN movies m ON ud.data_id = m.movie_id
            WHERE ud.user_id = %s AND ud.data_type = 'movie'
        """
        movies = db.execute_query(sql, (user_id,))
        
        # 合并结果
        items = []
        if books:
            items.extend(books)
        if movies:
            items.extend(movies)
            
        print(f"用户 {username} 的已爬取信息有：{len(items)} �?")
        
        return response.json({"items": items})
    except Exception as e:
        print(f"获取已爬取信息时出错: {str(e)}")
        return response.json({"error": str(e)}, status=500)

@app.route("/register", methods=["POST"])
async def register(request):
    try:
        data = request.json
        if not data or not data.get("username") or not data.get("password"):
            return json_response({"error": "用户名和密码不能为空"}, status=400)
        
        username = data["username"]
        password = data["password"]
        
        # 检查用户名是否已存�?
        existing_user = db.get_user_by_username(username)
        if existing_user:
            return json_response({"error": "用户名已存在"}, status=400)
        
        # 创建新用�?
        hashed_password = generate_password_hash(password)
        if db.create_user(username, hashed_password):
            return json_response({"message": "注册成功"})
        else:
            return json_response({"error": "注册失败"}, status=500)
            
    except Exception as e:
        print(f"注册时出�?: {e}")
        return json_response({"error": "注册失败"}, status=500)

@app.route("/login", methods=["POST"])
async def login(request):
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return json_response({"error": "用户名和密码都不能为�?"}, status=400)
    
    try:
        # 获取用户信息
        user = db.get_user_by_username(username)
        if not user:
            return json_response({"error": "用户名或密码错误"}, status=401)
        
        # 验证密码
        if not check_password_hash(user['password'], password):
            return json_response({"error": "用户名或密码错误"}, status=401)
        
        # 生成JWT token
        token = generate_token(user['id'])
        
        # 获取用户已爬取的信息数量
        sql = """
            SELECT COUNT(*) as count 
            FROM user_data 
            WHERE user_id = %s
        """
        result = db.execute_query(sql, (user['id'],))
        crawled_count = result[0]['count'] if result else 0
        
        print(f"用户 {username} 登录成功，已爬取信息有：{crawled_count} �?")
        
        return json_response({
            "message": "登录成功",
            "token": token, 
            "user": {
                "id": user['id'], 
                "username": user['username']
            }
        })
    except Exception as e:
        print(f"登录时出�?: {e}")
        return json_response({"error": "登录失败"}, status=500)

@app.route("/user/info", methods=["GET"])
async def get_user_info(request):
    user_id = request.ctx.user_id
    
    try:
        sql = "SELECT id, username, email, created_at FROM users WHERE id = %s"
        result = db.execute_query(sql, (user_id,))
        
        if not result:
            return json_response({"error": "用户不存�?"}, status=404)
        
        return json_response(result[0])
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

@app.route("/user/data", methods=["GET"])
async def get_user_data(request):
    user_id = request.ctx.user_id
    
    try:
        # 获取用户所有数�?
        sql = """
            SELECT ud.data_id, ud.data_type, 
                   COALESCE(b.book_name, m.movie_name) as name,
                   COALESCE(b.book_author, m.movie_director) as creator,
                   COALESCE(b.book_publisher, m.movie_type) as category,
                   COALESCE(b.book_date, m.movie_date) as date,
                   COALESCE(b.book_rating, m.movie_rating) as rating,
                   COALESCE(b.book_image, m.movie_image) as image
            FROM user_data ud
            LEFT JOIN books b ON ud.data_id = b.id AND ud.data_type = 'book'
            LEFT JOIN movies m ON ud.data_id = m.id AND ud.data_type = 'movie'
            WHERE ud.user_id = %s
            ORDER BY ud.created_at DESC
        """
        result = db.execute_query(sql, (user_id,))
        
        # 处理图片路径
        for item in result:
            if item['data_type'] == 'book':
                if not item['image'] or item['image'] == 'None':
                    item['image'] = "/book_image/no_book_image.png"
                else:
                    item['image'] = download_book_image(item['image'], item['data_id'])
            else:  # movie
                if not item['image'] or item['image'] == 'None':
                    item['image'] = "/movie_image/no_movie_image.png"
                else:
                    item['image'] = download_movie_image(item['image'], item['data_id'])
        
        return json_response({"items": result})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)

def init_db():
    try:
        # 创建用户�?
        sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        db.execute_query(sql)
        
        # 创建用户数据�?
        sql = """
            CREATE TABLE IF NOT EXISTS user_data (
                user_id INT NOT NULL,
                data_id VARCHAR(50) NOT NULL,
                data_type ENUM('book', 'movie') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, data_id, data_type),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """
        db.execute_query(sql)
        
        print("数据库初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")

@app.route("/", methods=["GET"])
async def root(request):
    return response.redirect('/login')

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 启动服务�?
    app.run(
        host="0.0.0.0", 
        port=8000,
        access_log=True,  # 启用访问日志
        debug=True,       # 启用调试模式
        auto_reload=True  # 启用自动重载
    )