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

import os, time, base64


from subprocess import Popen, PIPE

from md5 import new as md5

sys.path.append("/home/ryan/local/scripts/python")
import internet_util, image_util
from GoogleReader import GoogleReader
def main():

    print "\n***** Fetch Rss from Google Reader *****\n"

    base_folder = "/home/ryan/local/scripts/kindle/fetch_rss/output"
    timestamp = time.strftime("%Y.%m.%d %H:%M")

    # fetch article
    feed_list_url = ("https://www.google.com/reader"
                     "/public/subscriptions/user/-/label/Fun")
    username = base64.b64decode("c2Vhc2lkZXJ5YW5AZ21haWwuY29t")
    password = base64.b64decode("eW91cG9taWFu")
    gr = GoogleReader(username=username, password=password)
    # gr = GoogleReader(username=username, password=password,feed_list_url=feed_list_url)

    print "> Counting Articles..."

    article_amount = gr.get_amount()
    if not article_amount:
        output_rst("> No new items.")
        return

    input_char = ""
    while input_char.lower() not in ["y", "n"]:
        input_char = raw_input("    Fetch all %s articles? (y or n)" % article_amount)
        if input_char == "y":
            break
        elif input_char == "n":
            output_rst("> Abort to fetching articles.")
            return

    feed_content_list = gr.fetch_articles()
    file_name = "Featured Articles (%s)" % article_amount
    file_folder = os.path.join(base_folder, file_name)
    # create a folder to storage images.
    try:
        os.mkdir(file_folder)
    except OSError:
        pass

    # trans article_sum to mark the progress with left count
    html, outline = gen_html(feed_content_list, article_amount)
    make_nav_aid(file_folder, outline)
    html_with_images = internet_util.fetch_images(html, file_folder, timeout=5.0)

    # output files
    file_abs_path = "%s.html" % file_folder
    output(file_abs_path, html_with_images)

    gr.mark_all_as_read()

    texts = [(file_name, (150, 100)), (timestamp, (160, 650))]
    covertmp_abs_path = "%s/cover_temp.jpg" % base_folder
    cover_abs_path = "%s/cover.jpg" % base_folder
    image_util.add_texts_to_image(texts, covertmp_abs_path, cover_abs_path)

    print "> Convert to mobi..."

    opf_file = "%s.opf" % file_folder
    Popen(("kindlegen", opf_file), stdout=PIPE, stderr=PIPE)

    output_rst("Finished!")

def output_rst(text):
    print "****************************************\n%s" % text

#######################################################################################
# opf file template.

# uid, file_title, html, ncx
OPF = '''
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

#######################################################################################
# ncx file template

# uid, title, html
NCX = '''
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
NAV_SEC = '''
<navPoint class="section" id="%(sec_count)s">
    <navLabel><text>%(title)s</text></navLabel>
    <content src="%(html)s#section_%(sec_count)s" />
    %(nav_arts)s
</navPoint>
'''
# sec, art count, html, article_title
NAV_ART = '''
<navPoint class="article" id="%(sec_count)s_%(art_count)s" playOrder="%(art_count)s">
  <navLabel><text>%(title)s</text></navLabel>
  <content src="%(html)s#article_%(sec_count)s_%(art_count)s" />
</navPoint>
'''

def make_nav_aid(file_folder, outline):

    file_name = file_folder.rpartition("/")[2]
    uid = md5(file_name).hexdigest()
    html_rel_path = make_path(".html", file_name)
    ncx_rel_path = "%s.ncx" % file_name

    # opf

    opf = OPF % dict(uid=uid,
                     title=file_name,
                     html=html_rel_path,
                     ncx=ncx_rel_path)
    opf_abs_path = make_path(".opf", file_folder)
    output(opf_abs_path, opf)

    # ncx

    nav_secs = []
    feed_count = 0
    for feed_title, feed_article_titles in outline:
        feed_count += 1

        art_count = 0
        nav_arts = []
        for article in feed_article_titles:
            art_count += 1
            nav_arts.append(NAV_ART % dict(sec_count=feed_count,
                                           art_count=art_count,
                                           title=article,
                                           html=html_rel_path))
        nav_secs.append(NAV_SEC % dict(sec_count=feed_count,
                                       title=feed_title,
                                       html=html_rel_path,
                                       nav_arts="".join(nav_arts)))
    ncx = NCX % dict(uid=uid,
                     title=file_name,
                     html=html_rel_path,
                     nav_secs="".join(nav_secs))

    ncx_abs_path = "%s.ncx" % file_folder
    output(ncx_abs_path, ncx)

