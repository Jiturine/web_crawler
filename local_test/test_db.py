#!/usr/bin/env python
# -*- coding: utf-8 -*-

from db_config import DB_CONFIG
import pymysql
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_db")

def test_connection():
    try:
        logger.info("尝试连接数据库...")
        conn = pymysql.connect(**DB_CONFIG)
        logger.info("数据库连接成功！")
        
        with conn.cursor() as cursor:
            # 测试查询
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            logger.info(f"数据库中的表: {tables}")
            
            # 测试books表
            cursor.execute("DESCRIBE books")
            books_columns = cursor.fetchall()
            logger.info(f"books表结构: {books_columns}")
            
            # 测试book_comments表
            cursor.execute("DESCRIBE book_comments")
            comments_columns = cursor.fetchall()
            logger.info(f"book_comments表结构: {comments_columns}")
            
            # 测试user_data表
            cursor.execute("DESCRIBE user_data")
            user_data_columns = cursor.fetchall()
            logger.info(f"user_data表结构: {user_data_columns}")
        
        conn.close()
        logger.info("数据库连接已关闭")
        return True
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection() 