# comicrock
Comic downloader inspired by MangaRock

## Usage
### Searching
You need to know a book key to download a certain book. You can learn a book key with following command

```
comicrock.py search TEXT
```
You can also use '--field' option to search for either authors or genres
### Downloading
You can download a series with following command

```
comicrock.py download BOOK_KEY
```

If you want to download only certain chapters you can specify them with '--start INT' and '--end INT' options.
### Batch Downloading
You can download multiple series at once with following command

```
comicrock.py batch BOOK_KEY1 BOOK_KEY2 ...
```