def make_path(file_ext, file_path):
    '''
    return relative or absolute path as requst.
    '''
    return "%s%s" % (file_path, file_ext)

def output(file_path, strings):
    with open(file_path, "w+") as f:
        f.write(strings)

#######################################################################################

# html file template.

HTML = '''
<html>
  <head>
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
      <link rel="stylesheet" href="content.css" type="text/css"/>
  </head>
  <body>
    %(cover)s
    %(toc)s
    %(contents)s
  </body>
</html>

'''
COVER = '''
<div id="cover">
  <h1 id="title">Google Reader Featured Articles<img src="cover.jpg" width=0 height=0/></h1>
</div>
'''
CONTENT = '''
<div id="contents">
    %(sections)s
</div>
'''
SECTION = '''
<div id="section_%(count)s" class="section">
    %(articles)s
</div>
<mbp:pagebreak></mbp:pagebreak>
'''
ARTICLE = '''
<div id="article_%(sec_count)s_%(art_count)s" class="article">
    <h2 class="article_title">%(title)s</h2>
    <div class="article_content">%(contents)s</div>
</div>
<mbp:pagebreak></mbp:pagebreak>
'''

# table of contents

TOC = '''
<div id="toc">
    <h2>Feeds</h2>
        <ol>
            %(toc_feeds)s
       </ol>
    <mbp:pagebreak></mbp:pagebreak>
    %(toc_secs)s
</div>
<mbp:pagebreak></mbp:pagebreak>
'''

TOC_FEED = '''
<li>
    <a href="#toc_section_%(sec_count)s">%(title)s</a><br>
    %(art_count)s items.
</li>
'''
TOC_SEC = '''
<div id="toc_section_%(count)s" class="section">
    <h3>%(title)s</h3>
    <ol>
        %(articles)s
    </ol>
</div>
<mbp:pagebreak></mbp:pagebreak>
'''
TOC_ART = '''
<li>
    <a href="#article_%(sec_count)s_%(art_count)s">%(title)s</a>
</li>
'''

def gen_html(feed_content_list, article_amount):

    contents, outline = make_contents(feed_content_list, article_amount)
    toc = make_toc(outline)
    html = make_html(COVER, toc, contents)
    return (html, outline)

def make_html(cover, toc, contents):

    html = HTML % dict(cover=cover,
                       toc=toc,
                       contents=contents)
    return html

def make_contents(feed_content_list, article_amount):
    toc = ""
    contents = ""
    cover = ""
    outline = []

    feed_count = 0
    sections = []
    cur_art_count = 0
    for feed_title, feed_article_list in feed_content_list:
        feed_count += 1

        articles = []
        article_count = 0
        feed_article_titles = []
        for art_title, art_desc in feed_article_list:
            article_count += 1
            left = article_amount - cur_art_count - article_count
            title = "%s&lt; %s" % (left, art_title.string)
            if art_desc:
                content = "".join(art_desc)
            else:
                # if art has no content or summary
                content = ""
            articles.append(ARTICLE % dict(sec_count=feed_count,
                                                art_count=article_count,
                                                title=title,
                                                contents=content))
            feed_article_titles.append(title)
        cur_art_count += article_count
        sections.append(SECTION % dict(count=feed_count,
                                            articles="".join(articles)))
        outline.append((feed_title,feed_article_titles))
    contents = CONTENT % dict(sections="".join(sections))

    return (contents, outline)

def make_toc(outline):

    toc_feed = []
    toc_sec = []
    feed_count = 0
    for feed_title, feed_article_titles in outline:
        feed_count += 1
        art_count = len(feed_article_titles)
        toc_feed.append(TOC_FEED % dict(sec_count=feed_count,
                                        title=feed_title,
                                        art_count=art_count))
        toc_art = []
        art_count = 0
        for article in feed_article_titles:
            art_count += 1
            toc_art.append(TOC_ART % dict(sec_count=feed_count,
                                          art_count=art_count,
                                          title=article))
        toc_sec.append(TOC_SEC % dict(count=feed_count,
                                      title=feed_title,
                                      articles="".join(toc_art)))
    toc = TOC % dict(toc_feeds="".join(toc_feed),
                     toc_secs="".join(toc_sec))
    return toc

if __name__ == "__main__":
    main()

