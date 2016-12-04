import json
import re

from comicrock.comicrock import ComicRock

class ComicDatabase(ComicRock):

    def load(self):
        return json.load(open(self.db_path))

    def get_author(self, soup):
        fields = soup.select(self.author_selector)
        author_tag = [x for x in fields if x.text == 'Author:'][0]
        return [x.text.strip().split(', ') for x in author_tag.parent.next_siblings if x != '\n'][0]

    def get_genres(self, soup):
        fields = soup.select(self.genre_selector)
        return [x.text for x in fields]

    def get_comic_list(self):
        soup = self.get_html(self.search_url)
        return soup.select(".serie-box ul li a")

    def create_database(self):
        comics = self.get_comic_list()
        db = {}
        for i, serie in enumerate(comics):
            print("Progress {} out of {}".format(i, len(comics)), end='\r')
            serie_key = serie['href'].rpartition('/')[-1]
            db[serie_key] = {"name": serie.text.replace('/', '-'), "url": serie["href"]}
            soup = self.get_html(serie["href"])
            db[serie_key]["author"] = self.get_author(soup)
            db[serie_key]["genre"] = self.get_genres(soup)
        return db

    def generate(self):
        database = self.create_database()
        print("Generation complete. Saving.")
        json.dump(database, open(self.db_path, 'w'))

    def search(self, db, query, field='name'):
        regex = re.compile(query, re.IGNORECASE)
        if field == 'name':
            return {k:v for k,v in db.items() if regex.search(v[field])}
        else:
            return {k: v for k, v in db.items() if [x for x in v[field] if regex.search(x)]}