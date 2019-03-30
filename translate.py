#!/bin/python3
import sublime
import sublime_plugin
import hashlib
import urllib
import random
import threading
import json
import bs4
from bs4 import BeautifulSoup
import sys
import uuid
import requests
import hashlib
import time


def get_setting(key, defVal):
    return sublime.load_settings("Translate-CN.sublime-settings").get(key, defVal)


class TranslateTextCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sels = self.view.sel()
        translate_whole_word = get_setting("translate_whole_word", False)
        for sel in sels:
            if translate_whole_word:
                wholeWord = self.view.word(sel)
                words = self.view.substr(wholeWord)
            else:
                words = self.view.substr(sel)
            # print(words)
            if words != '':
                if get_setting("ciba", False):
                    thread = CibaApiCall(words)
                else:
                    thread = YouDaoApiCall(words)
                thread.start()


class TranslateInputCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        sels = self.view.sel()
        sublime.active_window().show_input_panel('尚未佩妥剑  转眼便江湖  愿历尽千帆  归来仍少年 ', '', self.on_done, None,
                                                 self.on_cancel)

    def on_done(self, words):
        if words != '':
            if get_setting("ciba", False):
                thread = CibaApiCall(words)
            else:
                thread = YouDaoApiCall(words)
            thread.start()

    def on_cancel():
        pass


class YouDaoApiCall(threading.Thread):
    def __init__(self, words):
        self.words = words
        self.appKey = get_setting("appKey", "")
        self.secretKey = get_setting("secretKey", "")
        self.timeout = 5
        threading.Thread.__init__(self)

    def run(self):
        data = {}

        def truncate(q):
            if q is None:
                return None
            size = len(q)
            return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]

        def do_request(data):
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            return requests.post(YOUDAO_URL, data=data, headers=headers)

        def encrypt(signStr):
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(signStr.encode('utf-8'))
            return hash_algorithm.hexdigest()

        YOUDAO_URL = 'http://openapi.youdao.com/api'
        APP_KEY = self.appKey
        APP_SECRET = self.secretKey
        q = self.words
        data['from'] = 'auto'
        data['to'] = 'auto'
        data['signType'] = 'v3'
        curtime = str(int(time.time()))
        data['curtime'] = curtime
        salt = str(uuid.uuid1())
        signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
        sign = encrypt(signStr)
        data['appKey'] = self.appKey
        secretKey = self.secretKey
        data['q'] = q
        data['salt'] = salt
        data['sign'] = sign
        sign = hashlib.sha256(sign.encode('utf-8')).hexdigest()
        try:
            response = do_request(data)
            result = response.content.decode('utf-8')
            if q.endswith(('.', '?', '!', ',')):
                self.parse(result, 0)
            else:
                self.parse(result, 1)
            return
        except Exception as e:
            sublime.error_message(str(e))

    def parse(self, result, flag):
        jsonObj = json.loads(result)
        try:
            if flag == 1:
                resArr = jsonObj['basic']['explains']
            else:
                resArr = jsonObj['translation']
        except Exception as e:
            resArr = ['/(ㄒoㄒ)/~~ 未找到释义']
        finally:
            self.resArr = resArr
            sublime.active_window().show_quick_panel(resArr, self.on_select)

    def on_select(self, index):
        if index > -1:
            sublime.set_clipboard(self.resArr[index])
        pass


class CibaApiCall(threading.Thread):
    def __init__(self, words):
        self.words = words
        self.timeout = 5
        # save session
        self.s = requests.session()
        # change http header
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, sdch", "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
            "Cache-Control": "max-age=0",
        })
        threading.Thread.__init__(self)

    def run(self):
        myurl = "http://www.iciba.com/%s" % self.words
        try:
            response = self.s.get(myurl, timeout=self.timeout)
            soup = BeautifulSoup(response.content, "html.parser")
            temp_results = soup.find_all("div", class_="in-base")
            self.parse(temp_results)
            return
        except Exception as e:
            sublime.error_message(str(e))

    def parse(self, result):
        # print(result)
        if not result:
            translate_final = ['/(ㄒoㄒ)/~~ 未找到ciba释义']
        else:
            # 不知道为什么在subl里ul的class就没有了。
            # temp_results = result[0].find_all('ul', class_='base-list')
            # print(result[0].find_all('span', class_='prop'))
            temp_results = result[0].find_all('span', class_='prop')[0].parent.parent
            # print(temp_results)
            if not temp_results:
                translate_final = ['/(ㄒoㄒ)/~~ 未找到ciba释义']
            else:
                # print(temp_results)
                translate_final = []
                for node in temp_results:
                    if isinstance(node, bs4.element.Tag):
                        temp_str = ''
                        for x in node.p:
                            if isinstance(x, bs4.element.Tag):
                                temp_str += x.text
                        translate_final.append(node.span.text + " " + temp_str)
        if not translate_final:
            translate_final = ['/(ㄒoㄒ)/~~ 未找到ciba释义']
        self.resArr = translate_final
        sublime.active_window().show_quick_panel(translate_final, self.on_select)

    def on_select(self, index):
        if index > -1:
            sublime.set_clipboard(self.resArr[index])
        pass
