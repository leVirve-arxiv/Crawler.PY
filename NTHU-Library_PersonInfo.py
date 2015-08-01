import re
import json
import requests
import urllib.parse
from bs4 import BeautifulSoup

__author__ = 'salas'


def get_page(url, soupful=True):
    resp = requests.get(url)
    resp.encoding = 'utf8'

    return BeautifulSoup(resp.text, 'lxml') if soupful else resp


def post_page(url, **kwargs):
    return requests.post(url, **kwargs)


class NotLoginException(Exception):
    pass


class UserPayload:

    def __init__(self, account, password):
        self.account = account
        self.password = password

    def to_dict(self):
        return {
            'bor_id': self.account,
            'bor_verification': self.password,
            'func': 'login',
            'ssl_flag': 'Y',
        }

class NTHULibrary():

    home = 'http://webpac.lib.nthu.edu.tw/F/'

    def __init__(self, user):
        self.user = user
        self._session_url = ''
        self.is_login = self._login()

    def _login(self):
        soup = get_page(urllib.parse.urljoin(self.home, '?func=file&file_name=login1'))
        login_url = soup.find('form').attrs.get('action')

        resp = post_page(login_url, data=self.user.to_dict())
        resp.encoding = 'utf-8'
        self._session_url = resp.url
        return '您已登入' in resp.text

    def get_info(self):
        if not self.is_login:
            raise NotLoginException
        soup = get_page(urllib.parse.urljoin(self._session_url, '?func=BOR-INFO'))

        return self._parse(soup)

    def _parse(self, soup):
        result = {}

        result['name'] = soup.find('font', attrs={'size': '4'}).text

        tables = soup.find_all('table', attrs={'cellspacing': '2'})

        # 圖書館流通狀態
        status = {}
        for row in tables[0].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip()
            val = cols[1].find('a').text.strip()
            link = re.findall("'(.*?)'", cols[1].find('a').attrs.get('href'))[0]
            status[key] = (val, link)

        person = {}
        # 聯絡資料
        for row in tables[1].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip() or '地址'
            val = cols[1].text.strip()
            person[key] = person[key] + val if key in person else val

        # 管理資訊
        manage = {}
        for row in tables[2].find_all('tr'):
            cols = [e for e in row.children if str(e).strip()]
            key = cols[0].text.strip()
            val = cols[1].text.strip()
            if key == '讀者權限資料':
                val = re.findall("borstatus='(.*)'", val)[0]
            manage[key] = val

        result['user'] = person
        result['user']['manage'] = manage
        result['status'] = status

        return result
        # return json.dumps(result, indent=2, ensure_ascii=False)

    def get_current_bowrrow(self, res):
        soup = get_page(res['status']['目前借閱中清單'][1])
        table = soup.find('table', attrs={'cellspacing': '2', 'border': '0'})
        books = []
        for row in table.find_all('tr')[1:]:
            cols = [e for e in row.children if str(e).strip()]
            meta_dl = re.findall('(.*?)(\d+)', cols[5].text)[0]
            pretty_title = cols[3].text
            if cols[3].text[-1] is '/':
                pretty_title = pretty_title[:-1].strip()

            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[2].text,
                'title': pretty_title,
                'publish_year': cols[4].text,
                'deadline_status': meta_dl[0] if len(meta_dl) == 2 else None,
                'deadline': meta_dl[1] if len(meta_dl) == 2 else meta_dl[0],
                'publish_cost': cols[7].text,
                'branch': cols[8].text,
                'call_number': cols[9].text
            }
            books.append(book)
        return books

    def get_bowrrow_history(self, res):
        soup = get_page(res['status']['借閱歷史清單'][1])
        table = soup.find('table', attrs={'cellspacing': '2', 'border': '0'})

        books = []
        for row in table.find_all('tr')[1:]:
            cols = [e for e in row.children if str(e).strip()]
            meta_dl = re.findall('(.*?)(\d+)', cols[4].text)[0]
            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[1].text,
                'title': cols[2].text,
                'publish_year': cols[3].text,
                'deadline_status': meta_dl[0] if len(meta_dl) == 2 else None,
                'deadline': meta_dl[1] if len(meta_dl) == 2 else meta_dl[0],
                'borrow_time': cols[6].text + ' ' + re.findall('>(.*?)<', str(cols[7]))[0],
                'branch': cols[8].text
            }
            books.append(book)
        return books

    def get_current_booking(self):
        pass

    def get_hold_booking(self):
        pass

    def get_booking_history(self, res):
        soup = get_page(res['status']['預約歷史清單'][1])
        table = soup.find('table', attrs={'cellspacing': '2', 'border': '0'})

        books = []
        for row in table.find_all('tr')[1:]:
            cols = [e for e in row.children if str(e).strip()]
            pretty_title = cols[2].text
            if cols[2].text[-1] is '/':
                pretty_title = pretty_title[:-1].strip()
            book = {
                'link': cols[0].find('a').attrs.get('href'),
                'author': cols[1].text,
                'title': cols[2].text,
                'publish_year': cols[3].text,
                'history_date': cols[4].text,
                'booking_date': cols[5].text,
                'booking_valid': cols[6].text,
                'book_return': cols[7].text,
                'branch': cols[8].text,
                'call_number': cols[9].text,
                'branch_take': cols[10].text,
                'book_status': cols[11].text
            }
            books.append(book)
        return books

if __name__ == '__main__':
    user = UserPayload('ID', 'PWD')
    libary = NTHULibrary(user)

    functions = {
        'info': libary.get_info(),
        'borrow-history': libary.get_bowrrow_history,
        'current-borrow': libary.get_current_bowrrow,
        'booking-history': libary.get_booking_history,
    }


    # get all data !!!!
    person_data = {}

    result = functions['info']

    person_data['personal'] = result
    person_data['借閱歷史'] = functions['borrow-history'](result)
    person_data['借閱中'] = functions['current-borrow'](result)
    person_data['預約紀錄'] = functions['booking-history'](result)

    f = open('my-lib-ultimate-data.json', 'w', encoding='utf8')
    json.dump(person_data, f, indent=2, ensure_ascii=False)
