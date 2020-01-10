# coding: utf-8
# author: liu rui
import codecs
import threading
from time import ctime, sleep

import requests
import lxml.etree as etree
from queue import Queue

from bs4 import BeautifulSoup

startPage = "http://news.xjtu.edu.cn/"


class university_spider_thread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        print("Starting " + self.name + ctime())
        # 获得锁，成功获得锁定后返回True
        # 可选的timeout参数不填时将一直阻塞直到获得锁定
        # 否则超时后将返回False
        while not url_queue.empty():
            # threadLock.acquire()
            # 线程需要执行的方法
            url = url_queue.get()
            print(url, url_queue.qsize())
            get_children_url(url)
            # 释放锁
            # threadLock.release()


# 所有已经爬取的链接
url_set = set()
# 待爬取队列
url_queue = Queue()
threadLock = threading.Lock()
# 创建线程列表
threads = []
num_thread = 1


def get_children_url(url):
    try:
        html = requests.get(url).content
    except:
        return

    # 提取当前网页中所有的链接
    selector = etree.HTML(html)
    beautifulSoupText = BeautifulSoup(html, 'html.parser')
    temp_url_list = selector.xpath('//a')
    for temp_url in temp_url_list:
        # print(a)
        new = temp_url.attrib.get("href", "")
        # 如果当前链接为JavaScript或者为空时，则不保存
        if new.startswith("javascript") or new == "":
            continue
        # 如果当前内部链接就是http时，则不考虑原始链接
        if new.startswith("http"):
            new_url = new
        else:
            new_url = create_new_url(url, new)
        # print(url, new)

        # 新的链接不能在过往的链接中，且不能离开现有的域名
        if not url_set.__contains__(new_url) and new_url.startswith(startPage):
            url_set.add(new_url)
            url_queue.put(new_url)
    save_html(url, beautifulSoupText)


# 保存当前网页的所有内容
def save_html(url, text):
    h = hash(url)
    with codecs.open("index_url.txt", "a+", encoding="utf-8") as file:
        file.writelines(str(h) + "\t" + url + "\n")
    with codecs.open("data/" + str(h) + ".txt", "w", encoding="utf-8") as file:
        file.writelines(str(text))


def single_thread():
    while not url_queue.empty():
        url = url_queue.get()
        sleep(1)
        print(url, url_queue.qsize(), len(url_set))
        get_children_url(url)


# 根据
def create_new_url(start, end):
    tempStart = start.split("/")[:-1]
    tempEnd = end.split("/")

    for e in tempEnd:
        if e.__eq__(".."):
            tempStart = tempStart[:-1]
        else:
            tempStart.append(e)
    return "/".join(tempStart)


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
    single_thread()
