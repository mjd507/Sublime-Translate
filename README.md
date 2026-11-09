## SublimeTransit

一个在 Sublime 编辑器上翻译单词的插件。

## API

### 有道智云

使用[有道智云](http://ai.youdao.com/docs/doc-trans-api.s#p02)提供的翻译 api 实现。

tip: 有道智云的翻译服务是收费服务，具体收费可参加其[文档](http://ai.youdao.com/docs/doc-trans-price.s#p03)

需要自己注册一个账号，获取到 appKey 和 secretKey，在 Setting - User 里面配置自己的 appKey 和 secretKey。


### 金山词霸

解析了金山词霸的网页，免费使用，不限次数。

默认开启，如需关闭需要在个人的配置文件里修改 ciba 的 value 为 false.

## 安装

- 使用 Sublime 的 「Package Control」包管理器进行安装，默认你已安装了包管理器，打开它，搜索「Translate-CN」，点击安装后，即可使用。


## 使用方法

- 快捷键

```python
# MacOs:
alt + t 翻译选中的文本
alt + i 翻译输入的文本

# Windows & Linux
alt + t 翻译选中的文本
alt + i 翻译输入的文本
```

- 右击，显示快捷菜单，选中 Translate-CN
  - current text  翻译选中的文本
  - input text    翻译输入的文本

## 配置

你可以在 Preferences --> Package Settings -->  Translate-CN --> Settings - User 下进行插件配置
```json
{
    "translate_whole_word": false,
    "appKey": "xxxxxxx",
    "secretKey": "xxxxxxx",
    "ciba": true
}
```

