# coding: utf-8


startPage = "http://news.xjtu.edu.cn/"


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


if __name__ == "__main__":
    n = create_new_url("http://news.xjtu.edu.cn", "index/gjjs.htm")
    print(n)
