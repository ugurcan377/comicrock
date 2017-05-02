import json
import re
from urllib.parse import urljoin

from comicrock.comicrock import ComicRock
from comicrock.rcb_driver import RCBDriver


class ComicDatabase(ComicRock):

    def load(self):
        return json.load(open(self.db_path))

    def create_database(self, db):
        rcb = RCBDriver()
        # comics = self.get_comic_list()
        rcb_comics = rcb.get_comic_list()
        # for i, serie in enumerate(comics):
        #     print("[DEFAULT]Progress {} out of {}".format(i, len(comics)), end='\r')
        #     serie_key = serie['href'].rpartition('/')[-1]
        #     if not db.get(serie_key, False):
        #         db[serie_key] = {"name": serie.text.replace('/', '-'), "url": serie["href"]}
        #         soup = self.get_html(serie["href"])
        #         db[serie_key].update(self.get_metadata(soup))
        for i, serie in enumerate(rcb_comics):
            print("[RCB_DRIVER]Progress {} out of {}".format(i, len(rcb_comics)), end='\r')
            serie_key = serie['href'].rpartition('/')[-1]
            if db.get(serie_key) and db[serie_key].get('rcb_url'):
                continue
            elif db.get(serie_key):
                db[serie_key]['rcb_url'] = serie['href']
            else:
                db[serie_key] = {"name": serie.text.replace('/', '-'), "rcb_url": serie["href"], 'rcb_only': True}
            soup = self.get_html(urljoin(rcb.base_url, serie["href"]))
            try:
                db[serie_key].update(rcb.get_metadata(soup))
            except IndexError:
                print("Metadata download for series {} failed".format(serie_key))
        return db

    def generate(self, db):
        database = self.create_database(db)
        print("Generation complete. Saving.")
        json.dump(database, open(self.db_path, 'w'))

    def search(self, db, query, field='name'):
        regex = re.compile(query, re.IGNORECASE)
        if field in ['name', 'publisher']:
            return {k: v for k, v in db.items() if regex.search(v.get(field, ''))}
        else:
            return {k: v for k, v in db.items() if [x for x in v.get(field, '') if regex.search(x)]}
