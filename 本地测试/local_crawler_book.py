from urllib import response

from pandas import Timestamp
from bs4 import BeautifulSoup
import requests
import time
import re
from headers import headers
import sys
import os

from sqlalchemy import Null

man_text='''
request format: (app_runner) <book_id> <comment_amount> [options]

Options:
    --time: sort the comments by time
    --hot:  sort the comments by isusefuls
    [
       -A/-B/-C:(Under isuseful mode only) Only show the good/middle/bad comments
    ]
    --help: show this help message

    YOU CAN DIRECTLY READ THE HELP MESSAGE WITHOUT PROVIDING ID AND AMOUNT

    if no sorter option provided, this program will run on default mode: sort by isusefuls, all comments shown
'''

default_lister={
    "id":"",
    "comment_amount":0,
    "sorter":"score",
    "percentage":False,
    "percentage_selector":"h"
}

class comment:
    __slots__=["comment_id","comment_username","comment_timestamp","comment_isuseful","comment_content","comment_rating"]

    def __init__(self):
        comment_id= -1,
        comment_username= "NULL",
        comment_timestamp= "NULL",
        comment_rating=-1,
        comment_content= "NULL",
        comment_isuseful= -1,


arg_available=["--time","--hot","--help","-A","-B","-C"]
def parser(args=sys.agrv[1:])->list:
    if len(args)<1:
        raise ValueError(f"no arguments provided,please check the help message below\n{man_text}")   
    if "--help" in args:
        print(man_text)
        sys.exit(0)
    res=default_lister
    res["id"]=args[0]
    res["comment_amount"]=args[1]
    options=args[2:]
    percentage_count=0
    sorter_count=0
    for arg in args:
        if arg not in arg_available:
            raise ValueError(f"invalid argument {arg}, please check the help message below\n{man_text}")
        else:
            if arg=="--time":
                res["sorter"]="time"
                sorter_count+=1
            if arg=="--hot":
                sorter_count+=1
            if arg=="-A":
                res["percentage"]=True
                res["percentage_selector"]="h"
                percentage_count+=1
            if arg=="-B":
                res["percentage"]=True
                res["percentage_selector"]="m"
                percentage_count+=1
            if arg=="-C":
                res["percentage"]=True
                res["percentage_selector"]="l"
                percentage_count+=1
    if(percentage_count>1 or sorter_count>1):
        raise ValueError("Conf, please check the help message below\n{man_text}")
            
    if(res["percentage"] and (res["sorter"]=="time")):
        raise ValueError(f"invalid argument combination, please check the help message below\n{man_text}")
    return res

def book_crawler(option:dict)->list:
    id=option["id"]
    amount=option["comment_amount"]
    sorter=option["sorter"]
    pager=0
    percent_type=""
    if option["percentage"]:
        percent_type=f"?percent_type={option["percentage_selector"]}&"
    comment_list=[]
    counter=0
    pagemax=amount//20+(amount%20)%1
    for pager in range(pagemax):
        try:
            url=f"https://book.douban.com/subject/{id}/comments/{percent_type}limit={pager*20}&status=P&sort={sorter}"
            response=requests.get(url,headers=headers)
            if response!=200:
                print(f"Cannot get page {pager+1},switch to next page")
                pager+=1
                continue
            bsoup=BeautifulSoup(response.text,"html.parser")
            comment_items = bsoup.find_all("li", {"class": "comment-item"})
            for comment_item in comment_items:
                    while(counter<amount):
                        try:
                            comment_id = comment_item["data-cid"]
                        except KeyError:
                            comment_id = f"id_missed_comment_{counter}"
                            
                        try:
                            avatar = comment_item.find("div", {"class": "avatar"})
                            comment_username = avatar.find("a")["title"]
                        except (AttributeError, KeyError):
                            pass
                            
                        try:
                            comment = comment_item.find("div", {"class": "comment"})
                            comment_isuseful = int(comment.find("span", {"class": "vote-count"}).get_text())
                        except (AttributeError, ValueError):
                            pass
                            
                        try:
                            comment_time_str = comment.find("a", {"class": "comment-time"}).get_text()
                            comment_time = time.strptime(comment_time_str, "%Y-%m-%d %H:%M:%S")
                            comment_timestamp = int(time.mktime(comment_time))
                        except (AttributeError, ValueError):
                            pass
                            
                        try:
                            comment_content = comment.find("p", {"class": "comment-content"}).get_text().strip()
                        except AttributeError:
                            pass
                            
                        try:
                            match = re.search(r'allstar(\d{2})', str(comment.find("span", {"class": "comment-info"})))
                            comment_rating = int((match.group(1))) // 10 if match else 0
                        except (AttributeError, ValueError):
                            pass

                        try:
                            res=comment()
                            res.comment_id = comment_id
                            res.comment_username = comment_username
                            res.comment_isuseful = comment_isuseful
                            res.comment_time_str = comment_time_str
                            res.comment_timestamp = comment_timestamp
                            res.comment_content = comment_content
                            res.comment_rating = comment_rating
                            comment_list.append(res.__dict__)
                        except Exception as e:
                            print(f"Error occurred while saving data for comment {comment_id}: {e}")
                        
        except:
            print(f"Error occurred while fetching data from page {pager+1}")
    return comment_list

if __name__ == "__main__":
    args=parser()
    f=open('res'+time.timestamp()+'.json', 'w+')
    f.dump(book_crawler(args))
    
