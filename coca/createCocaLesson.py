# encoding: utf-8

from pymongo import MongoClient
from jinja2 import Template
import codecs
import re
import os.path
import requests

DB = MongoClient('localhost', 27017)['ce']

class CogApi(object):
    def __init__(self, host='127.0.0.1', port=3000):
        self.base_url = 'http://' + host + ':' + str(port) + '/api/1.0'
        self.http = requests.Session()

    def login(self, username, password):
        data = {
            'origin': 'cogen',
            'username': username,
            'password': password
        }
        res = self.http.post(self.base_url+'/auth/login', json=data)
        print('User has logined.')
        res_json = res.json()
        self.http.headers.update({'authorization': res_json['token']})

    def is_logined(self):
        return self.http.headers.get('authorization') != None

    def create_lesson(self, lessonData):
        if not self.is_logined:
            print("Please login firstly")
            return
        res = self.http.post(self.base_url+'/lessons', json=lessonData)
        return res.json()


class CocaLessonFactory(object):
    def __init__(self):
        self.content_tpl = self._get_content_tpl()
        self.coca_words = self._get_coca_words()
        self.api_client = CogApi()
        self.api_client.login('admin', 'studycogen')

    def _get_content_tpl(self):
        tplfilepath = os.path.join(os.path.dirname(__file__), 'content_template.htm')
        tplfile = codecs.open(tplfilepath, encoding='utf8')
        tplstr = tplfile.read()
        return Template(tplstr)

    def _get_coca_words(self):
        filepath = os.path.join(os.path.dirname(__file__), 'coca_words.txt')
        cfile = codecs.open(filepath, encoding='utf8')
        words = [line.strip() for line in cfile.readlines() if line]
        return words

    def create_lesson(self, nth):
        lesson = {}
        start_idx = nth*10 - 9
        end_idx = start_idx + 9
        media_path = "/media/coca_audios/COCAIII_%04d-%04d.mp3" % (start_idx, end_idx)
        media = DB['media'].find_one({'path': media_path})
        lesson['mediaId'] = str(media['_id'])
        prestart_idx, prend_idx = start_idx - 10, start_idx - 1
        words = []
        if prestart_idx > 0:
            premedia_path = "/media/coca_audios/COCAIII_%04d-%04d.mp3" % (prestart_idx, prend_idx)
            premedia = DB['media'].find_one({'path': premedia_path})
            lesson['mediaId2'] = str(premedia['_id'])
            words = self.coca_words[prestart_idx-1:prend_idx+1]

        lesson['title'] = u'Day %d🍬 %04d-%04d' % (nth, start_idx, end_idx)
        lesson['content'] = self.generate_content(words)
        res = self.api_client.create_lesson(lesson)
        print('Lesson created: ' + res['_id'])
        return res

    def delete_lesson(self, nth):
        start_idx, end_idx = nth*10 - 9, nth*10
        title = u'Day %d🍬 %04d-%04d' % (nth, start_idx, end_idx)
        DB['lessons'].delete_one({'title': title})

    def generate_content(self, words):
        res = DB['words'].find({'word': {'$in': words}}, ['word', 'phonetic_us', 'phonetic_uk'])
        # order words
        wordict_list = [wd for wd in res]
        for wd in wordict_list:
            wd['seq'] = words.index(wd['word'])
        wordict_list.sort(key=lambda x: x['seq'])

        content = self.content_tpl.render(words=wordict_list)
        content = re.sub('\r|\n', '', content)
        content = re.sub(r'\s\s+', ' ', content)
        return content

if __name__ == '__main__':
    clf = CocaLessonFactory()
    for i in range(100):
        clf.create_lesson(i+1)
    