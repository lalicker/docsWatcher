#!/usr/bin/env python3

import urllib.request
import xml.etree.ElementTree as ET
import datetime
import re
from storageHandler import StorageHandler
import argparse
#import smtplib
#import email.message
from bs4 import BeautifulSoup

import logging
logging.basicConfig(level=logging.DEBUG, filename='./pylog.log')
#logging.basicConfig(level=logging.DEBUG, filename='./pydebug.log')

db = 'docsWatcher'

#TODO: Provide Credentials
emailHost = ''
emailPort = 0
emailUser = ''
emailPass = ''

###This returns an ElementTree DOM object based on a URL string ###
def getDOMTree(address):
    try:
        sitemap = urllib.request.urlopen(address)
    except:
        raise
    tree = ET.parse(sitemap)
    return tree

def initArgParse():
    parser = argparse.ArgumentParser(description='Monitor updates to page from sitemap provided')
    parser.add_argument('--sitemap','-s', required=True) 
    parser.add_argument('--pattern','-p', required=True)
    parser.add_argument('--recurse','-r', action='store_true',required=False)
    parser.add_argument('--exact','-e', action='store_true',required=False)
    return parser.parse_args()

def isSitemapIndex(tree):
    return tree.getroot().tag == '{'+ns['page']+'}sitemapindex'

def getSitemapsFromSitemapIndex(tree):
    subtrees = set()
    for sitemapURL in tree.findall('page:sitemap/page:loc',ns):
        subtrees.add(getDOMTree(sitemapURL.text))
    return subtrees

def urlElementToDict(e,ns):
    ret = dict()
    els = {'loc': 'page:loc','lastmod': 'page:lastmod','changefreq': 'page:changefreq','imageLoc': 'image:image/image:loc','imageTitle': 'image:image/image:title'}.items()
    for k,v in els:
        try:
            ret[k] = e.find(v,ns).text
        except:
            continue
    return ret

def matchPageUrl(url,re, mt):
    try:
        if mt:
            return re.fullmatch(url['loc'])
        else:
            return re.search(url['loc'])
    except:
        return None

def sendNotification(new):
    TODO:EDIT
    try:
        server = smtplib.SMTP(emailHost, emailPort)
        server.ehlo()
        server.starttls()
        server.login(emailUser,emailPass)
        # ...send emails

        message = email.message.EmailMessage()
        message['Subject'] = 'New Products Detected!'
        message['To'] = emailUser
        message['From'] = emailUser
        message.set_default_type('text/html')
        htmlBody = ''
        body = 'Updates to product pages that you are watching have been identified!\n'
        for x in new:
            body = body + x[0] + ' updated at ' + x[1] + '\n'
            htmlBody = htmlBody + '<tr><td><a href='+x[0]+'>'+x[0]+'</a></td><td>'+x[1]+'</td></tr>'
        htmlBody = """<html><head><style>table, th, td{{border: 1px solid black;font-family: sans-serif;font-weight: normal;}}th{{font-weight:bold;}}</style></head><body><p>Updates to product pages that you are watching have been identified!</p><table><tr><th>Product Link</th><th>Updated Time</th></tr>"""+htmlBody+"""</table></body></html>"""
        message.set_content(body)
        message.add_alternative(htmlBody)
        server.send_message(message)
        server.close()

    except:
        logging.error('Something went wrong...')

if __name__ == '__main__':
    logging.info('Process Started')
    ns = {'page' : 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    args = initArgParse()
    sh = StorageHandler(db+'.db')
    tf = '%Y-%m-%dT%H:%M:%S'

    
    tree = getDOMTree(args.sitemap)
    if(isSitemapIndex(tree)):
        sitemaps = getSitemapsFromSitemapIndex(tree)
    else:
        sitemaps = set()
        sitemaps.add(tree)
    urls = list()
    logging.debug(sitemaps)
    for sitemap in sitemaps:
        for url in sitemap.findall('page:url',ns):
            urls.append(urlElementToDict(url,ns))
    logging.debug(urls)    
    prog = re.compile(args.pattern)
    filteredUrls = list(filter(lambda x: matchPageUrl(x,prog,args.exact), urls))
    logging.debug(filteredUrls)

    new = list()
    for url in filteredUrls:
        res = dict(sh.getLoc(url['loc']))
        url['lastmod'] = url['lastmod'][0:-5]
        logging.debug('location %s\nlastmod %s',url['loc'],url['lastmod'])
        if url['loc'] not in res.keys() or datetime.datetime.strptime(res[url['loc']],tf) < datetime.datetime.strptime(url['lastmod'],tf):
            new.append((url['loc'],url['lastmod']))
    print("product, version, date")
    for item in new:
        logging.info(item)
        sh.upsertLoc(item[0],item[1])
        soup = BeautifulSoup(urllib.request.urlopen(item[0]),"html.parser")
        title = soup.find("h1","page").text
        for tag in soup.find_all("div","sect1"):
            if tag.h2 is not None:
                version = tag.h2.text
            else:
                version = ""
            if tag.p is not None and tag.p.strong is not None:
                date = tag.p.strong.text
            else:
                date = version
            print(title+","+version+","+date)
#TODO: look at DB and send email notification, write file? other stuff. 
