import requests
import bs4
import pickle
import logging
import tabulate
from decouple import Config, RepositoryEnv
import logging
import logging.config


DOTENV_FILE = "./.env"
env_config = Config(RepositoryEnv(DOTENV_FILE))

logging.config.fileConfig('./logging.conf')
login_logger = logging.getLogger("idfarm.login")
cookies_logger = logging.getLogger("idfarm.cookie")
search_logger = logging.getLogger("idfarm.search")


IDFARM_MAIN_URL = env_config.get("IDFARM_MAIN_URL")
IDFARM_LOGIN_URL = env_config.get("IDFARM_LOGIN_URL")
IDFARM_ID = env_config.get("IDFARM_ID")
IDFARM_PW = env_config.get("IDFARM_PW")

def do_login(s: requests.session):
    LOGIN_DATA = {
        "mb_id" : IDFARM_ID,
        "mb_password": IDFARM_PW,
    }

    login_response = s.post(IDFARM_LOGIN_URL, data=LOGIN_DATA)
    login_soup = bs4.BeautifulSoup(login_response.text, 'html.parser')
    username_span = login_soup.select_one("span.user-name")
    if username_span == None:
        login_logger.info("로그인 실패, 로그인 없이 진행합니다")
        return False
    
    if username_span.text== LOGIN_DATA["mb_id"]:
        login_logger.info("로그인 성공")
        with open("cookies","wb") as cookie_file:
            pickle.dump(s.cookies, cookie_file)
        return True

    login_logger.error("유저명이 일치하지 않습니다")
    return False
    
def do_cookies_validation(s: requests.session):
    main_page_response = s.get(IDFARM_MAIN_URL)
    main_page_soup = bs4.BeautifulSoup(main_page_response.text, 'html.parser')
    username_span = main_page_soup.select_one("span.user-name")

    if username_span == None:
        cookies_logger.error("쿠키가 유효하지 않습니다")
        return False
    elif username_span.text == IDFARM_ID:
        cookies_logger.info("쿠키가 유효합니다")
        return True
    else:
        cookies_logger.error("유저명이 일치하지 않습니다")
        return False

s = requests.session()

try:
    cached_cookies = pickle.load(open("cookies", 'rb'))
except:
    cookies_logger.debug("쿠키가 존재하지 않습니다")

s.cookies.update(cached_cookies)
if do_cookies_validation(s) == False:
    logged_in = do_login(s)


GAME_CODE = env_config.get("GAME_CODE")
SEARCH_CATEGORY = env_config.get("SEARCH_CATEGORY")
ACCOUNT_TYPE = env_config.get("ACCOUNT_TYPE", default="")
ACCOUNT_SOURCE = env_config.get("ACCOUNT_SOURCE", default="")
MIN_PRICE = env_config.get("MIN_PRICE", default="0")
MAX_PRICE = env_config.get("MAX_PRICE", default="9999999")
SORT_TYPE = env_config.get("SORT_TYPE", default="all")
FIRST_PAGE = env_config.get("FIRST_PAGE", default="1", cast=int)
LAST_PAGE = env_config.get("LAST_PAGE", default="10", cast=int)

out_table = [["구분", "서버", "제목", "가격", "날짜"]]

for page_no in range(LAST_PAGE, FIRST_PAGE - 1, -1):
    SEARCH_PAGE_URI = (
        "/bbs/board.php?"
        f"bo_table={GAME_CODE}"
        f"&sca={SEARCH_CATEGORY}"
        f"&stx="
        f"&wr_8="
        f"&wr_80={MIN_PRICE},{MAX_PRICE}"
        f"&wr_2={ACCOUNT_TYPE}"
        f"&wr_5="
        f"&wr_3="
        f"&wr_30="
        f"&wr_6={ACCOUNT_SOURCE}"
        f"&wr_15="
        f"&wr_7="
        f"&wr_16="
        f"&sorttype={SORT_TYPE}"
        f"&ordertype="
        f"&scl=2315"
        f"&page={page_no}"
    )

    search_page_response = s.get(IDFARM_MAIN_URL + SEARCH_PAGE_URI)
    search_logger.debug(search_page_response.url)
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

search_logger.debug(out_table)
print(tabulate.tabulate(out_table, headers="firstrow", tablefmt="fancy_grid", colalign=("left","left","left","right","left")))
