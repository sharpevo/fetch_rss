#!/usr/bin/env python
'''
- class attribuets: xxx_temp should moved into class body with capital letters.
- private method and attributes should contain two leadding underscores.
- ?init all the instance attributes in the __init__ body like self.xxx = xxx

'''
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import os, time
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import lxml.html, lxml.etree

import socket
# socket.setdefaulttimeout(5.0)

from subprocess import call
from md5 import new as md5

sys.path.append("/home/ryan/local/scripts/python")
import internet_util, google_reader, image_util

header = ""
token = ""
# uid, file_title, html, ncx
opf_temp = '''
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="%(uid)s">
<metadata>
<dc-metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>%(title)s</dc:title>
    <dc:language>zh</dc:language>
    <dc:identifier id="uid">%(uid)s</dc:identifier>
    <dc:creator>GoogleReader</dc:creator>
    <dc:description></dc:description>
    <meta name="cover" content="cover_id" />
</dc-metadata>

<x-metadata>
    <output encoding="utf-8" content-type="application/x-mobipocket-subscription-magazine"></output>
</x-metadata>
</metadata>

<manifest>
    <item id="css" media-type="text/css" href="content.css" />
    <item id="cover_id" media-type="image/jpeg" href="cover.jpg"/>
    <item id="content" media-type="application/xhtml+xml" href="%(html)s"></item>
    <item id="toc" media-type="application/x-dtbncx+xml" href="%(ncx)s"></item>
</manifest>

<spine toc="toc">
    <itemref idref="content"/>
</spine>

<guide>
    <reference type="start" title="start" href="%(html)s#content"></reference>
    <reference type="toc" title="toc" href="%(html)s#toc"></reference>
    <reference type="text" title="cover" href="%(html)s#cover"></reference>
</guide>
</package>
'''
# uid, title, html
ncx_temp = '''
<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh">
<head>
<meta name="dtb:uid" content="%(uid)s" />
<meta name="dtb:depth" content="4" />
<meta name="dtb:totalPageCount" content="0" />
<meta name="dtb:maxPageNumber" content="0" />
</head>
<docTitle><text>%(title)s</text></docTitle>
<docAuthor><text>GoogleReader</text></docAuthor>
<navMap>
    <navPoint class="periodical">
        <navLabel><text>%(title)s</text></navLabel>
        <content src="%(html)s" />
        %(nav_secs)s
    </navPoint>
</navMap>
</ncx>
'''
# sec_count, html, feed_title
nav_sec_temp = '''
<navPoint class="section" id="%(sec_count)s">
    <navLabel><text>%(title)s</text></navLabel>
    <content src="%(html)s#section_%(sec_count)s" />

    %(nav_arts)s
</navPoint>
'''
# sec, art count, html, article_title
nav_art_temp = '''
<navPoint class="article" id="%(sec_count)s_%(art_count)s" playOrder="%(art_count)s">
  <navLabel><text>%(title)s</text></navLabel>
  <content src="%(html)s#article_%(sec_count)s_%(art_count)s" />
</navPoint>
'''

def main():

    ## Construct destination file. e.g.,
    # base_folder = "/home/ryan/local/scripts/rss/output"
    # file_name = "2012-05-08_11-28(182)"
    # file_folder = "/home/ryan/local/scripts/rss/output/2012-05-08_11-28(182)"
    # file_path = "/home/ryan/local/scripts/rss/output/2012-05-08_11-28(182).html"
    base_folder = "/home/ryan/local/scripts/kindle/fetch_rss/output"
    timestamp = time.strftime("%Y.%m.%d %H:%M")


    # fetch article
    feed_list_url = ("https://www.google.com/reader"
                     "/public/subscriptions/user/-/label/Featured")
                     # "/public/subscriptions/user/-/label/Linux")
    gr = google_reader.GoogleReader(feed_list_url=feed_list_url)
    feed_content_list = gr.fetch_articles()
    if not feed_content_list:
        return "No new items."

    # make html
    article_sum = gr.get_sum()
    file_name = "Featured Articles (%s)" % article_sum
    file_folder = os.path.join(base_folder, file_name)
    try:
        os.mkdir(file_folder) # create a folder to storage images.
    except OSError:
        pass

    # trans article_sum to mark the progress with left count
    html, cat = make_html(feed_content_list, article_sum)
    make_opf(cat, file_name, file_folder)
    html_with_images = internet_util.fetch_images(html, file_folder, timeout=5.0)

    # output files
    file_path = "%s.html" % file_folder
    output(file_path, html_with_images)

    gr.mark_all_as_read()

    texts = [(file_name, (150, 100)), (timestamp, (220, 650))]
    cover_path = "/home/ryan/local/scripts/kindle/fetch_rss/output/cover_temp.jpg"
    cover_output = "/home/ryan/local/scripts/kindle/fetch_rss/output/cover.jpg"
    image_util.add_texts_to_image(texts, cover_path, cover_output)
    convert_to_mobi_by_kindlegen(file_path, file_folder)

    return "Finished!"

def convert_to_mobi_by_kindlegen(file_path, file_folder):

    opf_file = "%s.opf" % file_folder
    call(["kindlegen", opf_file])

