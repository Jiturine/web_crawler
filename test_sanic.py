from sanic import Sanic, html, response
from sanic.response import text, json
import time
import json
from jinja2 import Environment, FileSystemLoader
from emotion_classification import classify

app = Sanic("mySanic")

env = Environment(loader=FileSystemLoader("templates"))

# @app.route("/")
# async def index(request):
#     template = env.get_template("index.html")
#     return html(template.render(title="Python 前端示例", items=["苹果", "香蕉", "橘子"]))

@app.route("/v1/book/crawled/upload", methods=["POST"])
async def upload(request):
    if not request.json:
        return response.json({"error": "未提供 JSON 数据"}, status=400)
    path = "./upload"
    now_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
    filename = now_time + ".json"
    with open(path + "/" + filename, 'w', encoding='utf-8') as f:
        json.dump(request.json, f, ensure_ascii=False, indent=4)
    comment_texts = [comment["comment_content"] for comment in request.json["comment_list"]]
    print(classify(comment_texts[0]))
    return response.json({"code": 1, "message": "upload success!"})

@app.route("/v1/book/info", methods=['GET'])
async def get_books_info(request):
    return response.json({"code": 1, "msg": "convert successfully", "data": None})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)