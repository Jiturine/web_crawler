from sanic import Sanic, html, response
from sanic.response import text, json
import time
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from emotion_classification import classify
import plot
import os
import searcher
import time
app = Sanic("Web_Crawler")
app.static("/static", "./static") 

env = Environment(loader=FileSystemLoader(os.path.dirname(os.path.abspath(__file__))+"/templates"),autoescape=select_autoescape(["html", "htm"]))

def get_latest_file(directory):
    files = [os.path.join(directory, f) for f in os.listdir(directory)]
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return None
    latest_file = max(files, key=os.path.getmtime)
    return latest_file
@app.route("/")
async def home(request):
    template = env.get_template("index.html")
    return html(template.render())

@app.route("/v1/search")
async def search_handler(request):
    query = request.args.get("query", "")
    results = searcher.searcher2(query)
    
    return json({
        "query": query,
        "timestamp": time.now().timestamp(),
        "results": results
    })

@app.route("/v1/book/crawled/upload", methods=["POST"])
async def upload_book(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    path =os.path.dirname(os.path.abspath(__file__))+ "/upload"
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    filename = now_time + ".json"
    with open(path + "/" + filename, 'w', encoding='utf-8') as f:
        json.dump(request.json, f, ensure_ascii=False, indent=4)
    plot.plot_book_comment_wordcloud(request.json)
    return response.json({"code": 1, "message": "upload success!"})

@app.route("/v1/movie/crawled/upload", methods=["POST"])
async def upload_movie(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    path =os.path.dirname(os.path.abspath(__file__))+ "/upload"
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    filename = now_time + ".json"
    with open(path + "/" + filename, 'w', encoding='utf-8') as f:
        json.dump(request.json, f, ensure_ascii=False, indent=4)
    return response.json({"code": 1, "message": "upload success!"})

@app.route("/v1/book/comment/sentiment-analysis")
async def show_plot(request):
    template = env.get_template("show_plot.html")
    latest_img_path = get_latest_file("static")
    return html(template.render(title="Python 前端示例", img_path=latest_img_path))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)