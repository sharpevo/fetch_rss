#!/usr/bin/env python2
from md5 import new as md5

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

