#!/usr/bin/env python
'''
- class attribuets: xxx_temp should moved into class body with capital letters.
- private method and attributes should contain two leadding underscores.
- ?init all the instance attributes in the __init__ body like self.xxx = xxx

Question:
fetch_rss: if mark > output, safe for comming item, not for current.
           if output > mark, safe for current data, not for future.
now it focus on current data.
But not occur.
There is a new item comming after I fetch article, then a long time to fetch
images, and mark as read. In the end, the new item is still unread, why?

'''
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os, time, base64, curses

from GoogleReader import GoogleReader#, Feed, Article
from lib.kindle_format import kindle_format

project_folder = ""

def main():
    """
    fetch_rss.py <url>
    --no-image
    --no-mark
    """
    arg_list = ["--no-image", "--no-mark", "--debug-on", "-h"]
    no_image = False
    no_mark = False
    debug_on = False
    if len(sys.argv) >= 2:
        for arg in sys.argv[1:]:
            if arg not in arg_list:
                print "Error: Unsupported argument", arg
                return
            if arg == "--no-image":
                no_image = True
            if arg == "--no-mark":
                no_mark = True
            if arg == "--debug-on":
                debug_on = True
                no_image = True
                no_mark = True
            if arg == "-h":
                print "Usage: fetch_rss.py [--no-image] [--no-mark] [-h] url"
                print "Options:"
                print "    -h: show this help message"
                print "    --no-image: fetch rss without images"
                print "    --no-mark: not mark all as read after fetching"
                print "    --debug-on: fetch rss from a test label in google reader, e.g. Linux"
                return


    pretty_print("Fetch RSS from Google Reader")

    # fetch article
    username = base64.b64decode("your encrypted username")
    password = base64.b64decode("your encrypted password")
    if debug_on:
        feed_list_url = ("https://www.google.com/reader"
                         "/public/subscriptions/user/-/label/Linux")
        gr = GoogleReader(username=username, password=password,feed_list_url=feed_list_url)
    else:
        gr = GoogleReader(username=username, password=password)

    print "> Counting Articles..."

    article_amount = gr.get_amount()
    if not article_amount:
        print "> No new items."
        return

    input_char = ""
    while input_char.lower() not in ["y", "n"]:
        input_char = raw_input("    Fetch all %s articles? (y or n)" % article_amount)
        if input_char == "y":
            break
        elif input_char == "n":
            pretty_print("Abort to fetching articles")
            # os.rmdir(project_folder)
            return

    base_folder = "/home/ryan/local/scripts/kindle/pub"
    timestamp = time.strftime("rss_%Y-%m-%d_%H-%M")
    folder_name = "%s_%s" % (timestamp, gr.feed_list_url.rpartition("/")[2])
    global project_folder
    project_folder = os.path.join(base_folder, folder_name)
    os.mkdir(project_folder)
    project_title = "news.rss"

    gr.fetch_feeds()

    kf = kindle_format.Periodical(file_folder=project_folder, title=project_title)
    article_count = 0
    for feed_count, feed in enumerate(gr.unread_feeds):
        kf.append_section(feed.title)
        for feed_article_count, article in enumerate(feed.articles):
            left = article_amount - article_count - feed_article_count
            title = "%s&lt; %s" % (left, article.title)
            if article.desc:
                content = "".join(article.desc)
            else:
                content = ""
            kf.append_item(title, content)
        article_count += len(feed.articles)

    if no_image:
        kf.output(fetch_image=False)
    else:
        kf.output()

    if not no_mark:
        gr.mark_all_as_read()

    pretty_print("Success")

def pretty_print(text):
    symbol = "*"
    curses.setupterm()
    length = curses.tigetnum("cols")
    sep = (length - len(text) - 2) / 2
    layout_temp = "\n%(sep)s %(text)s %(sep)s\n"
    layout = layout_temp % dict(sep="*"*sep,
                                text=text)
    print layout

if __name__ == "__main__":
    try:
        main()
    except:
        print "remove", project_folder
        os.rmdir(project_folder)
