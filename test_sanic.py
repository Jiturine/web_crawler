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

@app.route("/v1/home", methods=["GET"])
async def home(request):
    template = env.get_template("home.html")
    return html(template.render())

@app.route("/v1/book/search", methods=["POST"])
async def search_book(request):
    try:
        data = request.json
        search_text = data["search_text"]
        book_id = book_crawler.book_searcher(search_text)[0]
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
    

def download_image(image_url, book_id):
    try:
        # 如果是默认图片路径或None，直接返回默认图片
        if image_url == "/book_image/no_image.png" or image_url is None or image_url == "None":
            return "/book_image/no_image.png"
            
        # 如果没有图片URL，返回默认图片
        if not image_url:
            return "/static/no_image.png"
            
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
        return "/static/no_image.png"

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
        # 下载并更新图片路径
        book_image = book_data.get('book_image')
        if book_image is None or book_image == "None":
            book_data['book_image'] = "/book_image/no_image.png"
        else:
            book_data['book_image'] = download_image(book_image, book_id)
            
        # 处理出版日期
        if isinstance(book_data.get('book_publish_date'), datetime):
            book_data['book_publish_date'] = book_data['book_publish_date'].strftime('%Y-%m-%d')
        # 生成词云图
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

@app.route("/v1/movie/crawled/upload", methods=["POST"])
async def upload_movie(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    
    # 保存到文件系统
    save_to_file(request.json, "movie")

    # 保存到数据库
    pass
   

# @app.route("/v1/book/comment/sentiment-analysis")
# async def show_plot(request):
#     template = env.get_template("show_plot.html")
#     latest_img_path = get_latest_file("static")
#     return html(template.render(title="鎯呮劅鍒嗘瀽", img_path=latest_img_path))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)