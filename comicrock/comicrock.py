from io import BytesIO
import os
import re
import shutil
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PIL import Image
import requests


class ComicRock(object):

    def __init__(self):
        self.download_path = os.path.expanduser('~/comics')
        self.base_url = 'http://readcomics.tv'
        self.search_url = urljoin(self.base_url, 'comic-list')
        self.book_url = urljoin(self.base_url, 'comic/')
        self.image_url = urljoin(self.base_url, 'images/manga/')
        self.chapter_selector = '.ch-name'

    def get_html(self, link):
        r = requests.get(link)
        if not r.ok:
            raise requests.HTTPError("Book Not Found")
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def search_comics(self, text):
        soup = self.get_html(self.search_url)
        tag_list = soup.find_all('a', attrs={'class': None}, string=re.compile(text, re.IGNORECASE))
        return [(x.text, x['href'].rpartition('/')[-1]) for x in tag_list]

    def get_book_name(self, url, soup=None):
        if soup is None:
            soup = self.get_html(url)
        name = soup.select('td strong')[0].text
        return name.replace('/', '-')

    def download_series(self, url, start=0, end=-1, dry_run=False):
        soup = self.get_html(url)
        book_name = self.get_book_name(url, soup=soup)
        chapter_list = [x['href'] for x in soup.select(self.chapter_selector)]
        book_path = os.path.join(self.download_path, book_name)
        os.makedirs(book_path, exist_ok=True)
        serialized_book_name = url.rpartition('/')[-1]
        if end < 0:
            end = len(chapter_list)
        print('This book has {} issues.'.format(len(chapter_list)))
        for chapter_url in chapter_list:
            chapter_no = int(chapter_url.rpartition('/')[-1].split('-')[-1])
            if start <= chapter_no <= end:
                self.download_issue(chapter_no, chapter_url, book_name, serialized_book_name, book_path, dry_run)
        return book_path

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        soup = self.get_html(url)
        page_count = soup.select('div.ct-right div.label')[0].text
        page_count = [int(s) for s in page_count.split() if s.isdigit()][0]
        issue_name = '{name}-{no}'.format(name=book_name, no='{0:03d}'.format(no))
        issue_path = os.path.join(book_path, issue_name)
        archive_path = os.path.join(book_path, issue_name)
        if not dry_run:
            if os.path.exists(archive_path+'.cbz'):
                return 0
            os.makedirs(issue_path, exist_ok=True)
            for page in range(1, page_count+1):
                print('Downloading Issue #{} Page {} of {}'.format(no, page, page_count), end='\r')
                page_url = urljoin(self.image_url, '{book}/{chapter}/{page}.jpg'.format(book=serialized_book_name,
                                                                                        chapter=no, page=page))
                page_path = os.path.join(issue_path, '{0:03d}.jpg'.format(page))
                try:
                    self.download_image(page_url, page_path)
                except Exception:
                    print('Error on saving page {} of {} issue {}'.format(page, book_name, no))
            shutil.make_archive(archive_path, 'zip', issue_path)
            os.rename(archive_path+'.zip', archive_path+'.cbz')
            shutil.rmtree(issue_path)
        else:
            print(issue_path)
            print('Issue #{}, URL: {}, Pages: {}'.format(no, url, page_count))

    def download_image(self, url, path):
        r = requests.get(url)
        i = Image.open(BytesIO(r.content))
        try:
            i.load()
        except IOError:
            pass
        i.save(path)