import os
from urllib.parse import urljoin

from comicrock.comicrock import ComicRock

class CastleDriver(ComicRock):
    def __init__(self):
        super().__init__()
        self.base_url = 'http://comicastle.org'
        self.book_url = urljoin(self.base_url, 'manga-{key}.html')
        self.chapter_selector = 'h3 ~ table a'
        self.book_name_selector = '.page-header h1#tables'

    def get_book_url(self, key):
        return self.book_url.format(key=key)

    def download_series(self, url, start=0, end=-1, dry_run=False):
        soup = self.get_html(url)
        book_name = self.get_book_name(url, soup=soup)
        chapter_list = [x['href'] for x in soup.select(self.chapter_selector)]
        book_path = os.path.join(self.download_path, book_name)
        os.makedirs(book_path, exist_ok=True)
        serialized_book_name = url.rpartition('/')[-1][6:-5]
        if end < 0:
            end = len(chapter_list)
        print('This book has {} issues.'.format(len(chapter_list)))
        for chapter_url in chapter_list:
            chapter_no = chapter_url.rpartition('/')[-1].split('-')[-1][:-5]
            no = int(chapter_no)
            if start <= no <= end:
                self.download_issue(chapter_no, urljoin(self.base_url, chapter_url), book_name, serialized_book_name,
                                    book_path, dry_run)
        return book_path

    def download_issue(self, no, url, book_name, serialized_book_name, book_path, dry_run):
        soup = self.get_html(url)
        page_count = soup.select('select option')
        page_count = int(len([x for x in page_count if x.text.isdigit()]) / 2)
        issue_name = '{name}-{no}'.format(name=book_name, no='{0:03d}'.format(int(no)))
        issue_path = os.path.join(book_path, issue_name)
        image_path = soup.select('.chapter-img')[0]['src'].strip()[:-7]
        page_base_url = image_path + '{0:03d}.jpg'
        archive_path = os.path.join(book_path, issue_name)
        if not dry_run:
            if os.path.exists(archive_path+'.cbz'):
                return 0
            os.makedirs(issue_path, exist_ok=True)
            for page in range(0, page_count+1):
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
