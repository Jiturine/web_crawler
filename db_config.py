#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql

DB_CONFIG = {
    'host': 'localhost',#服务器IP地址
    'port': 3306,#端口
    'user': 'root',#数据库用户名
    'password': 'zzy051007',#数据库密码
    'database': 'web_crawler',#数据库名
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
