import os
from io import BytesIO
from urllib.parse import urljoin, quote

import requests
from PIL import Image

from comicrock.comicrock import ComicRock


class RCBDriver(ComicRock):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://readcomicbooksonline.com'
        self.book_url = self.base_url
        self.chapter_selector = '.chapter a'
        self.book_name_selector = '.page-title'
        self.author_selector = '#statsblock td.title'
        self.comic_selector = '#primary .field-content a'
        self.search_url = urljoin(self.base_url, 'comics-list')

    def get_metadata(self, soup):
        fields = soup.select(self.author_selector)
        author_tag = [x for x in fields if x.text == 'Author/Artist'][0]
        publisher_tag = [x for x in fields if x.text == 'Publisher'][0]
        genre_tag = [x for x in fields if x.text == 'Genres'][0]
        return {'author': [x.text.strip().split(', ') for x in author_tag.next_siblings if x != ' '][0],
                'genre': [x.text.strip().split(', ') for x in genre_tag.next_siblings if x != ' '][0],
                'publisher': [x.text.strip() for x in publisher_tag.next_siblings if x != ' '][0]}

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
        chapter_list.reverse()
        for chapter_url in chapter_list:
            chapter_no = chapter_url.rpartition('/')[-1].split('_')[-1]
            no = int(chapter_no)
            if start <= no <= end:
                self.download_issue(chapter_no, chapter_url, book_name, serialized_book_name, book_path, dry_run)
        return book_path

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        soup = self.get_html(url)
        if len(soup.select('.placeholder')) > 0:
            print('Issue #{} was a placeholder page. Sorry!'.format(no))
            return -1
        page_count = soup.select('select[name="page"] option')
        page_count = int(len(page_count) / 2)
        issue_name = '{name}-{no}'.format(name=book_name, no='{0:03d}'.format(int(no)))
        issue_path = os.path.join(book_path, issue_name)
        issue_base_url = url.rpartition('/')[0]
        image_path = soup.select('.picture')[0]['src'][:-7]
        page_base_url = urljoin(issue_base_url, quote(image_path)) + '{0:03d}.jpg'
        archive_path = os.path.join(book_path, issue_name)
        if not dry_run:
            if os.path.exists(archive_path+'.cbz'):
                return 0
            os.makedirs(issue_path, exist_ok=True)
            for page in range(1, page_count+1):
                print('Downloading Issue #{} Page {} of {}'.format(no, '{0:02d}'.format(page), page_count), end='\r')
                page_url = page_base_url.format(page)
                page_path = os.path.join(issue_path, '{0:03d}.jpg'.format(page))
                try:
                    self.download_image(page_url, page_path)
                except Exception:
                    print('Error on saving page {} of {} issue {}'.format(page, book_name, no))
            self.package_issue(archive_path, issue_path)
        else:
            print('Issue #{}, URL: {}, Pages: {}'.format(no, url, page_count))
            print('Issue Path: {}, Image URL {}'.format(issue_path, page_base_url))

    def download_image(self, url, path):
        headers = {
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'en-US,en;q=0.8,tr;q=0.6',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/53.0.2785.143 Chrome/53.0.2785.143 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': url,
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
        r = requests.get(url, headers=headers)
        i = Image.open(BytesIO(r.content))
        try:
            i.load()
        except IOError:
            pass
        i.save(path)