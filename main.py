# -*- coding: utf-8 -*-
import re
import urllib2
import uuid

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from lxml import etree

from html_catch_util import getHtml

### 配置代理(外网) ###

proxy_info = {'host': 'dev-proxy.oa.com',
              'port': 8080
              }
proxy_support = urllib2.ProxyHandler({"http": "http://%(host)s:%(port)d" % proxy_info})

opener = urllib2.build_opener(proxy_support)
urllib2.install_opener(opener)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:root@127.0.0.1/story?charset=utf8"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


### 整本书
class Book(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    author = db.Column(db.String(255))
    pic = db.Column(db.Text())
    description = db.Column(db.Text())
    type = db.Column(db.String(255))
    url = db.Column(db.Text(255))


### 章节
class Chapter(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    no = db.Column(db.Integer())
    title = db.Column(db.String(255))
    story_id = db.Column(db.String(255))
    content = db.Column(db.Text())
    url = db.Column(db.Text())

    def __str__(self):
        return self.id + "-" + self.title + "-" + self.story_id + "-" + self.content + "-" + self.url


db.create_all()


### 爬取全书网（http://www.quanshuwang.com）的书
class Quanshuwang(object):
    root_url = u"http://www.quanshuwang.com"
    shuku_root_url = root_url + u"/shuku/"
    page_root_url = root_url + u"/all/allvisit_0_0_0_0_0_0_%s.html"
    book_root_url = root_url + u"/book_\d+\.html"
    encoding = u"gbk"

    ### 读取全网书总页数
    def resolve_total_page_count(self):
        html = getHtml(self.shuku_root_url).decode(self.encoding)
        html_tree = etree.HTML(html)
        page_no_array = html_tree.xpath(u'//*[@id="pagelink"]/a/text()')
        return int(page_no_array[len(page_no_array) - 1])

    ### 遍历所有分页，获取所有书的详情页url
    def resolve_all_page_url(self, total_page_count):
        for i in range(1, total_page_count + 1):
            story_detail_url_list = self.resolve_all_story_url_from_html(self.page_root_url % i)
            ### print story_detail_url
            for story_detail_url in story_detail_url_list:
                story, chapter_detail_url = self.resolve_book_info_html(story_detail_url)
                self.resolve_chapter_info_html(chapter_detail_url, story.id)

    ### 从html中匹配出所有书的详情url
    def resolve_all_story_url_from_html(self, html_url):
        html = getHtml(html_url).decode(self.encoding)
        return re.findall(self.book_root_url, html)

    ### 解析书的基本信息
    def resolve_book_info_html(self, html_url):
        print html_url

        html = getHtml(html_url)
        html_tree = etree.HTML(html)

        detail_url = html_tree.xpath(u'//*[@class="b-oper"]/a/@href')
        if len(detail_url) != 0:
            print detail_url[0].encode('utf-8')

        book = Book.query.filter_by(url=html_url).first()
        if book is not None:
            return book, detail_url[0]

        book = Book()
        book.id = uuid.uuid3(uuid.NAMESPACE_DNS, html_url.encode('utf-8'))
        book.url = html_url

        name = html_tree.xpath(u'//*[@class="b-info"]/h1/text()')
        if len(name) != 0:
            book.name = name[0]
            print book.name.encode('utf-8')

        type = html_tree.xpath(u'//*[@class="main-index"]/a/text()')
        if len(type) != 0:
            book.type = type[len(type) - 1]
            print book.type.encode('utf-8')

        author = html_tree.xpath(u'//*[@class="bookso"]/dd/a/text()')
        if len(author) != 0:
            book.author = author[0]
            print book.author.encode('utf-8')

        description = html_tree.xpath(u'//*[@id="waa"]/text()')
        if len(description) != 0:
            book.description = description[0]
            print book.description.encode('utf-8')

        pic_url = html_tree.xpath(u'//*[@class="detail"]/a/img/@src')
        if len(pic_url) != 0:
            book.pic = pic_url[0]
            print book.pic.encode('utf-8')

        db.session.add(book)
        db.session.commit()
        return book, detail_url[0]

    ### 解析书本章节信息
    def resolve_chapter_info_html(self, html_url, story_id):

        html = getHtml(html_url)
        print html_url
        html_tree = etree.HTML(html)

        chapter_title_list = html_tree.xpath(u'//*[@class="clearfix dirconone"]/li/a/text()')
        chapter_url_list = html_tree.xpath(u'//*[@class="clearfix dirconone"]/li/a/@href')

        for i in range(len(chapter_url_list)):
            chapter_url_list[i] = html_url + u"/" + chapter_url_list[i]

        size = min(len(chapter_title_list), len(chapter_url_list))

        for i in range(size):
            if Chapter.query.filter_by(url=chapter_url_list[i]).first() is None:
                chapter = Chapter()
                chapter.id = uuid.uuid3(uuid.NAMESPACE_DNS, chapter_url_list[i].encode('utf-8')).__str__()
                chapter.no = i
                chapter.story_id = story_id
                chapter.title = chapter_title_list[i]
                chapter.url = chapter_url_list[i]
                chapter.content = self.resolve_chapter_content_html(chapter_url_list[i])
                db.session.add(chapter)
                db.session.commit()

    ### 解析章节内容，输出篇幅
    def resolve_chapter_content_html(self, html_url):
        html = getHtml(html_url)
        html_tree = etree.HTML(html)
        main_content = html_tree.xpath(u'//*[@id="content"]/text()')
        return u'\n'.join(main_content)


if __name__ == '__main__':
    quanshuwang = Quanshuwang()
    # print quanshuwang.resolve_story_chapter_info_html("http://www.quanshuwang.com/book/1/1314")
    print quanshuwang.resolve_all_page_url(quanshuwang.resolve_total_page_count())
