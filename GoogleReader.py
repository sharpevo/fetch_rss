#!/usr/bin/env python2
"""
Functions based on Google Reader API.
# Feeds under folder Featured
# http://www.google.com/reader/public/subscriptions/user/-/label/Featured
# or
# http://www.google.com/reader/public/subscriptions/user/10190748274335693350/label/Featured

# articles each feeds
# https://www.google.com/reader/atom/feed/http://feed.feedsky.com/iheima

# feed in folder
# http://www.google.com/reader/view/feed%2Fhttp%3A%2F%2Fplanet.archlinux.org%2Frss20.xml

"""
import time, base64
import urllib, urllib2
from BeautifulSoup import BeautifulSoup as BS
import lxml.html

AUTH_URL = 'https://www.google.com/accounts/ClientLogin'
UNREAD_URL = "http://www.google.com/reader/api/0/unread-count?all=true"
google_url = 'http://www.google.com'
reader_url = google_url + '/reader'
token_url = reader_url + '/api/0/token'
subscription_list_url = reader_url + '/api/0/subscription/list'
reading_url = reader_url + '/atom/user/-/state/com.google/reading-list'
read_items_url = reader_url + '/atom/user/-/state/com.google/read'
reading_tag_url = reader_url + '/atom/user/-/label/%s'
starred_url = reader_url + '/atom/user/-/state/com.google/starred'
subscription_url = reader_url + '/api/0/subscription/edit'
get_feed_url = reader_url + '/atom/feed/'

class Feed():

    def __init__(self, title="", html_url="", xml_url="", articles=[] ):
        self.title = title
        self.html_url = html_url
        self.xml_url = xml_url
        self.articles = articles

class Article():

    def __init__(self, title="", desc=""):
        self.title = title
        self.desc = desc

class GoogleReader():

    def __init__(self,
                 username, password,
                 feed_list_url=("https://www.google.com/reader"
                                "/public/subscriptions/user/-/label/Featured")):
        self.header = self.authorize(username, password)
        self.feed_list_url = feed_list_url
        self.unread_objects = self.gen_unread_objects()

    def gen_unread_objects(self):
        '''
        unread xml structure:
            <object>
            <string name="id">feed/http://feed.feedsky.com/iheima</string>
            <number name="count">21</number>
            <number name="newestItemTimestampUsec">1337221206164209</number></object>
        '''
        resp = self.get_resp(UNREAD_URL)
        html = lxml.html.fromstring(resp)
        unread_objects = html.xpath("//object")[1:] # remove root obj
        return unread_objects

    def get_amount(self):
        label_string = "/".join(self.feed_list_url.split("/")[-2:])
        for unread_object in self.unread_objects:
            if label_string in unread_object.find("string").text:
                return int(unread_object.find("number").text)
        return 0

    def authorize(self, username, password):

        print "> Waiting for GR Auth..."

        auth_req_data = urllib.urlencode({"Email": username,
                                          "Passwd": password,
                                          "service": "reader"})
        auth_req = urllib2.Request(AUTH_URL,
                                   data=auth_req_data)
        ## auth_resp.split("\n"), with a '', so need if x
        # SID=DQAAALcA...wPT2\n
        # LSID=DQAAALk...AAB7\n
        # Auth=DQAAALg...B7h9\n
        #
        auth_resp = urllib2.urlopen(auth_req).read()

        # dict([["1","a"],["2","b"]]), dict sequence element#0 requires 2 arguments.
        # {'1': 'a', '2': 'b'}
        auth_resp_dict = dict(x.split("=") for x in auth_resp.split("\n") if x)

        AUTH = auth_resp_dict["Auth"]
        header = {"Authorization": "GoogleLogin auth=%s" % AUTH}
        return header

    def get_resp(self, url, data=""):
        if data:
            req = urllib2.Request(url, data, self.header)
        else:
            req = urllib2.Request(url, None, self.header)

        try:
            resp = urllib2.urlopen(req)
            return resp.read()
        except: # URLError
            print "Error while getting response from", url
        return None

    def parsing_feeds(self, feed_list_url):
        '''
        outline structure:
            <outline
            text="@iheima"
            title="@iheima"
            type="rss"
            xmlUrl="http://feed.feedsky.com/iheima"
            htmlUrl="http://www.google.com/reader/view/"
                    "feed%2Fhttp%3A%2F%2Ffeed.feedsky.com%2Fiheima"/>

        '''

        print "> Parsing Feeds..."

        resp = self.get_resp(feed_list_url)
        html = lxml.html.fromstring(resp)
        all_feeds_obj = html.xpath("//outline[@type='rss']")
        unread_xml_urls = [obj.find("string").text for obj in self.unread_objects]
        unread_feeds = [self.parse_feed(feed_obj)
                        for feed_obj in all_feeds_obj
                        if ("feed/%s" % feed_obj.get("xmlurl")) in unread_xml_urls]
        print "    %s/%s unread feeds" % (len(unread_feeds), len(all_feeds_obj))
        return unread_feeds

    def parse_feed(self, feed_obj):

        feed_title = feed_obj.get("text")
        feed_xml_url = feed_obj.get("xmlurl")
        feed_html_url = feed_obj.get("htmlurl")
        google_url, feed_quote_url = feed_html_url.split("/view/")
        unread_param = "n=1000&xt=user/-/state/com.google/read"
        feed_url = "%s/%s/%s?%s" % (google_url.replace("http", "https"),
                                    "atom",
                                    feed_quote_url,
                                    unread_param)
        return Feed(title=feed_title,
                    html_url=feed_url,
                    xml_url=feed_xml_url)
    def fetch_feeds(self):
        """
        Articles may be ill formed html, such us contain "<>"
        Use BS
        """
        self.unread_feeds = self.parsing_feeds(self.feed_list_url)
        print "> Fetching Articles..."
        for feed in self.unread_feeds:
            self.fetch_article(feed)

    def fetch_article(self, feed):

        # keep content in code and pre as original one, avoid adding space after span.
        BS.QUOTE_TAGS = {"pre":None, "code":None}

        soup = BS(self.get_resp(feed.html_url),
                  convertEntities="html")
        art_objects = soup.findAll("entry")
        article_amount = len(art_objects)
        print "    Fetch %2d articles from %s" % (article_amount, feed.title)
        feed.articles = [Article(title=art_objects[i].title.string,
                                 desc=art_objects[i].content or art_objects[i].summary)
                         for i in range(article_amount)]

    def mark_all_as_read(self):
        self.token = self.get_resp("http://www.google.com/reader/api/0/token")
        print "> Mark items as read..."
        for feed in self.unread_feeds:
            self.mark_all_as_read_for_feed(feed.xml_url)

    def mark_all_as_read_for_feed(self, feed_xml_url):
        req_url = "https://www.google.com/reader/api/0/mark-all-as-read"
        req_data = urllib.urlencode({"s":"feed/%s" % feed_xml_url,
                                     "T":self.token,
                                     "ts":int(time.time())})
        try:
            resp = self.get_resp(req_url, data=req_data)
            print "    Mark Items in %s" % feed_xml_url
        except:
            print "Error while marking items as read in %s" % feed_xml_url
