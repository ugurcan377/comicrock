import os
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import cfscrape


from comicrock.comicrock import ComicRock


class RCODriver(ComicRock):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://readcomiconline.to'
        self.book_url = urljoin(self.base_url, 'Comic/')
        self.chapter_selector = '.listing tr td a'
        self.book_name_selector = '.bigChar'
        self.scraper = cfscrape.create_scraper()

    def get_html(self, link):
        r = self.scraper.get(link)
        if not r.ok:
            raise Exception("Book Not Found")
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def download_series(self, url, start=0, end=-1, dry_run=False):
        soup = self.get_html(url)
        book_name = self.get_book_name(url, soup=soup)
        chapter_list = [urljoin(self.base_url, x['href']) for x in soup.select(self.chapter_selector) if 'TPB' not in x['href']]
        book_path = os.path.join(self.download_path, book_name)
        os.makedirs(book_path, exist_ok=True)
        serialized_book_name = url.rpartition('/')[-1]
        if end < 0:
            end = len(chapter_list)
        print('This book has {} issues.'.format(len(chapter_list)))
        chapter_list.reverse()
        for chapter_url in chapter_list:
            chapter_no = urlparse(chapter_url).path.rpartition('/')[-1].split('-')[-1]
            no = int(chapter_no)
            if start <= no <= end:
                chapter_url += '&readType=1'
                self.download_issue(chapter_no, chapter_url, book_name, serialized_book_name, book_path, dry_run)
        return book_path

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        soup = self.get_html(url)
        issue_name = '{name}-{no}'.format(name=book_name, no='{0:03d}'.format(int(no)))
        issue_path = os.path.join(book_path, issue_name)
        archive_path = os.path.join(book_path, issue_name)
        js_text = soup.findAll('script', type="text/javascript")
        regex = re.compile('lstImages.push\("(.*)"\);')
        try:
            page_list = regex.findall(js_text[4].text)
        except IndexError:
            raise Exception('There is something wrong with page Javascript!\nProbably a wild Captcha appeared')
        if not dry_run:
            if len(page_list) == 0:
                fp = open(os.path.join(self.download_path, 'html-log.txt'), 'w')
                fp.write(str(soup))
                fp.close()
                raise Exception('No page found! Probably a wild Captcha appeared')
            if os.path.exists(archive_path+'.cbz'):
                return 0
            os.makedirs(issue_path, exist_ok=True)
            for page, page_url in enumerate(page_list):
                print('Downloading Issue #{} Page {}'.format(no, '{0:02d}'.format(page+1)), end='\r')
                page_path = os.path.join(issue_path, '{0:03d}.jpg'.format(page))
                try:
                    self.download_image(page_url, page_path)
                except Exception:
                    print('Error on saving page {} of {} issue {}'.format(page, book_name, no))
            self.package_issue(archive_path, issue_path)
        else:
            print(issue_path)
            print('Issue #{}, URL: {}, Pages: {}'.format(no, url, len(page_list)))
