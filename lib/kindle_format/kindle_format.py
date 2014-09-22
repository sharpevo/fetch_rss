import os, sys
from md5 import new as md5
from subprocess import Popen, PIPE
from lib.internet_util import internet_util
from lib.image_util import image_util


class Periodical():
    """Make kindle format supportive from html."""

    def __init__(self,
                 title="title",
                 file_folder="/home/ryan/local/scripts/kindle/pub",
                 file_name="index"):

        self.section_list = []

        self.title = title
        self.file_folder = file_folder
        self.file_name = file_name
        self.uid = md5(file_name).hexdigest()

        path_prefix = os.path.join(file_folder, file_name)
        self.html_rel_path = self.make_path("html", file_name)
        self.html_abs_path = self.make_path("html", path_prefix)
        self.ncx_rel_path = self.make_path("ncx", file_name)
        self.ncx_abs_path = self.make_path("ncx", path_prefix)
        self.opf_abs_path = self.make_path("opf", path_prefix)
        self.mobi_abs_path = self.make_path("mobi", path_prefix)

    def make_path(self, file_ext, file_name):
        return "%s.%s" % (file_name, file_ext)

    # depre
    def add_section(self, sect_title):
        self.section_list.append(Section(sect_title))

    # dpre
    def add_item(self, title="", content="", section_index=-1):
        self.add_item(title, content, section_index=section_index)

    # dpre
    def add_item(self, title, content, section_index=-1):
        section = self.section_list[section_index]
        item = Item(title=title, content=content)
        section.add_item(item)

    def append_section(self, sect_title):
        self.section_list.append(Section(sect_title))

    def append_item(self, title, content):
        section = self.section_list[-1]
        item = Item(title=title, content=content)
        section.add_item(item)

    def gen_html(self, fetch_image=True):

        print "> Generate html..."

        section_html_list = [section.make_html(sect_count) \
                             for sect_count, section in enumerate(self.section_list)]
        sect_title_temp = '<li><a href="#sect_%(sect_count)s">%(title)s</a></li>'
        sect_title_list = [ sect_title_temp % \
                           dict(sect_count=sect_count, title=section.title) \
                           for section in self.section_list]

        html = Html(self.title,
                    self.html_abs_path,
                    "".join(section_html_list),
                    "".join(sect_title_list),
                    fetch_image=fetch_image)
        html.output()

    def gen_ncx(self):

        print "> Generate ncx..."

        section_navp_list = [section.make_navp(sect_count, self.html_rel_path) \
                             for sect_count, section in enumerate(self.section_list)]
        ncx = Ncx(ncx_abs_path=self.ncx_abs_path,
                  uid=self.uid,
                  title=self.title,
                  sect_navp="".join(section_navp_list),
                  html_rel_path=self.html_rel_path)
        ncx.output()

    def gen_opf(self):

        print "> Generate opf..."

        opf = Opf(opf_abs_path=self.opf_abs_path,
                  uid=self.uid,
                  title=self.title,
                  html_rel_path=self.html_rel_path,
                  ncx_rel_path=self.ncx_rel_path)
        opf.output()

    def gen_mobi(self):

        print "> Generate mobi..."

        Popen(("kindlegen", self.opf_abs_path), stdout=PIPE) #, stderr=PIPE)

    def send_to_calibre(self, library_path="/media/Resources/KindleSource/News"):

        print "> Send to Calibre..."

        cmd = ["calibredb",
               "add",
               "--library-path", library_path,
               "-d", self.mobi_abs_path]
        # cmd = "calibredb add --library-path %s -d %s" % (library_path, self.mobi_abs_path)
        Popen(cmd, stdout=PIPE, stderr=PIPE)

    def output(self, fetch_image=True,
               library_path="/media/Resources/KindleSource/News"):
        self.gen_html(fetch_image=fetch_image)
        self.gen_ncx()
        self.gen_opf()
        self.gen_mobi()
        self.send_to_calibre(library_path)


class Section():

    SECT_HTML_TEMP = '''
    <div id="section_%(sect_count)s" class="section">
        <h2 class="sect_title">%(title)s</h2>
        %(items)s
    </div>
    <mbp:pagebreak/>
    '''
    SECT_NAVP_TEMP = '''
    <navPoint class="section" id="%(sect_count)s">
        <navLabel><text>%(title)s</text></navLabel>
        <content src="%(html)s#section_%(sect_count)s" />
        %(items)s
    </navPoint>
    '''

    def __init__(self, title):
        self.title = title
        self.item_list = []

    def add_item(self, item):
        self.item_list.append(item)

    def make_html(self, sect_count):
        item_html_list = [item.make_html(sect_count, item_count) \
                          for item_count, item in enumerate(self.item_list)]
        return self.SECT_HTML_TEMP % dict(title=self.title,
                                          sect_count=sect_count,
                                          items="".join(item_html_list))
    def make_navp(self, sect_count, html_rel_path):
        item_navp_list = [item.make_navp(sect_count, item_count, html_rel_path) \
                          for item_count, item in enumerate(self.item_list)]
        return self.SECT_NAVP_TEMP % dict(title=self.title,
                                          sect_count=sect_count,
                                          html=html_rel_path,
                                          items="".join(item_navp_list))

