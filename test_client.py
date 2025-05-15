import book_crawler, movie_crawler
import requests
import json

type = input("书评(book) or 影评(movie):")
if(type == "book"):
    search_text = input("请输入书名：")
    id = book_crawler.book_searcher(search_text)[0]
    print(f"正在爬取ID为 {id} 的书籍数据...")
    data = book_crawler.get_book_data(id=id)
    response = requests.post("http://localhost:8000/v1/book/crawled/upload", data=json.dumps(data))
elif(type == "movie"):
    search_text = input("请输入电影名：")
    id = movie_crawler.movie_searcher(search_text)[0]
    print(f"正在爬取ID为 {id} 的电影数据...")
    data = movie_crawler.get_movie_data(id=id)
    response = requests.post("http://localhost:8000/v1/movie/crawled/upload", data=json.dumps(data))
else:
    print("无效输入!")