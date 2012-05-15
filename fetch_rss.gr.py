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

from subprocess import call
from md5 import new as md5

sys.path.append("/home/ryan/local/scripts/python")
import internet_util, image_util
import gen_html, nav_aid, google_reader

def main():

    base_folder = "/home/ryan/local/scripts/kindle/fetch_rss/output"
    timestamp = time.strftime("%Y.%m.%d %H:%M")

    # fetch article
    feed_list_url = ("https://www.google.com/reader"
                     "/public/subscriptions/user/-/label/Featured")
    gr = google_reader.GoogleReader(feed_list_url=feed_list_url)
    feed_content_list = gr.fetch_articles()
    if not feed_content_list:
        return "No new items."

    # make html
    article_sum = gr.get_sum()
    file_name = "Featured Articles (%s)" % article_sum
    file_folder = os.path.join(base_folder, file_name)
    # create a folder to storage images.
    try:
        os.mkdir(file_folder)
    except OSError:
        pass

    # trans article_sum to mark the progress with left count
    html, outline = gen_html.gen_html(feed_content_list, article_sum)
    nav_aid.make_nav_aid(file_folder, outline)
    html_with_images = internet_util.fetch_images(html, file_folder, timeout=5.0)

    # output files
    file_abs_path = "%s.html" % file_folder
    with open(file_abs_path, "w+") as f:
        f.write(html_with_images)

    gr.mark_all_as_read()

    texts = [(file_name, (150, 100)), (timestamp, (140, 650))]
    covertmp_abs_path = "%s/cover_temp.jpg" % base_folder
    cover_abs_path = "%s/cover.jpg" % base_folder
    image_util.add_texts_to_image(texts, covertmp_abs_path, cover_abs_path)

    opf_file = "%s.opf" % file_folder
    call(["kindlegen", opf_file])

    return "Finished!"

if __name__ == "__main__":
    print main()

