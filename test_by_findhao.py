import hashlib
import urllib
import random
import threading
import json
import sublime
import sublime_plugin

class YouDaoApiCall(threading.Thread):

    def __init__(self, words):
        self.words = words
        self.appKey = "6e8463beddc95355"
        self.secretKey = "uW3AJNMG67kL2TdpSsle45WCd6ZaoYAs"
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
