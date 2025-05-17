#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql

DB_CONFIG = {
    'host': 'localhost',#服务器IP地址
    'port': 3306,#端口
    'user': 'root',
    'password': '123456',
    'database': 'web_crawler',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
} 
