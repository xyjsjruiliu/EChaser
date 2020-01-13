# coding: utf-8
# author: liu rui
import codecs
import random
import threading
from time import ctime, sleep

import requests
import lxml.etree as etree
from queue import Queue

from bs4 import BeautifulSoup

# 起始网页
startPage = "http://news.xjtu.edu.cn/"

# 所有已经爬取的链接
url_set = set()
# 待爬取队列
url_queue = Queue()
# 创建线程列表
threads = []
num_thread = 10


# 爬虫线程类
class university_spider_thread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        while not url_queue.empty():
            # 线程需要执行的方法
            url = url_queue.get()
            print("当前爬取链接：", url,
                  "\t待爬链接数量：", url_queue.qsize(),
                  "\t总共获取链接数量：", len(url_set),
                  "\t当前时间：", ctime())
            sleep(random.randint(2, 7))
            get_children_url(url)


# 获取当前网页中的所有子链接，并保存当前网页的内容
def get_children_url(url):
    try:
        html = requests.get(url, timeout=2).content
    except:
        return

    # 提取当前网页中所有的链接
    selector = etree.HTML(html)
    beautifulSoupText = BeautifulSoup(html, 'html.parser')
    temp_url_list = selector.xpath('//a')
    for temp_url in temp_url_list:
        new = temp_url.attrib.get("href", "")
        # 如果当前链接为JavaScript或者为空时，则不保存，或者链接为图片、word等时也不保存
        if isErrorUrl(new):
            continue
        handle_url(url, new)
    # 保存当前链接的内容
    save_html(url, beautifulSoupText)


# 处理新的子链接
def handle_url(url, new):
    # 如果当前内部链接就是http时，则不考虑原始链接
    if new.startswith("http"):
        new_url = new
        # print(new_url)
    else:
        new_url = create_new_url(url, new)

    # 新的链接不能在过往的链接中，且不能离开现有的域名
    if not url_set.__contains__(new_url):
        url_set.add(new_url)
        url_queue.put(new_url)


# 如果当前链接为JavaScript或者为空时，则不保存，或者链接为图片、word等时也不保存
def isErrorUrl(new):
    if new.startswith("javascript") or new == "" \
            or new.endswith(".pdf") \
            or new.endswith(".jpg") \
            or new.endswith(".png") \
            or new.endswith(".doc") \
            or new.endswith(".docx") \
            or new.endswith(".xls") \
            or new.endswith(".xlsx") \
            or new.endswith(".apk") \
            or new.endswith(".ipa") \
            or new.endswith(".zip"):
        return True
    else:
        return False


# 保存当前网页的所有内容
def save_html(url, text):
    h = hash(url)
    with codecs.open("index_url.txt", "a+", encoding="utf-8") as file:
        file.writelines(str(h) + "\t" + url + "\n")
    with codecs.open("data/" + str(h) + ".txt", "w", encoding="utf-8") as file:
        file.writelines(str(text))


# 单线程运行模式
def single_thread():
    while not url_queue.empty():
        url = url_queue.get()
        sleep(0.5)
        print(url, url_queue.qsize(), len(url_set))
        get_children_url(url)


# 根据源链接，和子链接，合成新的链接
def create_new_url(start, end):
    if len(start.split("/")) == 3:
        return start + "/" + end

    tempStart = start.split("/")[:-1]
    tempEnd = end.split("/")

    for e in tempEnd:
        if e.__eq__(".."):
            tempStart = tempStart[:-1]
        else:
            tempStart.append(e)
    return "/".join(tempStart)


# 多线程运行模式
def mutil_thread():
    for i in range(num_thread):
        thread = university_spider_thread(0, "Thread-%s" % i)
        # 添加线程到列表
        threads.append(thread)
    # 循环开启线程
    for i in range(num_thread):
        threads[i].start()
    # 等待所有线程完成
    for t in threads:
        t.join()

    print("Exiting Main Thread")


if __name__ == "__main__":
    url_set.add(startPage)
    print(startPage, url_queue.qsize(), len(url_set))
    get_children_url(startPage)
    # single_thread()
    mutil_thread()
