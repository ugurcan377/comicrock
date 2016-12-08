from io import BytesIO
import os
import shutil
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PIL import Image
import requests


class ComicRock(object):

    def __init__(self):
        self.download_path = os.path.expanduser('~/comics')
        self.db_path = os.path.join(self.download_path, 'db.json')
        self.base_url = 'http://readcomics.tv'
        self.search_url = urljoin(self.base_url, 'comic-list')
        self.book_url = urljoin(self.base_url, 'comic/')
        self.image_url = urljoin(self.base_url, 'images/manga/')
        self.chapter_selector = '.ch-name'
        self.book_name_selector = 'td strong'
        self.author_selector = '.manga-details td span'
        self.genre_selector = '.manga-details td a'
        self.comic_selector = '.serie-box ul li a'

    def get_html(self, link):
        r = requests.get(link)
        if not r.ok:
            raise requests.HTTPError("Book Not Found")
        soup = BeautifulSoup(r.text, 'html.parser')
        return soup

    def get_book_url(self, key):
        return urljoin(self.book_url, key)

    def get_book_name(self, url, soup=None):
        if soup is None:
            soup = self.get_html(url)
        name = soup.select(self.book_name_selector)[0].text
        return name.replace('/', '-')

    def get_metadata(self, soup):
        author_fields = soup.select(self.author_selector)
        author_tag = [x for x in author_fields if x.text == 'Author:'][0]
        genre_fields = soup.select(self.genre_selector)
        return {'author': [x.text.strip().split(', ') for x in author_tag.parent.next_siblings if x != '\n'][0],
                'genre': [x.text for x in genre_fields]}

    def get_comic_list(self):
        soup = self.get_html(self.search_url)
        return soup.select(self.comic_selector)

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
            chapter_no = chapter_url.rpartition('/')[-1].split('-')[-1]
            no = int(chapter_no)
            if start <= no <= end:
                self.download_issue(chapter_no, chapter_url, book_name, serialized_book_name, book_path, dry_run)
        return book_path

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        soup = self.get_html(url)
        page_count = soup.select('div.ct-right div.label')[0].text
        page_count = [int(s) for s in page_count.split() if s.isdigit()][0]
        issue_name = '{name}-{no}'.format(name=book_name, no='{0:03d}'.format(int(no)))
        issue_path = os.path.join(book_path, issue_name)
        archive_path = os.path.join(book_path, issue_name)
        if not dry_run:
            if os.path.exists(archive_path+'.cbz'):
                return 0
            os.makedirs(issue_path, exist_ok=True)
            for page in range(1, page_count+1):
                print('Downloading Issue #{} Page {} of {}'.format(no, '{0:02d}'.format(page), page_count), end='\r')
                page_url = urljoin(self.image_url, '{book}/{chapter}/{page}.jpg'.format(book=serialized_book_name,
                                                                                        chapter=no, page=page))
                page_path = os.path.join(issue_path, '{0:03d}.jpg'.format(page))
                try:
                    self.download_image(page_url, page_path)
                except Exception:
                    print('Error on saving page {} of {} issue {}'.format(page, book_name, no))
            self.package_issue(archive_path, issue_path)
        else:
            print('Issue #{}, URL: {}, Pages: {}'.format(no, url, page_count))
            print('Issue Path: {}'.format(issue_path))

    def package_issue(self, archive_path, issue_path):
        shutil.make_archive(archive_path, 'zip', issue_path)
        os.rename(archive_path + '.zip', archive_path + '.cbz')
        shutil.rmtree(issue_path)

    def download_image(self, url, path):
        r = requests.get(url)
        i = Image.open(BytesIO(r.content))
        try:
            i.load()
        except IOError:
            pass
        i.save(path)
