headers = {
    "user-agent": "MOzilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0",
    "cookie": 'viewed="1007305"; bid=fWQ0-FZntE4; _vwo_uuid_v2=D52527652226A007630C83C93D9A0891D|b950b2128fc09ca46a4593f813740ff8; push_noty_num=0; push_doumail_num=0; __utmz=30149280.1743048911.3.2.utmcsr=search.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/book/subject_search; ll="118318"; _pk_id.100001.4cf6=ca641e730c6671ac.1743594698.; dbcl2="243782112:sUEI3lkhlrw"; __utmz=223695111.1744802466.3.2.utmcsr=book.douban.com|utmccn=(referral)|utmcmd=referral|utmcct=/subject/2567698/comments/; ck=uSSJ; ap_v=0,6.0; frodotk_db="c16e116bdf129516444a34439d37bf42"; __utma=30149280.6038330.1742993301.1744802426.1745670627.7; __utmc=30149280; __utmc=223695111; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1745672561%2C%22https%3A%2F%2Fsearch.douban.com%2Fmovie%2Fsubject_search%3Fsearch_text%3D%E6%B5%81%E6%B5%AA%E5%9C%B0%E7%90%83%26cat%3D1002%22%5D; _pk_ses.100001.4cf6=1; __utmv=30149280.24378; __utmb=30149280.9.10.1745670627; __utma=223695111.483568495.1743594699.1745670627.1745672583.5; __utmb=223695111.0.10.1745672583',
}

import requests
from fake_useragent import UserAgent
def get_dynamicheaders(target_url: str) -> dict:
    session = requests.Session()
    ua = UserAgent()
    user_agent = ua.random

    try:
        response = session.get(
            target_url,
            headers={'User-Agent': user_agent},
            timeout=12
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to get headers: {e}")
        return {}
    cookies_str = '; '.join([f"{c.name}={c.value}" for c in session.cookies])

    return {
        'User-Agent': user_agent,
        'Cookie': cookies_str
    }
