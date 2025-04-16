import sys
from bs4 import BeautifulSoup
import requests
import json
import csv
import re
import urllib

args=sys.argv[1:]
headers={
        "user-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
        "cookie":''
    }


def searcher(searchtext):
    url=f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp=requests.get(url,headers=headers)
    bs=BeautifulSoup(resp.text,"html.parser")
    
    len_of_classname=4
    len_of_namecontent=6
    prefix="sc-"

    divs=bs.find_all('div')
    tag4=[div for div in divs if len(div['class'])==len_of_classname]
    movies=[div for div in tag4 if ((div['class'])[0].startswith(prefix) and (div['class'])[2].startswith(prefix))]
    links=[]
    for movie in movies:
        HRefLink=movie.find("a")["href"]
        links.append(HRefLink)
    return links

def infogetter(link):
    resp=requests.get(link,headers=headers)
    bs=BeautifulSoup(resp.text,"html.parser")
    Movie_Name=bs.find("span",{"property":"v:itemreviewed"}).get_text(strip=True)
    Movie_Year=bs.find("span",{"class":"year"}).get_text()
    Movie_AverageScore=bs.find("strong",{"class":"ll rating_num"}).get_text()
    Movie_ID=re.search(r'/subject/(\d+)/',link).group(1)
    Movie_ShortComments=[]
    Info={
        "Movie_Name":Movie_Name,
        "Movie_ID":Movie_ID,
        "Movie_Year":Movie_Year,
        "Movie_AverageScore":Movie_AverageScore,
        "Movie_ShortComments":Movie_ShortComments
    }
    return Info

def commentgetter(Movie_Info,CommentCount):
    count=0
    for i in range((CommentCount//20)-1):
            url=f"https://movie.douban.com/subject/{Movie_Info["Movie_ID"]}/comments?start={i*20}&limit=20&status=P&sort=new_score"
            resp=requests.get(url,headers=headers)
            bs=BeautifulSoup(resp.text,"html.parser")
            items=bs.find_all('div',{"class":"comment-item"})
            for item in items:
                while(count<=CommentCount):
                    Comment_ID=item["data-cid"]
                    date_str=item.find('a',{"class":"comment-time"}).get_text()
                    info=item.find('span',{"class":"comment-info"})
                    Comment_Content=item.find('span',{"class":"short"}).get_text(strip=True)
                    Comment_UserName=((item.find('div',{"class":"avatar"})).find("a"))["title"]
                    stars=item.find('span',{"class": lambda x:x and x.startswith('allstar')})['class'][1]
                    isuseful=info.find('span',{"class":"votes vote-count"}).get_text(strip=True)
                    rating=int(stars[-2])
                    Comment={
                        "Comment_UserName":Comment_UserName,
                        "Comment_ID":Comment_ID,
                        "Comment_Time":date_str,
                        "Comment_Content":Comment_Content,
                        "Comment_IsUseful":isuseful,
                        "Comment_Rating":rating
                    }
                    Movie_Info["Movie_ShortComments"].append(Comment)
                    count+=1
    return Movie_Info


def main():
    searchres=searcher(args[0])
    infos=[]
    for res in searchres:
        ori=infogetter(res)
        ori=commentgetter(ori,args[1])
        infos.append(ori)
    with open('output.json','w+')as f:
        json.dump(infos)


if __name__=="__main__" :
    main()                         






