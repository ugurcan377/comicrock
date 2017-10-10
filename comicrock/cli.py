#! /usr/bin/python3
import click
import requests

from comicrock.castle_driver import CastleDriver
from comicrock.comicrock import ComicRock
from comicrock.database import ComicDatabase
from comicrock.rco_driver import RCODriver
from comicrock.rcb_driver import RCBDriver

DRIVERS = {'rco': RCODriver,
           'rcb': RCBDriver,
           'castle': CastleDriver}


@click.group()
def cli():
    """The Comic Downloading Software"""


@cli.command()
@click.argument('query')
@click.option('--field', type=click.Choice(['author', 'genre']))
@click.option('--verbose', is_flag=True)
def search(query, field, verbose):
    """Search for a comic series, author or genre"""
    if not field:
        field = 'name'
    database = ComicDatabase()
    try:
        db = database.load()
    except FileNotFoundError:
        click.echo('Database Not Found! You can generate it with "comicrock generatedb"')
        return -1
    results = database.search(db, query, field)
    if verbose:
        click.echo(results)
    else:
        for k, v in results.items():
            if v.get('rcb_only', False):
                click.echo('[RCB]{} ---> {} ({})'.format(k, v['name'], ', '.join(v['author'])))
            else:
                click.echo('{} ---> {} ({})'.format(k, v['name'], ', '.join(v['author'])))


@cli.command()
@click.option('--start', default=0, type=int, help='Download starting from this chapter')
@click.option('--end', default=-1, type=int, help='Download to this chapter')
@click.option('--driver', type=click.Choice(['rco', 'rcb', 'castle']))
@click.option('--dry-run', is_flag=True, help='Start a test run without downloading')
@click.option('--no-fav', is_flag=True, help='Do not add this comic to favorites')
@click.argument('key')
def download(start, end, driver, dry_run, no_fav, key):
    """Download the comic book series with given book key
        You can learn a book key with search command
    """
    driver_obj = DRIVERS.get(driver, RCBDriver)
    comic = driver_obj()
    book_name = comic.get_book_name(key)
    click.echo("Downloading {}, this may take a while for long series".format(book_name))
    try:
        result = comic.download_series(key, start=start, end=end, dry_run=dry_run, no_fav=no_fav)
        click.echo('Download finished, enjoy your books at {}'.format(result))
    except requests.HTTPError as exc:
        click.echo('Download Failed: {}'.format(exc))


@cli.command()
@click.option('--driver', type=click.Choice(['rco', 'rcb', 'castle']))
@click.argument('keys', nargs=-1)
def batch(driver, keys):
    """Download multiple series at once"""
    driver_obj = DRIVERS.get(driver, RCBDriver)
    comic = driver_obj()
    for key in keys:
        book_name = comic.get_book_name(key)
        click.echo("Downloading {}, this may take a while for long series".format(book_name))
        try:
            result = comic.download_series(key)
            click.echo('Download finished, enjoy your books at {}'.format(result))
        except requests.HTTPError as exc:
            click.echo('Download Failed: {}'.format(exc))


@cli.command()
def generatedb():
    """Generate a comic database for better searching"""
    database = ComicDatabase()
    try:
        db = database.load()
        click.echo("Existing Database Found! Updating")
    except FileNotFoundError:
        click.echo('Database Not Found! Creating"')
        db = {}
    database.generate(db)

@cli.command()
def update():
    """Update your favorite comics"""
    driver_obj = DRIVERS.get('', RCBDriver)
    comic = driver_obj()
    keys = comic.get_fav_list()
    for key in keys:
        book_name = comic.get_book_name(key)
        click.echo("Downloading {}, this may take a while for long series".format(book_name))
        try:
            result = comic.download_series(key)
            click.echo('Download finished, enjoy your books at {}'.format(result))
        except requests.HTTPError as exc:
            click.echo('Download Failed: {}'.format(exc))

def main():
    cli()
