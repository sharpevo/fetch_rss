#!/usr/bin/env python2

# html file template.

HTML = '''
<html>
  <head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"></head>
  <body>
    %(cover)s
    %(toc)s
    %(contents)s
  </body>
</html>

'''
COVER = '''
<div id="cover">
  <h1 id="title">Google Reader Featured Articles</h1>
  <img src="cover.jpg"/>
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

def gen_html(feed_content_list, article_sum):

    contents, outline = make_contents(feed_content_list, article_sum)
    toc = make_toc(outline)
    html = make_html(COVER, toc, contents)
    return (html, outline)

def make_html(cover, toc, contents):

    html = HTML % dict(cover=cover,
                       toc=toc,
                       contents=contents)
    return html

def make_contents(feed_content_list, article_sum):
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
            cur_art_count += article_count
            left = article_sum - cur_art_count
            title = "%s (%s+)" % (art_title.string, left)
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



