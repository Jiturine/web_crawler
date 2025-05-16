from bs4 import BeautifulSoup
from matplotlib.pylab import f
import requests
import re
from headers import headers

class result:
    title=0,
    content=0
    

def searcher(searchtext):
    url = f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst

def searcher_full(searchtext,pagenum):
    url = f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    idlst = rein.findall(ori)
    
def searcher2(searchtext):
    url = f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    f=open('res.html','w+')
    print(bs.text,file=f)
    f.close()
    ttlst=bs.find_all('a', {"class":"title_text"})
    abr=bs.find_all('div',{"class":"meta_abstract"})
    lst = rein.findall(ori)
    lstn=[]
    # for i in range(len(lst)-1):
    #     res={
    #         "title":ttlst[i],
    #         "id":lst[i],
    #         "content":abr[i]
    #     }
    #     lstn.append(res)
    return lstn

print(searcher2("text"))