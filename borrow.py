import requests
from bs4 import BeautifulSoup

session = requests.Session()
ID, PWD = 'STUDENT_ID', 'PASSWORD'


def get_page(url):
    response = session.get(url)
    response.encoding = 'utf8'
    return BeautifulSoup(response.text)


def process(soup):
    results = soup.find_all(attrs={'cellspacing': '2'})
    for result in results:
        for row in result.find_all('tr'):
            if row.has_attr('class'):
                continue
            col = row.find_all('td')
            try:
                name = col[1].string.strip()
                deadline = '%s %s' % (col[3].string, col[4].string)
                reason = col[8].string.strip()
                print('%s\n%s\t%s' % (name, deadline, reason))
            except:
                print('%s\n%s' % (name, deadline))


def login(login_url):
    soup = get_page(login_url)
    form = soup.find_all('form')[0]
    action = form['action']
    data = {
        'bor_id': ID,
        'bor_verification': PWD,
        'ssl_flag': 'Y',
        'func': 'login',
    }
    response = session.post(action, data=data)
    response.encoding = 'utf8'
    soup = get_page(response.url + '?func=bor-renew-all&adm_library=TOP51')
    process(soup)


def start():
    soup = get_page('http://webpac.lib.nthu.edu.tw/F?RN=842953775')
    bar = soup.findAll(attrs={'title': 'Enter your username and password'})[0]
    login(bar['href'])

start()
