# encoding=utf8

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import re
import time

DB = MongoClient('localhost', 27017)['ce']

def crawl_word_by_bing(word):
    url = 'https://cn.bing.com/dict/search?q=%s' % word
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    prus = soup.find('div', class_='hd_prUS')
    phonicus= _find_phonic(prus.string) if prus else None
    pruk = soup.find('div', class_='hd_pr')
    phonicuk = _find_phonic(pruk.string) if pruk else None
    return phonicus, phonicuk

EXTRACT_PHONIC_PATTERN = re.compile(r'\[(.+)\]')
def _find_phonic(text):
    matchObj = EXTRACT_PHONIC_PATTERN.search(text)
    return matchObj.group(1) if matchObj else None

def crawl_word_by_youdao(word):
    url = 'http://dict.youdao.com/w/%s/' % word
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    pr = soup.find_all('span', class_='phonetic')
    phonicuk = _find_phonic(pr[0].string) if pr else None
    phonicus = _find_phonic(pr[1].string) if (pr and len(pr)>1) else None
    return phonicus, phonicuk


def main():
    cursor = DB.words.find({'phonetic_uk': None}, ['word'])
    for word in cursor:
        print 'crawling phonetic for %s' % word['word']
        us, uk = crawl_word_by_youdao(word['word'])
        if us or uk:
            DB.words.update_one({'word':word['word']}, {'$set': 
                                { 'phonetic_us': us, 'phonetic_uk': uk }})
        time.sleep(1)

if __name__ == '__main__':
    main()