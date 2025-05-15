 #!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
from pymysql import Error
from db_config import DB_CONFIG
from datetime import datetime

class DatabaseOperations:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = pymysql.connect(**DB_CONFIG)
            if self.connection.open:
                print("成功连接到MySQL数据库")
                self.create_tables()
        except Error as e:
            print(f"连接数据库时出错: {e}")

    def create_tables(self):
        try:
            with self.connection.cursor() as cursor:
                # 创建书籍表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS books (
                        book_id VARCHAR(20) PRIMARY KEY,
                        book_name VARCHAR(255) NOT NULL,
                        book_author VARCHAR(255),
                        book_isbn VARCHAR(20),
                        book_publisher VARCHAR(255),
                        book_price VARCHAR(50),
                        book_date VARCHAR(50),
                        book_rating VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                # 创建评论表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS book_comments (
                        comment_id VARCHAR(20) PRIMARY KEY,
                        book_id VARCHAR(20),
                        comment_username VARCHAR(255),
                        comment_timestamp INT,
                        comment_rating INT,
                        comment_content TEXT,
                        comment_isuseful INT,
                        is_positive TINYINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (book_id) REFERENCES books(book_id)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                self.connection.commit()
                print("数据表创建成功")
        except Error as e:
            print(f"创建表时出错: {e}")

    def save_book_data(self, book_data):
        try:
            with self.connection.cursor() as cursor:
                # 插入书籍信息
                book_sql = """
                    INSERT INTO books (book_id, book_name, book_author, book_isbn, 
                                     book_publisher, book_price, book_date, book_rating)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    book_name = VALUES(book_name),
                    book_author = VALUES(book_author),
                    book_isbn = VALUES(book_isbn),
                    book_publisher = VALUES(book_publisher),
                    book_price = VALUES(book_price),
                    book_date = VALUES(book_date),
                    book_rating = VALUES(book_rating)
                """
                book_values = (
                    book_data['book_id'],
                    book_data['book_name'],
                    book_data['book_author'],
                    book_data['book_isbn'],
                    book_data['book_publisher'],
                    book_data['book_price'],
                    book_data['book_date'],
                    book_data['book_rating']
                )
                cursor.execute(book_sql, book_values)
                
                # 插入评论信息
                comment_sql = """
                    INSERT INTO book_comments 
                    (comment_id, book_id, comment_username, comment_timestamp, 
                     comment_rating, comment_content, comment_isuseful, is_positive)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    comment_username = VALUES(comment_username),
                    comment_timestamp = VALUES(comment_timestamp),
                    comment_rating = VALUES(comment_rating),
                    comment_content = VALUES(comment_content),
                    comment_isuseful = VALUES(comment_isuseful),
                    is_positive = VALUES(is_positive)
                """
                
                for comment in book_data['comment_list']:
                    comment_values = (
                        comment['comment_id'],
                        book_data['book_id'],
                        comment['comment_username'],
                        comment['comment_timestamp'],
                        comment['comment_rating'],
                        comment['comment_content'],
                        comment['comment_isuseful'],
                        comment['comment_ispositive']
                    )
                    cursor.execute(comment_sql, comment_values)
                
                self.connection.commit()
                print(f"成功保存书籍 {book_data['book_name']} 的数据")
                return True
        except Error as e:
            print(f"保存数据时出错: {e}")
            return False

    def get_book_data(self, book_id):
        try:
            with self.connection.cursor() as cursor:
                # 获取书籍信息
                cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
                book = cursor.fetchone()
                
                if book:
                    # 获取评论信息
                    cursor.execute("SELECT * FROM book_comments WHERE book_id = %s", (book_id,))
                    comments = cursor.fetchall()
                    for comment in comments:
                        comment['comment_time'] = datetime.fromtimestamp(comment['comment_timestamp'])
                    book['comment_list'] = comments
                    return book
                return None
        except Error as e:
            print(f"获取数据时出错: {e}")
            return None

    def close(self):
        if self.connection and self.connection.open:
            self.connection.close()
            print("数据库连接已关闭")