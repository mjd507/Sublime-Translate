#!/bin/python3
import sublime
import sublime_plugin
import hashlib
import threading
import json
import uuid
import requests
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

    def on_cancel(self):
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

        YOUDAO_URL = 'https://openapi.youdao.com/api'
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
            self.parse(result)
            return
        except Exception as e:
            sublime.error_message(str(e))

    def parse(self, result):
        jsonObj = json.loads(result)
        # print(jsonObj)
        try:
            resArr = jsonObj['translation']
        except Exception as e:
            resArr = ['Does not find the result from YouDao Api']
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
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd", 
            "Accept-Language": "en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4",
            "Cache-Control": "max-age=0",
            "Origin": "https://www.iciba.com",
            "referer": "https://www.iciba.com"
        })
        threading.Thread.__init__(self)

    def run(self):
        client = "6"
        key = "1000006"
        timestamp = str(int(time.time() * 1000))
        word = self.words
        sign_str = "/chat/word/v1" + client + key + timestamp +  word + "7ece94d9f9c202b0d2ec557dg4r9bc"

        hash_algorithm = hashlib.md5()
        hash_algorithm.update(sign_str.encode('utf-8'))
        signature = hash_algorithm.hexdigest()

        api_url = "https://service.iciba.com/chat/word/v1"
        params = {
            "client": client,
            "key": key,
            "timestamp": timestamp,
            "word": word,
            "signature": signature
        }
        try:
            response = requests.get(api_url, params=params, timeout=self.timeout)
            result = response.json()
            self.parse(result)
        except Exception as e:
            sublime.error_message("Ciba Api Request Failed: " + str(e))

    def parse(self, result):
        # print(result)
        data = result.get("data", {})
        aiVo = data.get("aiSearchWordSentenceVo", {})
        paraphraseMap = aiVo.get("paraphraseMap", {})
        translate_final = [f"{k} {v}" for k, v in paraphraseMap.items()]
        if not translate_final:
            translate_final = ['Does not find the result from Ciba!']
        self.resArr = translate_final
        sublime.active_window().show_quick_panel(translate_final, self.on_select)

    def on_select(self, index):
        if index > -1:
            sublime.set_clipboard(self.resArr[index])
        pass
