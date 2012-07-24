#!/usr/bin/env python
"""Browser Shell
This gives us an interactive shell to selenium
"""
#this needs to be cleaned up quite a bit.

import signal
import os
import re
import stat
from time import sleep
import ConfigParser

from BeautifulSoup import BeautifulSoup
from urllib2 import urlparse
from urllib2 import quote as urlquote
from urllib2 import unquote as urlunquote
from codecs import register, CodecInfo


from fuzzywuzzy import fuzz as fw #maybe this belongs elsewhere...

from selenium import webdriver, selenium
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from IPython import embed


#think about adding htmlunit for some tests

config = ConfigParser.ConfigParser()
cfg_search_paths = [os.path.expanduser('~/.brsh.cfg'), './brsh.cfg']
for f in cfg_search_paths:
    r = config.read(f)
    if r:
        break

assert r, "config not found in locations {0}".format(cfg_search_paths)

assert config.has_section('base'), ("No [base] found in conifguration. "
                                    "Verify your config based on the "
                                    "example provided.")

try:
    profile =  webdriver.FirefoxProfile(config.get('base','profile'))
except ConfigParser.NoOptionError:
    print ("Verify that your profile is set. "
           "Configuration can be based on the example provided.")
    raise

preload = None
try:
    preload =  config.get('base','preload')
except ConfigParser.NoOptionError:
    print "No preload found."

location = config.get('base','location') if config.has_option('base', 'location') else None

def check_robots(url): #hum.....
    if not url[-1] == '/':
        url += '/' 
    browser.get(url + 'robots.txt')
    s = soup_page()
    paths = [ i.split()[1] for i in s.pre.contents[0].split('\n') if i ][1:]
    return ( browser.get('%s%s' % path) for path in paths )

#sitemap

def get_links():
    return ((a.text, a.get_attribute('href'))
            for a in browser.find_elements_by_css_selector('a'))

# def get_all_urls():
#     re.search(browser re.DOTALL

def print_links():
    for a, href in get_links():
        print a, href

def print_link_titles():
    for a, href in get_links():
        print a

def print_link_locn():
    for a, href in get_links():
        print href

open_link = lambda name: browser.find_element_by_link_text(name).click()

def soup_page():
    return BeautifulSoup(browser.page_source)

#add caps setting to config
def init_browser(location="local"): 
    if not location or location == "local": 
        browser = webdriver.Firefox(firefox_profile=profile)
        def timeout_handler(signum, frame): #selenium hangs on first
                                            #get when local, so here's
                                            #a hack
            raise Exception()
        signal.signal(signal.SIGALRM, timeout_handler)
        try: 
            signal.alarm(1)
            browser.get('about:about')
        except Exception:
            pass
    else:
        pass
        #caps = webdriver.DesiredCapabilities.INTERNETEXPLORER
        caps = webdriver.DesiredCapabilities.FIREFOX
        browser = webdriver.Remote(
            command_executor='http://' + location + ':4444/wd/hub',
            desired_capabilities=caps)
    browser.get('about:about')
    return browser


location = location or raw_input('location (return for local)> ') #need to add port info
browser = init_browser(location)

def url_decode(input, errors='strict'):
    output = urlunquote(input)
    return (output, len(input))


def url_encode(input, errors='strict'):
    output = urlquote(input)
    return (output, len(input))

CODECS_IN_FILE={"url" : CodecInfo(name = 'url',
                                  encode=url_encode,
                                  decode=url_decode),
                }
def getregentry(name):
    return CODECS_IN_FILE[name]
register(getregentry)


try:
    if preload:
        if os.path.exists(preload):
            st = os.stat(preload)
            if st.st_uid == os.getuid() and ( not ((stat.S_IMODE(st.st_mode) | 0755) ^ 0755)):
                execfile(preload)
            else:
                stupid = raw_input("Are you stupid enough to execute code someone else may be able to"\
                                   " write (yes/NO)?")
                if stupid.upper() == "YES":
                    print "Ok... setting up backdoor now..."
                    execfile(preload)
                else:
                    print "Oh, you're not stupid. Let's not load that then."
        else:
            print "preload file not found, ignoring config option."
except Exception:
    print ("Preload failed. Please verify the file exists, is valid, and has the"
           " correct permissions")
    raise


embed()
# ipshell = IPShellEmbed(['-pi1','selenium \\# >>> '])
# ipshell("use the browser object to interface with the browser")

try:
    browser.close()
except:
    pass
