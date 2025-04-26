from bs4 import BeautifulSoup
import requests
import re

def searcher(searchtext):
    url = f"https://search.douban.com/movie/subject_search?search_text={searchtext}&cat=1002"
    resp = requests.get(url, headers=headers)
    bs = BeautifulSoup(resp.text, "html.parser")
    ori = bs.find('script', {"type": "text/javascript"}).get_text(strip=True)
    rein = re.compile(r'"url": "https://movie.douban.com/subject/(\d+)/"')
    lst = rein.findall(ori)
    return lst
