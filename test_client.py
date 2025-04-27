import book_crawler
import requests
import json

search_text = input("请输入书名：")
id = book_crawler.book_searcher(search_text)[0]
data = book_crawler.get_book_data(id=id)
response = requests.post("http://localhost:8000/v1/book/crawled/upload", data=json.dumps(data))
print(response.text)