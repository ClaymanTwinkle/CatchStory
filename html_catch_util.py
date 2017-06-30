# -*- coding: utf-8 -*-

import urllib2


### 解析url为html字符串
def getHtml(url):
    page = urllib2.urlopen(url)
    html = page.read()
    return html


### 清理html的转义字符
def clear_esc(html):
    return html.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&quot;", '"').replace("&#13;", "\n")
