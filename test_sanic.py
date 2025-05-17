# -*- coding: utf-8 -*-
from sanic import Sanic, html, response
from sanic.response import text, json
import time
import json
from jinja2 import Environment, FileSystemLoader
from emotion_classification import classify
import plot
import os
import requests
from db_operations import DatabaseOperations
from datetime import datetime
import book_crawler, movie_crawler
import requests
import httpx
from urllib.parse import urlparse

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
        json.dump(data, f, ensure_ascii=False, indent=4)

def download_search_cache_image(image_url, item_id, is_book=True):
    try:
        if not image_url or image_url in ["None", None]:
            return "/book_image/no_book_image.png" if is_book else "/movie_image/no_movie_image.png"
        # 创建search_cache目录
        cache_dir = "static/search_cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        # 用图片url的hash或item_id命名，防止重复
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
        print(f"下载search_cache图片出错: {e}")
        return "/book_image/no_book_image.png" if is_book else "/movie_image/no_movie_image.png"

@app.route("/v1/index", methods=["GET"])
async def home(request):
    template = env.get_template("index.html")
    return html(template.render())

@app.route("/v1/book/search", methods=["POST"])
async def search_book(request):
    try:
        data = request.json
        search_text = data["search_text"]
        book_ids = book_crawler.book_searcher(search_text)
        
        # 获取每个书籍的基本信息
        search_results = []
        for book_id in book_ids:
            try:
                book_info = book_crawler.get_book_info(book_id)
                # 下载图片到search_cache
                cache_img = download_search_cache_image(book_info["book_image"], book_id, is_book=True)
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
                print(f"获取书籍 {book_id} 信息时出错: {e}")
                continue
                
        return response.json({
            "status": "success",
            "results": search_results
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)
    
@app.route("/v1/movie/search", methods=["POST"])
async def search_movie(request):
    try:
        data = request.json
        search_text = data["search_text"]
        movie_ids = movie_crawler.movie_searcher(search_text)
        
        # 获取每个电影的基本信息
        search_results = []
        for movie_id in movie_ids:
            try:
                movie_info = movie_crawler.get_movie_info(movie_id)
                # 下载图片到search_cache
                cache_img = download_search_cache_image(movie_info["movie_image"], movie_id, is_book=False)
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
                print(f"获取电影 {movie_id} 信息时出错: {e}")
                continue
                
        return response.json({
            "status": "success",
            "results": search_results
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/book/crawl", methods=["POST"])
async def crawl_book(request):
    try:
        data = request.json
        book_id = data["id"]
        print(f"正在爬取ID为 {book_id} 的书籍数据...")
        book_data = book_crawler.get_book_data(id=book_id)
        async with httpx.AsyncClient() as client:
            upload_response = await client.post(
                "http://localhost:8000/v1/book/crawled/upload",
                json=book_data, 
                timeout=5.0
            )
            upload_response.raise_for_status()
        return response.json({
            "status": "success",
            "book_id": book_id,
            "upload_status": "completed"
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)

@app.route("/v1/movie/crawl", methods=["POST"])
async def crawl_movie(request):
    try:
        data = request.json
        movie_id = data["id"]
        print(f"正在爬取ID为 {movie_id} 的电影数据...")
        movie_data = movie_crawler.get_movie_data(id=movie_id)
        
        # 下载并更新图片路径
        movie_image = movie_data.get('movie_image')
        if movie_image is None or movie_image == "None":
            movie_data['movie_image'] = "/movie_image/no_movie_image.png"
        else:
            movie_data['movie_image'] = download_movie_image(movie_image, movie_id)
            
        async with httpx.AsyncClient() as client:
            upload_response = await client.post(
                "http://localhost:8000/v1/movie/crawled/upload",
                json=movie_data, 
                timeout=5.0
            )
            upload_response.raise_for_status()
        return response.json({
            "status": "success",
            "movie_id": movie_id,
            "upload_status": "completed"
        })
    except Exception as e:
        return response.json({"error": str(e)}, status=500)

def download_book_image(image_url, book_id):
    try:
        # 如果是默认图片路径或None，直接返回默认图片
        if image_url == "/book_image/no_book_image.png" or image_url is None or image_url == "None":
            return "/book_image/no_book_image.png"
            
        # 如果没有图片URL，返回默认图片
        if not image_url:
            return "/book_image/no_book_image.png"
            
        # 创建book_image文件夹（如果不存在）
        if not os.path.exists("book_image"):
            os.makedirs("book_image")
            
        # 从URL中获取文件扩展名
        parsed_url = urlparse(image_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'
            
        # 构建本地文件路径
        local_path = f"book_image/{book_id}{file_ext}"
        
        # 如果文件已存在，直接返回路径
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
        print(f"下载图片时出错: {e}")
        return "/book_image/no_book_image.png"

def download_movie_image(image_url, movie_id):
    try:
        # 如果是默认图片路径或None，直接返回默认图片
        if image_url == "/movie_image/no_movie_image.png" or image_url is None or image_url == "None":
            return "/movie_image/no_movie_image.png"
            
        # 如果没有图片URL，返回默认图片
        if not image_url:
            return "/movie_image/no_movie_image.png"
            
        # 创建movie_image文件夹（如果不存在）
        if not os.path.exists("movie_image"):
            os.makedirs("movie_image")
            
        # 从URL中获取文件扩展名
        parsed_url = urlparse(image_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        if not file_ext:
            file_ext = '.jpg'
            
        # 构建本地文件路径
        local_path = f"movie_image/{movie_id}{file_ext}"
        
        # 如果文件已存在，直接返回路径
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
        print(f"下载图片时出错: {e}")
        return "/movie_image/no_movie_image.png"

@app.route("/v1/book/crawled/upload", methods=["POST"])
async def upload_book(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    
    # 保存到文件系统
    save_to_file(request.json, "book")
    
    # 保存到数据库
    if db.save_book_data(request.json):
        plot.plot_book_comment_wordcloud(request.json)
        return response.json({"code": 1, "message": "上传成功"})
    else:
        return response.json({"code": -1, "message": "数据库保存失败"}, status=500)

@app.route("/v1/book/data/<book_id>", methods=["GET"])
async def get_book_data(request, book_id):
    book_data = db.get_book_data(book_id)
    if book_data:
        # 添加书籍图片路径
        book_image = book_data.get('book_image')
        if book_image is None or book_image == "None":
            book_data['book_image'] = "/book_image/no_book_image.png"
        else:
            book_data['book_image'] = download_book_image(book_image, book_id)
            
        # 处理出版日期
        if isinstance(book_data.get('book_publish_date'), datetime):
            book_data['book_publish_date'] = book_data['book_publish_date'].strftime('%Y-%m-%d')
        # 生成词云
        plot.plot_book_comment_wordcloud(book_data)
        wordcloud_path = f"static/book_comment_wordcloud_{book_id}.png"
        
        # 计算评论统计
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
        img_tag_start = rendered.find('<img src="')
        if img_tag_start != -1:
            img_tag_end = rendered.find('"', img_tag_start + 10)
            print(rendered[img_tag_start:img_tag_end+1])
        
        return html(rendered)
    else:
        return response.json({"code": -1, "message": "未找到书籍数据"}, status=404)

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
        writer.writerow(['作者', book_data['book_author']])
        writer.writerow(['出版社', book_data['book_publisher']])
        writer.writerow(['出版日期', book_data['book_publish_date']])
        writer.writerow(['评分', book_data['book_rating']])
        writer.writerow([])  # 空行
        
        # 写入评论信息
        writer.writerow(['评论信息'])
        writer.writerow(['评论时间', '评论内容', '评分', '情感倾向'])
        for comment in book_data['comment_list']:
            writer.writerow([
                comment['comment_time'].strftime('%Y-%m-%d %H:%M:%S'),
                comment['comment_content'],
                comment['comment_rating'],
                '正面' if comment.get('is_positive', 0) == 1 else '负面'
            ])
        
        # 设置响应头
        headers = {
            'Content-Type': 'text/csv; charset=utf-8-sig',
            'Content-Disposition': f'attachment; filename=book_{book_id}.csv'
        }
        
        return response.raw(output.getvalue().encode('utf-8-sig'), headers=headers)
    else:
        return response.json({"code": -1, "message": "未找到书籍数据"}, status=404)

@app.route("/v1/movie/crawled/upload", methods=["POST"])
async def upload_movie(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    
    # 保存到文件系统
    save_to_file(request.json, "movie")

    # 保存到数据库
    if db.save_movie_data(request.json):
        plot.plot_movie_comment_wordcloud(request.json)
        return response.json({"code": 1, "message": "上传成功"})
    else:
        return response.json({"code": -1, "message": "数据库保存失败"}, status=500)

@app.route("/v1/movie/data/<movie_id>", methods=["GET"])
async def get_movie_data(request, movie_id):
    movie_data = db.get_movie_data(movie_id)
    if movie_data:
        # 下载并更新图片路径
        movie_image = movie_data.get('movie_image')
        if movie_image is None or movie_image == "None":
            movie_data['movie_image'] = "/movie_image/no_movie_image.png"
        else:
            movie_data['movie_image'] = download_movie_image(movie_image, movie_id)
            
        # 处理出版日期
        if isinstance(movie_data.get('movie_publish_date'), datetime):
            movie_data['movie_publish_date'] = movie_data['movie_publish_date'].strftime('%Y-%m-%d')
        # 生成词云
        plot.plot_movie_comment_wordcloud(movie_data)
        wordcloud_path = f"static/movie_comment_wordcloud_{movie_id}.png"
        
        # 计算评论统计
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
        img_tag_start = rendered.find('<img src="')
        if img_tag_start != -1:
            img_tag_end = rendered.find('"', img_tag_start + 10)
            print(rendered[img_tag_start:img_tag_end+1])
        
        return html(rendered)
    else:
        return response.json({"code": -1, "message": "未找到电影数据"}, status=404)

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
        writer.writerow(['电影名', movie_data['movie_name']])
        writer.writerow(['导演', movie_data['movie_director']])
        writer.writerow(['类型', movie_data['movie_type']])
        writer.writerow(['上映日期', movie_data['movie_date']])
        writer.writerow(['评分', movie_data['movie_rating']])
        writer.writerow([])  # 空行
        
        # 写入评论信息
        writer.writerow(['评论信息'])
        writer.writerow(['评论时间', '评论内容', '评分', '情感倾向'])
        for comment in movie_data['comment_list']:
            writer.writerow([
                comment['comment_time'].strftime('%Y-%m-%d %H:%M:%S'),
                comment['comment_content'],
                comment['comment_rating'],
                '正面' if comment.get('is_positive', 0) == 1 else '负面'
            ])
        
        # 设置响应头
        headers = {
            'Content-Type': 'text/csv; charset=utf-8-sig',
            'Content-Disposition': f'attachment; filename=movie_{movie_id}.csv'
        }
        
        return response.raw(output.getvalue().encode('utf-8-sig'), headers=headers)
    else:
        return response.json({"code": -1, "message": "未找到电影数据"}, status=404)

@app.route("/v1/crawled/items", methods=["GET"])
async def get_crawled_items(request):
    try:
        with db.connection.cursor() as cursor:
            # 获取已爬取的书籍
            cursor.execute("SELECT book_id, book_name FROM books")
            books = cursor.fetchall()
            # 获取已爬取的电影
            cursor.execute("SELECT movie_id, movie_name FROM movies")
            movies = cursor.fetchall()
            items = []
            for book in books:
                items.append({
                    "id": book['book_id'],
                    "name": book['book_name'],
                    "type": "book"
                })
            for movie in movies:
                items.append({
                    "id": movie['movie_id'],
                    "name": movie['movie_name'],
                    "type": "movie"
                })
            return response.json({"items": items})
    except Exception as e:
        return response.json({"error": str(e)}, status=500)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )