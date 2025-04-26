import book_crawler
import requests
import json

data = book_crawler.get_book_data("https://book.douban.com/subject/2567698/")
print("hello world")
response = requests.post("http://localhost:8000/v1/book/crawled/upload", data=json.dumps(data))
print(response.text)