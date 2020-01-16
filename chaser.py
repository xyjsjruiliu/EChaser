# coding: utf-8
# author: liu rui
import codecs
import random
import requests
import threading
import happybase
import lxml.etree as etree

from queue import Queue
from time import ctime, sleep
from bs4 import BeautifulSoup

# 起始网页
startPage = "http://news.xjtu.edu.cn/"

# 所有已经爬取的链接
url_set = set()
# 待爬取队列
url_queue = Queue()
# 已经爬取的网页链接数量
number_page = {"count": 0}
# 创建线程列表
threads = []
num_thread = 10


class HBaseClient(object):
    def __init__(
            self,
            host=None,
            port=None,
            timeout=None
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        # HBase库中表的名字，可以修改
        self.table_name = "echaser_db"

        # 连接数据库
        self.connection = happybase.Connection(host=self.host,
                                               port=self.port,
                                               timeout=self.timeout,
                                               # protocol='compact', transport='framed'
                                               )
        self.connection.open()

    # 扫描全表
    def scan(self, table_name, row_key):
        table = self.connection.table(table_name)
        # 全局扫描一个table
        for key, value in table.scan(row_prefix=bytes(row_key, encoding="utf8")):
            print(str(key, encoding="utf-8"))
            for k, v in value.items():
                print("\t", str(k, encoding="utf-8"), str(v, encoding="utf-8"))

    # 批量导入数据
    def batch_put(self, table_name, data):
        table = self.connection.table(table_name)
        bat = table.batch()
        for hbase_data in data:
            bat.put(hbase_data["row_key"],
                    {'baseInfo:' + hbase_data["column"]: hbase_data["value"]})
        bat.send()


client = HBaseClient("localhost", 9090, 5000)


# 爬虫线程类
class university_spider_thread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

    def run(self):
        while not url_queue.empty():
            # if number_page["count"] >= 100:
            #     exit(0)
            # 线程需要执行的方法
            url = url_queue.get()
            print("当前爬取链接：", url,
                  "\t待爬链接数量：", url_queue.qsize(),
                  "\t总共获取链接数量：", len(url_set),
                  "\t当前时间：", ctime(),
                  "\t当前下载链接数量：", number_page["count"],
                  "\t线程name：", self.name)
            sleep(random.randint(2, 7))
            try:
                get_children_url(url)
            except Exception as e:
                print(e)
                print("get children url error!!!!!")
                # client = HBaseClient("localhost", 9090, 5000)


# 获取当前网页中的所有子链接，并保存当前网页的内容
def get_children_url(url):
    try:
        html = requests.get(url, timeout=4).content
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
    number_page["count"] += 1


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
    data = [
            {"row_key": url, "column": "url", "value": url},
            {"row_key": url, "column": "html", "value": text},
            {"row_key": url, "column": "time", "value": ctime()}
        ]
    # with codecs.open("index_url.txt", "a+", encoding="utf-8") as file:
    #     file.writelines(str(h) + "\t" + url + "\n")
    # with codecs.open("data/" + str(h) + ".txt", "w", encoding="utf-8") as file:
    #     file.writelines(str(text))
    client.batch_put("echaser_db", data)


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
