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
                print("成功连接到MySQL数据�?")
                self.create_tables()
        except Error as e:
            print(f"连接数据库时出错: {e}")

    def create_tables(self):
        """创建必要的数据表"""
        try:
            with self.connection.cursor() as cursor:
                # 创建users�?
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                # 创建books�?
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
                        book_image VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                # 创建book_comments�?
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS book_comments (
                        comment_id VARCHAR(50) PRIMARY KEY,
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

                # 创建movies�?
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movies (
                        movie_id VARCHAR(20) PRIMARY KEY,
                        movie_name VARCHAR(255) NOT NULL,
                        movie_director VARCHAR(255),
                        movie_scriptwriter VARCHAR(255),
                        movie_IMDb VARCHAR(20),
                        movie_star VARCHAR(255),
                        movie_type VARCHAR(50),
                        movie_date VARCHAR(50),
                        movie_rating VARCHAR(10),
                        movie_image VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                
                # 创建movie_comments�?
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movie_comments (
                        comment_id VARCHAR(50) PRIMARY KEY,
                        movie_id VARCHAR(20),
                        comment_username VARCHAR(255),
                        comment_timestamp INT,
                        comment_rating INT,
                        comment_content TEXT,
                        comment_isuseful INT,
                        is_positive TINYINT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """)
                self.connection.commit()
                print("数据表创建成�?")
        except Exception as e:
            print(f"创建数据表时出错: {e}")
            self.connection.rollback()

    def save_book_data(self, book_data):
        """保存书籍数据到数据库"""
        try:
            with self.connection.cursor() as cursor:
                # 插入或更新书籍信�?
                cursor.execute("""
                    INSERT INTO books (
                        book_id, book_name, book_author, book_isbn, 
                        book_publisher, book_price, book_date, book_rating, book_image
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON DUPLICATE KEY UPDATE
                        book_name = VALUES(book_name),
                        book_author = VALUES(book_author),
                        book_isbn = VALUES(book_isbn),
                        book_publisher = VALUES(book_publisher),
                        book_price = VALUES(book_price),
                        book_date = VALUES(book_date),
                        book_rating = VALUES(book_rating),
                        book_image = VALUES(book_image)
                """, (
                    book_data["book_id"],
                    book_data["book_name"],
                    book_data["book_author"],
                    book_data["book_isbn"],
                    book_data["book_publisher"],
                    book_data["book_price"],
                    book_data["book_date"],
                    book_data["book_rating"],
                    book_data["book_image"]
                ))
                
                # 插入评论数据
                for comment in book_data.get("comment_list", []):
                    cursor.execute("""
                        INSERT INTO book_comments (
                            comment_id, book_id, comment_username, comment_timestamp,
                            comment_rating, comment_content, comment_isuseful, is_positive
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON DUPLICATE KEY UPDATE
                            comment_username = VALUES(comment_username),
                            comment_timestamp = VALUES(comment_timestamp),
                            comment_rating = VALUES(comment_rating),
                            comment_content = VALUES(comment_content),
                            comment_isuseful = VALUES(comment_isuseful),
                            is_positive = VALUES(is_positive)
                    """, (
                        comment["comment_id"],
                        book_data["book_id"],
                        comment["comment_username"],
                        comment["comment_timestamp"],
                        comment["comment_rating"],
                        comment["comment_content"],
                        comment["comment_isuseful"],
                        comment["comment_ispositive"]
                    ))
                
                self.connection.commit()
                return True
        except Exception as e:
            print(f"保存数据时出�?: {e}")
            self.connection.rollback()
            return False
    
    def save_movie_data(self, movie_data):
        """保存电影数据到数据库"""
        try:
            with self.connection.cursor() as cursor:
                # 插入或更新电影信�?
                cursor.execute("""
                    INSERT INTO movies (
                        movie_id, movie_name, movie_director, movie_scriptwriter, movie_star,
                        movie_type, movie_date, movie_rating, movie_IMDb, movie_image
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON DUPLICATE KEY UPDATE
                        movie_name = VALUES(movie_name),
                        movie_director = VALUES(movie_director),
                        movie_scriptwriter = VALUES(movie_scriptwriter),
                        movie_star = VALUES(movie_star),
                        movie_type = VALUES(movie_type),
                        movie_date = VALUES(movie_date),
                        movie_rating = VALUES(movie_rating),
                        movie_IMDb = VALUES(movie_IMDb),
                        movie_image = VALUES(movie_image)
                """, (
                    movie_data["movie_id"],
                    movie_data["movie_name"],
                    movie_data["movie_director"],
                    movie_data["movie_scriptwriter"],
                    movie_data["movie_star"],
                    movie_data["movie_type"],
                    movie_data["movie_date"],
                    movie_data["movie_rating"],
                    movie_data["movie_IMDb"],
                    movie_data["movie_image"]
                ))
                
                # 插入评论数据
                for comment in movie_data.get("comment_list", []):
                    cursor.execute("""
                        INSERT INTO movie_comments (
                            comment_id, movie_id, comment_username, comment_timestamp,
                            comment_rating, comment_content, comment_isuseful, is_positive
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s
                        ) ON DUPLICATE KEY UPDATE
                            comment_username = VALUES(comment_username),
                            comment_timestamp = VALUES(comment_timestamp),
                            comment_rating = VALUES(comment_rating),
                            comment_content = VALUES(comment_content),
                            comment_isuseful = VALUES(comment_isuseful),
                            is_positive = VALUES(is_positive)
                    """, (
                        comment["comment_id"],
                        movie_data["movie_id"],
                        comment["comment_username"],
                        comment["comment_timestamp"],
                        comment["comment_rating"],
                        comment["comment_content"],
                        comment["comment_isuseful"],
                        comment["comment_ispositive"]
                    ))
                
                self.connection.commit()
                return True
        except Exception as e:
            print(f"保存数据时出�?: {e}")
            self.connection.rollback()
            return False

    def get_book_data(self, book_id):
        try:
            with self.connection.cursor() as cursor:
                # 查询书籍信息
                cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
                book = cursor.fetchone()
                
                if book:
                    # 查询评论信息
                    cursor.execute("SELECT * FROM book_comments WHERE book_id = %s", (book_id,))
                    comments = cursor.fetchall()
                    for comment in comments:
                        comment['comment_time'] = datetime.fromtimestamp(comment['comment_timestamp'])
                    book['comment_list'] = comments
                    return book
                return None
        except Error as e:
            print(f"查询数据时出�?: {e}")
            return None

    def get_movie_data(self, movie_id):
        try:
            with self.connection.cursor() as cursor:
                # 查询电影信息
                cursor.execute("SELECT * FROM movies WHERE movie_id = %s", (movie_id,))
                movie = cursor.fetchone()
                
                if movie:
                    # 处理电影信息中的datetime字段
                    if 'created_at' in movie and isinstance(movie['created_at'], datetime):
                        movie['created_at'] = movie['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    if 'updated_at' in movie and isinstance(movie['updated_at'], datetime):
                        movie['updated_at'] = movie['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 查询评论信息
                    cursor.execute("SELECT * FROM movie_comments WHERE movie_id = %s", (movie_id,))
                    comments = cursor.fetchall()
                    for comment in comments:
                        # 处理评论中的datetime字段
                        if 'comment_timestamp' in comment:
                            comment['comment_time'] = datetime.fromtimestamp(comment['comment_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                        if 'created_at' in comment and isinstance(comment['created_at'], datetime):
                            comment['created_at'] = comment['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    movie['comment_list'] = comments
                    return movie
                return None
        except Error as e:
            print(f"查询电影数据时出�?: {e}")
            return None

    def close(self):
        """关闭数据库连�?"""
        if self.connection:
            self.connection.close()
            print("MySQL数据库连接已关闭")

    def get_user_by_username(self, username):
        """根据用户名查找用�?"""
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                sql = "SELECT * FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                return cursor.fetchone()
        except Exception as e:
            print(f"根据用户名查找用户时出错: {e}")
            return None

    def create_user(self, username, password):
        """创建新用�?"""
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
                cursor.execute(sql, (username, password))
                self.connection.commit()
                return True
        except Exception as e:
            print(f"创建用户时出�?: {e}")
            self.connection.rollback()
            return False

    def execute_query(self, sql, params=None):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            try:
                result = cursor.fetchall()
                return result
            except:
                return None
