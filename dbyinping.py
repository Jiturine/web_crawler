import sys
from bs4 import BeautifulSoup
import requests
import json
import csv
import re
import urllib

args = sys.argv[1:]
headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    "cookie": 'll="118318"; bid=si_BtTorNRE; ap_v=0,6.0; __utma=30149280.177445380.1744800338.1744800338.1744800338.1; __utmc=30149280; __utmz=30149280.1744800338.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _vwo_uuid_v2=D6D32BA365DDF5C14D3FA9AD0EA368AD8|d969f70347666474813ce9cd08cc3eb0; __yadk_uid=Ephz73OMf57XzBwPE0YkmRUmloCrL3XW; dbcl2="288357659:D8uuhFn+Jgw"; ck=gTKH; push_noty_num=0; push_doumail_num=0'
}


def searcher(searchtext):
    url = f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst


def infogetter(link):
    resp = requests.get(link, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    Movie_Name = bs.find(
        "span", {"property": "v:itemreviewed"}).get_text(strip=True)
    Movie_Year = bs.find("span", {"class": "year"}).get_text()
    Movie_AverageScore = bs.find(
        "strong", {"class": "ll rating_num"}).get_text()
    Movie_ID = re.search(r'/subject/(\d+)/', link).group(1)
    Movie_ShortComments = []
    Info = {
        "Movie_Name": Movie_Name,
        "Movie_ID": Movie_ID,
        "Movie_Year": Movie_Year,
        "Movie_AverageScore": Movie_AverageScore,
        "Movie_ShortComments": Movie_ShortComments
    }
    return Info


def commentgetter(Movie_ID, CommentCount):
    count = 0
    comments = []
    for i in range((CommentCount//20)-1):
        url = f"https://movie.douban.com/subject/{Movie_ID}/comments?start={i*20}&limit=20&status=P&sort=new_score"
        resp = requests.get(url, headers=headers)
        bs = BeautifulSoup(resp.text, "html.parser")
        items = bs.find_all('div', {"class": "comment-item"})

        for item in items:
            while (count <= CommentCount):
                Comment_ID = item["data-cid"]
                date_str = item.find('a', {"class": "comment-time"}).get_text()
                info = item.find('span', {"class": "comment-info"})
                Comment_Content = item.find(
                    'span', {"class": "short"}).get_text(strip=True)
                Comment_UserName = (
                    (item.find('div', {"class": "avatar"})).find("a"))["title"]
                stars = item.find('span', {"class": lambda x: x and x.startswith('allstar')})[
                    'class'][1]
                isuseful = info.find(
                    'span', {"class": "votes vote-count"}).get_text(strip=True)
                rating = int(stars[-2])
                Comment = {
                    "Comment_UserName": Comment_UserName,
                    "Comment_ID": Comment_ID,
                    "Comment_Time": date_str,
                    "Comment_Content": Comment_Content,
                    "Comment_IsUseful": isuseful,
                    "Comment_Rating": rating
                }
                comments.append(Comment)
                count += 1
    return comments


url = f"https://movie.douban.com/subject/34780991/comments?start=20&limit=20&status=P&sort=new_score"
resp = requests.get(url, headers=headers)
bs = BeautifulSoup(resp.text, "html.parser")
