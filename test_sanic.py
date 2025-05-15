# -*- coding: utf-8 -*-
from sanic import Sanic, html, response
from sanic.response import text, json
import time
import json
from jinja2 import Environment, FileSystemLoader
from emotion_classification import classify
import plot
import os
from db_operations import DatabaseOperations
from datetime import datetime
import book_crawler, movie_crawler
import requests
import httpx

app = Sanic("mySanic")
app.static("/static", "./static") 

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
    

@app.route("/v1/book/crawled/upload", methods=["POST"])
async def upload_book(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    
    # 保存到文件系统
    save_to_file(request.json, "book")
    
    # 保存到数据库
    if db.save_book_data(request.json):
        plot.plot_book_comment_wordcloud(request.json)
        return response.json({"code": 1, "message": "上传成功！"})
    else:
        return response.json({"code": -1, "message": "数据库保存失败"}, status=500)

@app.route("/v1/book/data/<book_id>", methods=["GET"])
async def get_book_data(request, book_id):
    book_data = db.get_book_data(book_id)
    if book_data:
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
        return html(template.render(
            title=f"{book_data['book_name']} - 详情",
            book=book_data,
            wordcloud_path=wordcloud_path,
            total_comments=total_comments,
            positive_comments=positive_comments,
            negative_comments=negative_comments
        ))
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

    return response.json({"code": 1, "message": "上传成功！"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)