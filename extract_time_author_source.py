# coding: utf-8
# 抽取网页中的：1、来源，2、时间，3、作者
import re
import os
import codecs


sourcePagePath = "data/"
hashSourceFile = "index_url.txt"


def mapFile():
    pattern = "来源"
    allPath = fromAllPage()

    for k, v in allPath.items():
        print(v)
        s = re.match(pattern, v)
        if s is not None:
            print(k)


def getHashFile():
    hashMap = {}
    with codecs.open(hashSourceFile, "r", encoding="utf-8") as file:
        for line in file.readlines():
            line = line.strip()
            hashMap[line.split("\t")[0]] = line.split("\t")[1]
    return hashMap


def fromAllPage():
    allPath = {}
    for home, dirs, files in os.walk(sourcePagePath):
        for filename in files:
            fullname = os.path.join(home, filename)
            allPath[filename[0: filename.index(".")]] = readFile(fullname)
    return allPath


# 读取文件内的内容
def readFile(filename):
    lines = ""
    with codecs.open(filename, "r", encoding="utf-8") as file:
        for line in file.readlines():
            lines += line
    return lines


if __name__ == "__main__":
    mapFile()
