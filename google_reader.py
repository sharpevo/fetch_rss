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
import time


import urllib, urllib2
from BeautifulSoup import BeautifulSoup as BS
import lxml.html

AUTH_URL = 'https://www.google.com/accounts/ClientLogin'
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


class GoogleReader():


    def __init__(self,
                 username="seasideryan@gmail.com",
                 password="youpomian",
                 feed_list_url=("https://www.google.com/reader"
                                "/public/subscriptions/user/-/label/Featured")):
        self.list_to_mark = []
        self.article_sum = 0
        self._authorize(username, password)
        self.feed_url_list = self.parse_feeds(feed_list_url)

    def get_sum(self):
        return self.article_sum

    def _authorize(self, username, password):

        print "> Waiting for GR auth..."

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
        self.header = {"Authorization": "GoogleLogin auth=%s" % AUTH}

    def get_resp(self, url, data=""):
        if data:
            req = urllib2.Request(url, data, self.header)
        else:
            req = urllib2.Request(url, None, self.header)

        try:
            resp = urllib2.urlopen(req)
            return resp.read()
        except: # URLError
            print "::Error while getting response from", url
        return None

    def parse_feeds(self, feed_list_url):

        print "> ParsingFeeds..."

        resp = self.get_resp(feed_list_url)
        html = lxml.html.fromstring(resp)
        feeds = html.xpath("//outline[@type='rss']")
        feed_url_list = [self.parse_feed(feed) for feed in feeds if self.has_unread(feed.get("xmlurl"))]
        print "    %s/%s unread feeds" % (len(feed_url_list), len(feeds))
        return feed_url_list

    def parse_feed(self, feed):

        feed_title = feed.get("text")
        feed_xml_url = feed.get("xmlurl")
        feed_html_url = feed.get("htmlurl")
        google_url, feed_quote_url = feed_html_url.split("/view/")
        unread_param = "n=1000&xt=user/-/state/com.google/read"
        feed_url = "%s/%s/%s?%s" % (google_url.replace("http", "https"),
                                    "atom",
                                    feed_quote_url,
                                    unread_param)
        return (feed_title, feed_url, feed_xml_url)

    def has_unread(self, feed_xml_url):
        unread_url = "http://www.google.com/reader/api/0/unread-count?all=true"
        html = lxml.html.fromstring(self.get_resp(unread_url))
        unread_feed_list = html.xpath("//string")
        for feed in unread_feed_list:
            if feed_xml_url in feed.text:
                return True
        return False


    def fetch_articles(self):
        """
        Articles may be ill formed html, such us contain "<>"
        Use BS
        """
        print "> Fetching Articles..."

        feed_content_list = [self.fetch_article(tit, html, xml) for tit, html, xml in self.feed_url_list]
        return feed_content_list

    def fetch_article(self, feed_title, feed_html_url, feed_xml_url):
        soup = BS(self.get_resp(feed_html_url),
                  convertEntities="html")
        # titles = soup.findAll("title", attrs={"type":"html"})
        # article_titles = [title for title in titles if feed_title not in title]
        # article_titles = [title for title in titles if feed_title not in title]
        # contents = soup.findAll("summary") or soup.findAll("content")

        entries = soup.findAll("entry")

        article_sum = len(entries)
        self.article_sum += article_sum
        print "    Fetch %s articles from %s" % (article_sum, feed_title)
        # article_list = [(article_titles[i], contents[i]) for i in range(article_sum)]
        article_list = [(entries[i].title, entries[i].content or entries[i].summary) for i in range(article_sum)]
        self.list_to_mark.append(feed_xml_url)
        return (feed_title, article_list)

    def mark_all_as_read(self):
        self.token = self.get_resp("http://www.google.com/reader/api/0/token")
        for feed_xml_url in self.list_to_mark:
            self.mark_all_as_read_for_feed(feed_xml_url)

    def mark_all_as_read_for_feed(self, feed_xml_url):
        req_url = "https://www.google.com/reader/api/0/mark-all-as-read"
        req_data = urllib.urlencode({"s":"feed/%s" % feed_xml_url,
                                     "T":self.token,
                                     "ts":int(time.time())})

        try:
            resp = self.get_resp(req_url, data=req_data)
            print "       Mark items in %s as read" % feed_xml_url
        except:
            print "Error while marking items as read in %s" % feed_xml_url
