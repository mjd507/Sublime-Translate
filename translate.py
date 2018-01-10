#!/bin/python3
import sublime
import sublime_plugin
import hashlib
import urllib
import random
import threading
import json
# requests lib is more easier to use.
import requests
import bs4
from bs4 import BeautifulSoup


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
        sublime.active_window().show_input_panel('希望是个好东西，生生不息，遥不可及 :)', 'enjoy everyday！', self.on_done, None,
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
        appKey = self.appKey
        secretKey = self.secretKey
        myurl = 'https://openapi.youdao.com/api'
        q = self.words
        fromLang = 'auto'
        toLang = 'auto'
        salt = random.randint(1, 65536)

        sign = appKey + q + str(salt) + secretKey
        sign = hashlib.md5(sign.encode('utf-8')).hexdigest()
        myurl = myurl + '?appKey=' + appKey + '&q=' + urllib.parse.quote(
            q) + '&from=' + fromLang + '&to=' + toLang + '&salt=' + str(salt) + '&sign=' + sign

        try:
            conn = urllib.request.urlopen(myurl, timeout=self.timeout)
            response = conn.read()
            result = response.decode('utf-8')
            print(result)
            self.parse(result)
            return
        except Exception as e:
            sublime.error_message(str(e))
        finally:
            conn.close()

    def parse(self, result):
        jsonObj = json.loads(result)
        try:
            resArr = jsonObj['basic']['explains']
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
        print(result)
        if not result:
            translate_final = ['/(ㄒoㄒ)/~~ 未找到释义']
        else:
            # 不知道为什么在subl里ul的class就没有了。
            # temp_results = result[0].find_all('ul', class_='base-list')
            # print(result[0].find_all('span', class_='prop'))
            temp_results = result[0].find_all('span', class_='prop')[0].parent.parent
            print(temp_results)
            if not temp_results:
                translate_final = ['/(ㄒoㄒ)/~~ 未找到释义']
            else:
                # print(temp_results)
                translate_final = []
                for node in temp_results:
                    if isinstance(node, bs4.element.Tag):
                        temp_str = ''
                        for x in node.p:
                            if isinstance(x, bs4.element.Tag):
                                temp_str += x.text
                        translate_final.append(node.span.text + "\t" + temp_str)
        if not translate_final:
            translate_final = ['/(ㄒoㄒ)/~~ 未找到释义']
        self.resArr = translate_final
        sublime.active_window().show_quick_panel(translate_final, self.on_select)

    def on_select(self, index):
        if index > -1:
            sublime.set_clipboard(self.resArr[index])
        pass
