#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql

DB_CONFIG = {
    'host': '106.52.139.242',#服务器IP地址
    'port': 8000,#端口
    'user': 'root',#数据库用户名
    'password': '123456',#数据库密码
    'database': 'web_crawler',#数据库名
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
} 
