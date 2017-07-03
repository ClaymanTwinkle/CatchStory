# -*- coding: utf-8 -*-

import urllib2


### 解析url为html字符串
def getHtml(url):
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)
    try:
        page = urllib2.urlopen(url, timeout=20)
        html = page.read()
    except:
        print u"超时了"
        return getHtml(url)
    return html


### 清理html的转义字符
def clear_esc(html):
    return html.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#13;", "\n")