def make_html(feed_content_list, article_sum):

    # catalogs storage feed title and article titles.
    # [..., (feed_tit, art_tits), ...]
    # also used in opf_gen
    cat = []
    feed_article_titles = []
    # html contains 3 parts, cover, toc, and contents.
    # Individually construction.
    toc = ""
    contents = ""
    cover = ""
    html_temp = '''
    <html>
      <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head>
      <body>
        %(cover)s
        %(toc)s
        %(contents)s
      </body>
    </html>
    '''

    # make contents
    content_temp = '''
    <div id="contents">
        %(sections)s
    </div>
    '''
    section_temp = '''
    <div id="section_%(count)s" class="section">
        %(articles)s
    </div>
    <mbp:pagebreak></mbp:pagebreak>
    '''
    article_temp = '''
    <div id="article_%(sec_count)s_%(art_count)s" class="article">
        <h2 class="article_title">%(title)s</h2>
        <div class="article_content">%(contents)s</div>
    </div>
    <mbp:pagebreak></mbp:pagebreak>
    '''
    feed_count = 0
    sections = []
    cur_art_count = 0
    for feed_title, feed_article_list in feed_content_list:
        feed_count += 1
        articles = []
        article_count = 0
        feed_article_titles = []
        # for article in feed_article_list:
        for art_title, art_desc in feed_article_list:
            article_count += 1
            cur_art_count += article_count
            left = article_sum - cur_art_count
            title = "%s (%s+)" % (art_title.string, left)
            if art_desc:
                content = "".join(art_desc)
            else:
                # if art has no content or summary
                content = ""
            articles.append(article_temp % dict(sec_count=feed_count,
                                                art_count=article_count,
                                                title=title,
                                                contents=content))
            feed_article_titles.append(title)
        sections.append(section_temp % dict(count=feed_count,
                                            articles="".join(articles)))
        cat.append((feed_title,feed_article_titles))
    contents = content_temp % dict(sections="".join(sections))

    # make toc
    toc_temp = '''
    <div id="toc">
        %(feed_list)s
        <mbp:pagebreak></mbp:pagebreak>
        %(details)s
    </div>
    <mbp:pagebreak></mbp:pagebreak>
    '''
    toc_feed_list_temp = '''
    <h2>Feeds</h2>
    <ol>
        %(feeds)s
    </ol>
    <mbp:pagebreak></mbp:pagebreak>
    '''
    toc_feed_temp = '''
    <li>
        <a href="#toc_section_%(sec_count)s">%(title)s</a><br>
        %(art_count)s items.
    </li>
    '''
    toc_detail_temp = '''
    <div id="toc_section_%(count)s" class="section">
        <h3>%(title)s</h3>
        <ol>
            %(articles)s
        </ol>
    </div>
    <mbp:pagebreak></mbp:pagebreak>
    '''
    toc_article_temp = '''
    <li>
        <a href="#article_%(sec_count)s_%(art_count)s">%(title)s</a>
    </li>
    '''

    toc_details = []

    toc_feeds = []
    toc_feed_list = []
    feed_count = 0
    for feed_title, feed_article_titles in cat:
        feed_count += 1
        art_count = len(feed_article_titles)
        toc_feeds.append(toc_feed_temp % dict(sec_count=feed_count,
                                              title=feed_title,
                                              art_count=art_count))
        toc_articles = []
        art_count = 0
        for article in feed_article_titles:
            art_count += 1
            toc_articles.append(toc_article_temp % dict(sec_count=feed_count,
                                                        art_count=art_count,
                                                        title=article))
        toc_details.append(toc_detail_temp % dict(count=feed_count,
                                                  title=feed_title,
                                                  articles="".join(toc_articles)))
    toc_feed_list.append(toc_feed_list_temp % dict(feeds="".join(toc_feeds)))

    toc = toc_temp % dict(feed_list="".join(toc_feed_list),
                          details="".join(toc_details))

    # composition
    cover = '''
    <div id="cover">
      <h1 id="title">Google Reader Featured Articles</h1>
      <img src="cover.jpg"/>
    </div>
    '''
    html = html_temp % dict(cover=cover,
                            toc=toc,
                            contents=contents)
    return (html, cat)

def make_opf(cat, file_name, file_folder):

    uid = md5(file_name).hexdigest()
    html = "%s.html" % file_name
    ncx = "%s.ncx" % file_name

    nav_secs = []
    feed_count = 0
    for feed_title, feed_article_titles in cat:
        feed_count += 1
        art_count = len(feed_article_titles)
        opf = opf_temp % dict(uid=uid,
                              title=file_name,
                              html=html,
                              ncx=ncx)
        art_count = 0
        nav_arts = []
        for article in feed_article_titles:
            art_count += 1
            nav_arts.append(nav_art_temp % dict(sec_count=feed_count,
                                                art_count=art_count,
                                                title=article,
                                                html=html))
        nav_secs.append(nav_sec_temp % dict(sec_count=feed_count,
                                            title=feed_title,
                                            html=html,
                                            nav_arts="".join(nav_arts)))
    ncx = ncx_temp % dict(uid=uid,
                          title=file_name,
                          html=html,
                          nav_secs="".join(nav_secs))

    ncx_path = "%s.ncx" % file_folder
    output(ncx_path, ncx)

    opf_path = "%s.opf" % file_folder
    output(opf_path, opf)
    # sattic file shared by all the peridical.
    # css_path = "%s.css" % file_folder
    # output(css_path, css)

def output(file_path, strings):
    f = open(file_path, "w+")
    f.write(strings)
    f.close()

if __name__ == "__main__":
    print main()
