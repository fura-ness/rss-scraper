import os, random, hashlib, datetime, time, string, re

import feedparser

import praw
from prawutil import r

LOCKFILE = '/tmp/rss-load.lock'

if __name__=='__main__':

    if os.path.exists(LOCKFILE):
        print 'lock file %s exists, exiting' % LOCKFILE
        exit(0)


    ignored_tokens = [t.strip() for t in open('ignored-tokens.txt').readlines() if t.strip()]
    ignored_tokens += [string.capwords(t) for t in ignored_tokens]
    ignored_tokens = list(set(ignored_tokens))

    ignored_urls = [t.strip() for t in open('ignored-urls.txt').readlines() if t.strip()]

    collapsed_tokens = [t.strip() for t in open('collapsed-tokens.txt').readlines() if t.strip()]
    collapsed_tokens += [string.capwords(t) for t in collapsed_tokens]
    collapsed_tokens = list(set(collapsed_tokens))
    collapsed_tokens_seen = []

    already_posted = [h.strip() for h in open('posted.txt').readlines() if h.strip()]

    articles = set()

    for f in os.listdir('./feeds'):
        feed = feedparser.parse('./feeds/%s' % f)
        for entry in feed.entries:

            try:
                t = entry.title
            except AttributeError:
                continue

            ignore = any(t in entry.title for t in ignored_tokens)
            if ignore:
                continue

            try:
                link = entry.link
            except AttributeError:
                continue

            try:
                fb_link = entry.feedburner_origlink
                link = fb_link
            except AttributeError:
                pass

            ignore = any(t in link.lower() for t in ignored_urls)
            if ignore:
                continue

            try:
                article_hash = hashlib.md5(link).hexdigest()
            except:
                continue

            if article_hash in already_posted:
                continue

            already_posted.append(article_hash)

            title = translate(entry.title)
            title = title.encode('utf-8')
            if not title:
                continue

            skip = False
            for ct in collapsed_tokens:
                if ct in title:
                    if ct in collapsed_tokens_seen:
                        skip = True
                    else:
                            collapsed_tokens_seen.append(ct)

                    break

            if skip:
                continue

            articles.add((link, title))


    print now(), '+++ FEEDS LOADED (%03d)' % len(articles)

    articles = list(articles)
    random.shuffle(articles)

    f = open('articles-posted.txt', 'a')

    for n, (link, title) in enumerate(articles):
        try:
            print now(), '%03d' % (n+1), '%03d' % len(articles), title
            article_hash = hashlib.md5(link).hexdigest()
            if len(title) > 300:
                print 'title too long'
                f.write('%s\n' % article_hash)
                continue
            r.submit('news_etc', title, url=link)
            f.write('%s\n' % article_hash)
            time.sleep(4)
        except praw.errors.AlreadySubmitted:
            print now(), '+++ EXCEPTION AlreadySubmitted: %s' % link
            f.write('%s\n' % article_hash)
            continue
        except praw.errors.ClientException as e:
            print now(), '+++ EXCEPTION ClientException: %s, %s' % (e, link)
            continue
        except praw.errors.APIException as e:
            print now(), '+++ EXCEPTION APIException: %s, %s, %s' % (e, link, 'DOMAIN_BANNED' in str(e))
            if 'DOMAIN_BANNED' in str(e):
                f.write('%s\n' % article_hash)
            continue
        except praw.errors.HTTPException as e:
            print now(), '+++ EXCEPTION HTTPException: %s, %s' % (e, link)
            continue
        except KeyError as e:
            print now(), '+++ EXCEPTION KeyError: %s, %s' % (e, link)
            f.write('%s\n' % article_hash)
            continue
        except Exception as e:
            print now(), '+++ EXCEPTION Unknown: %s, %s, %s' % (e.__class__.__name__, e, link)
            continue


    os.unlink(LOCKFILE)
