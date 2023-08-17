import requests
import bs4
import pickle
import logging
import tabulate
from decouple import config


logger = logging.getLogger("idfarm")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s %(levelname)s:%(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)


search_uri = "/bbs/board.php?bo_table=hsr&sca=%EC%95%84%EC%9D%B4%EB%94%94"

def do_login(s: requests.session):
    login_response = s.post(config("IDFARM_LOGIN_URL"), data=LOGIN_DATA)
    login_soup = bs4.BeautifulSoup(login_response.text, 'html.parser')

    username_span = login_soup.select_one("span.user-name")
    if username_span == None:
        logger.error("로그인 실패")
        return False
    
    if username_span.text== LOGIN_DATA["mb_id"]:
        logger.info("로그인 성공")
        with open("cookies","wb") as cookie_file:
            pickle.dump(s.cookies, cookie_file)
        return True

    logger.error("유저명이 일치하지 않습니다")
    logger.error("로그인 실패")
    return False
    
def do_cookies_validation(s: requests.session):
    main_page_response = s.get(config("IDFARM_MAIN_URL"))
    main_page_soup = bs4.BeautifulSoup(main_page_response.text, 'html.parser')
    username_span = main_page_soup.select_one("span.user-name")

    if username_span == None:
        logger.error("쿠키가 유효하지 않습니다")
        return False
    elif username_span.text == config("IDFARM_ID"):
        logger.debug("쿠키가 유효합니다")
        return True
    else:
        logger.error("유저명이 일치하지 않습니다")
        return False

LOGIN_DATA = {
    "mb_id" : config("IDFARM_ID"),
    "mb_password": config("IDFARM_PW"),
}

s = requests.session()
cached_cookies = pickle.load(open("cookies", 'rb'))
s.cookies.update(cached_cookies)

if do_cookies_validation(s) == False:
    do_login(s)


GAME_CODE = config("GAME_CODE")
SEARCH_CATEGORY = config("SEARCH_CATEGORY")
ACCOUNT_TYPE = config("ACCOUNT_TYPE", default="")
ACCOUNT_SOURCE = config("ACCOUNT_SOURCE", default="")
MIN_PRICE = config("MIN_PRICE", default="")
MAX_PRICE = config("MAX_PRICE", default="")
SORT_TYPE = config("SORT_TYPE", default="all")

out_table = [["구분", "서버", "제목", "가격", "날짜"]]

for page_no in range(10, 0, -1):
    search_page_uri = f"/bbs/board.php?bo_table={GAME_CODE}&sca={SEARCH_CATEGORY}&stx=&wr_8=&wr_80={MIN_PRICE}%2C{MAX_PRICE}&wr_2={ACCOUNT_TYPE}&wr_5=&wr_3=&wr_30=&wr_6={ACCOUNT_SOURCE}&wr_15=&wr_7=&wr_16=&sorttype={SORT_TYPE}&ordertype=&scl=2315&page={page_no}"
    search_page_response = s.get(config("IDFARM_MAIN_URL") + search_page_uri)
    logger.debug(search_page_response.url)
    search_page_soup = bs4.BeautifulSoup(search_page_response.text, 'html.parser')

    uls = search_page_soup.select_one("div.table__grid--cont.premium").select("ul")
    uls.reverse()
    for ul in uls:
        if ul.has_attr("onclick") == False:
            continue

        career = ul.select_one("li.career").text.strip()
        # game = ul.select_one("li.game").text
        region = ul.select_one("li.tit.second > em").text.strip()
        title = ul.select_one("li.tit.second > span").text.strip()
        price = ul.select_one('li.price').text.strip()
        date = ul.select_one("li.date").text.strip()
        link = ul["onclick"].split("'")[1]

        out_table.append([career, region, title, price, date])

logger.debug(out_table)
print(tabulate.tabulate(out_table, headers="firstrow", tablefmt="fancy_grid", colalign=("left","left","left","right","left")))
