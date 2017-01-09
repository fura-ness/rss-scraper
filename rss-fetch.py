import random, os, datetime, time

import requests

from strutil import slugify

LOCKFILE = '/tmp/rss-fetch.lock'


if __name__=='__main__':

    if os.path.exists(LOCKFILE):
        print 'lock file %s exists, exiting' % LOCKFILE
        exit(0)

    open(LOCKFILE, 'w')

    urls = [u.strip() for u in open('feed-urls.txt').read().split() if u.strip()]

    random.shuffle(urls)

    for url in urls:

        if url.startswith('#'):
            continue

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-00-00')
        slug = slugify(url)
        slug = slug.replace('http-', '')
        slug = slug.replace('https-', '')
        slug = slug.replace('www-', '')
        filename = 'feeds/%s-%s' % (slug, timestamp)

        if os.path.exists(filename):
            continue

        try:
            r = requests.get(url, headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'})
        except requests.exceptions.ConnectionError:
            print 'ConnectionError', url
            continue

        print r.status_code, slugify(url)

        if r.status_code != 200:
            print r.text.encode('utf-8').replace('\n', ' ')[0:120]
            continue

        with open(filename, 'w') as f:
            f.write(r.text.encode('utf-8'))

        time.sleep(0.25)


    os.unlink(LOCKFILE)
