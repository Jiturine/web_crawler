import book_crawler, movie_crawler
import sys
import os
import requests
import json
from db_operations import DatabaseOperations

# type = input("书评(book) or 影评(movie):")
# if(type == "book"):
#     search_text = input("请输入书名：")
#     id = book_crawler.book_searcher(search_text)[0]
#     print(f"正在爬取ID为 {id} 的书籍数据...")
#     data = book_crawler.get_book_data(id=id)
#     response = requests.post("http://localhost:8000/v1/book/crawled/upload", data=json.dumps(data))
# elif(type == "movie"):
#     search_text = input("请输入电影名：")
#     id = movie_crawler.movie_searcher(search_text)[0]
#     print(f"正在爬取ID为 {id} 的电影数据...")
#     data = movie_crawler.get_movie_data(id=id)
#     response = requests.post("http://localhost:8000/v1/movie/crawled/upload", data=json.dumps(data))
# else:
#     print("无效输入!")
while True:
    
    op = input("回复1显示已爬取的书籍，回复2爬取新书籍，回复3退出\n")
    
    if op == "1":
        _stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        db = DatabaseOperations()
        sys.stdout = _stdout 

        with db.connection.cursor() as cursor:
            cursor.execute("SELECT book_id, book_name FROM books")
            books = cursor.fetchall()
            if books:
                print("已爬取的书籍信息：")
                for book in books:
                    print(f"{book['book_name']}（{book['book_id']}）：http://localhost:8000/v1/book/data/{book['book_id']}")
            else:
                print("数据库中暂无书籍信息")
        
        sys.stdout = open(os.devnull, 'w')
        db.close()
        sys.stdout = _stdout
    elif op == "2":
        search_text = input("请输入书名：")
        id = book_crawler.book_searcher(search_text)[0]
        print(f"正在爬取ID为 {id} 的书籍数据...")
        data = book_crawler.get_book_data(id=id)
        response = requests.post("http://localhost:8000/v1/book/crawled/upload", data=json.dumps(data))
        print(response.text)
    elif op == "3":
        break
    else:
        print("没有这个选项")
        continue
