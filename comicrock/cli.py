#! /usr/bin/python3
from urllib.parse import urljoin

import click
import requests

from comicrock.comicrock import ComicRock


@click.group()
def cli():
    """The Comic Downloading Software"""


@cli.command()
@click.argument('text')
def search(text):
    """Search for a comic series"""
    comic = ComicRock()
    results = comic.search_comics(text)
    for series in results:
        click.echo('{name} ---> {url}'.format(name=series[0], url=series[1]))


@cli.command()
@click.option('--start', default=0, type=int, help='Download starting from this chapter')
@click.option('--end', default=-1, type=int, help='Download to this chapter')
@click.option('--dry-run', is_flag=True, help='Start a test run without downloading')
@click.argument('key')
def download(start, end, dry_run, key):
    """Download the comic book series with given book key
        You can learn a book key with search command
    """
    comic = ComicRock()
    url = urljoin(comic.book_url, key)
    book_name = comic.get_book_name(url)
    click.echo("Downloading {}, this may take a while for long series".format(book_name))
    try:
        result = comic.download_series(url, start=start, end=end, dry_run=dry_run)
        click.echo('Download finished, enjoy your books at {}'.format(result))
    except requests.HTTPError as exc:
        click.echo('Download Failed: {}'.format(exc))


@cli.command()
@click.argument('keys', nargs=-1)
def batch(keys):
    """Download multiple series at once"""
    comic = ComicRock()
    for key in keys:
        url = urljoin(comic.book_url, key)
        book_name = comic.get_book_name(url)
        click.echo("Downloading {}, this may take a while for long series".format(book_name))
        try:
            result = comic.download_series(url)
            click.echo('Download finished, enjoy your books at {}'.format(result))
        except requests.HTTPError as exc:
            click.echo('Download Failed: {}'.format(exc))


def main():
    cli()