class Item():

    ITEM_HTML_TEMP = '''
    <div id="item_%(sect_count)s_%(item_count)s" class="item">
        <h3 class="item_title">%(title)s</h3>
        <div class="item_content">%(content)s</div>
    </div>
    <mbp:pagebreak/>
    '''

    ITEM_NAVP_TEMP = '''
    <navPoint class="article" id="%(sect_count)s_%(item_count)s" playOrder="%(item_count)s">
      <navLabel><text>%(title)s</text></navLabel>
      <content src="%(html)s#item_%(sect_count)s_%(item_count)s" />
    </navPoint>
    '''

    def __init__(self,title="", content=""):
        self.title = title
        self.content = content

    def make_html(self, sect_count, item_count):
        return self.ITEM_HTML_TEMP % dict(title=self.title,
                                          sect_count=sect_count,
                                          item_count=item_count,
                                          content=self.content)

    def make_navp(self, sect_count, item_count, html_rel_path):
        return self.ITEM_NAVP_TEMP % dict(title=self.title,
                                          sect_count=sect_count,
                                          item_count=item_count,
                                          html=html_rel_path)

class Html():

    HTML_TEMP = '''
    <html>
      <head>
          <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
          <link rel="stylesheet" href="/home/ryan/local/scripts/kindle/pub/content.css" type="text/css"/>
      </head>
      <body>
          <div id="cover">
              <h1 id="title">%(title)s<img src="cover.jpg" width=0 height=0/></h1>
          </div>
          <div id="content">
              %(sections)s
          </div>
      </body>
    </html>
    '''

    def __init__(self, title, html_abs_path, section_html, sect_title_list, fetch_image=True):
        self.html_abs_path = html_abs_path
        self.html = self.HTML_TEMP % dict(title=title,
                                          sections=section_html,
                                          sect_title="".join(sect_title_list))
        self.fetch_image = fetch_image

    def output(self):
        if self.fetch_image:
            self.html = internet_util.fetch_images(self.html,
                                                   self.html_abs_path.rpartition(".")[0],
                                                   timeout=5.0)
        with open(self.html_abs_path, "w+") as f:
            f.write(self.html)

class Ncx():

    # uid, title, html
    NCX_TEMP = '''
    <?xml version="1.0" encoding="UTF-8"?>
    <ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh">
    <head>
    <meta name="dtb:uid" content="%(uid)s" />
    <meta name="dtb:depth" content="4" />
    <meta name="dtb:totalPageCount" content="0" />
    <meta name="dtb:maxPageNumber" content="0" />
    </head>
    <docTitle><text>%(title)s</text></docTitle>
    <docAuthor><text>Ryan Woo</text></docAuthor>
    <navMap>
        <navPoint class="periodical">
            <navLabel><text>%(title)s</text></navLabel>
            <content src="%(html)s" />
            %(sect_navp)s
        </navPoint>
    </navMap>
    </ncx>
    '''

    def __init__(self,
                 uid="", title="", sect_navp="",
                 html_rel_path="",  ncx_abs_path=""):
        self.ncx_abs_path = ncx_abs_path
        self.ncx = self.NCX_TEMP % dict(uid=uid,
                                        title=title,
                                        html=html_rel_path,
                                        sect_navp=sect_navp)

    def output(self):
        with open(self.ncx_abs_path, "w+") as f:
            f.write(self.ncx)

class Opf():

    OPF_TEMP = '''
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
        <item id="css" media-type="text/css" href="/home/ryan/local/scripts/kindle/pub/content.css" />
        <item id="cover_id" media-type="image/jpeg" href="cover.jpg"/>
        <item id="content" media-type="application/xhtml+xml" href="%(html)s"></item>
        <item id="toc" media-type="application/x-dtbncx+xml" href="%(ncx)s"></item>
    </manifest>

    <spine toc="toc">
        <itemref idref="content"/>
    </spine>

    <guide>
        <reference type="start" title="start" href="%(html)s#content"></reference>
        <reference type="text" title="cover" href="%(html)s#cover"></reference>
    </guide>
    </package>
    '''

    def __init__(self, opf_abs_path="", uid="", title="",
                 html_rel_path="", ncx_rel_path=""):
        self.opf_abs_path = opf_abs_path
        self.opf = self.OPF_TEMP % dict(uid=uid,
                                        title=title,
                                        html=html_rel_path,
                                        ncx=ncx_rel_path)
    def output(self):
        with open(self.opf_abs_path, "w+") as f:
            f.write(self.opf)
