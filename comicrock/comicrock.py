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
        self.db_path = os.path.join(self.download_path, '.db.json')
        self.fav_path = os.path.join(self.download_path, '.fav')
        self.base_url = ''
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

    def get_book_name(self, key, soup=None):
        url = self.get_book_url(key)
        if soup is None:
            soup = self.get_html(url)
        name = soup.select(self.book_name_selector)[0].text
        return name.replace('/', ' ').replace('-)', ')').replace(':', '')

    def get_metadata(self, soup):
        author_fields = soup.select(self.author_selector)
        author_tag = [x for x in author_fields if x.text == 'Author:'][0]
        genre_fields = soup.select(self.genre_selector)
        return {'author': [x.text.strip().split(', ') for x in author_tag.parent.next_siblings if x != '\n'][0],
                'genre': [x.text for x in genre_fields]}

    def get_comic_list(self):
        soup = self.get_html(self.search_url)
        return soup.select(self.comic_selector)

    def get_fav_list(self):
        try:
            with open(self.fav_path, 'r') as f:
                fav_list = f.readlines()
        except FileNotFoundError:
            with open(self.fav_path, 'a+') as f:
                fav_list = []
        return [fav.strip() for fav in fav_list]

    def download_series(self, url, start=0, end=-1, dry_run=False):
        pass

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        pass

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
