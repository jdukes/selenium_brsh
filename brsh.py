#!/usr/bin/env python2
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

from binascii import b2a_hex
from os import urandom

from BeautifulSoup import BeautifulSoup
from urllib2 import urlparse
from urllib2 import quote as urlquote
from urllib2 import unquote as urlunquote
from codecs import register as _register
from codecs import CodecInfo as _CodecInfo

from selenium import webdriver, selenium
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from IPython import __version__ as IPy_version
if IPy_version == '0.10.2':
    from IPython.Shell import IPShellEmbed
else:
    # fucking IPython changes the way they embed every other
    # relesae...  need to figure out which one this works for.
    from IPython.frontend.terminal.embed import InteractiveShellEmbed
    #from IPython import embed
    from IPython.config.loader import Config

#think about adding htmlunit for some tests

config = ConfigParser.ConfigParser()
cfg_search_paths = [os.path.expanduser('~/.brsh.cfg'), './brsh.cfg']
for filename in cfg_search_paths:
    r = config.read(filename)
    if r:
        break

assert r, "config not found in locations {0}".format(cfg_search_paths)
del(r)

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

#these should all be moved to a seperate helper library
def check_robots(url): #hum.....
    if not url[-1] == '/':
        url += '/' 
    browser.get(url + 'robots.txt')
    s = soup_page() 
    paths = [ i.split()[1] for i in s.pre.contents[0].split('\n') if i ][1:]
    return ( browser.get('%s%s' % path) for path in paths )

#sitemap

def get_links():
    return ({'name':a.text.encode('latin1'), 'uri':a.get_attribute('href')}
            for a in browser.find_elements_by_css_selector('a'))

#getOwnPropertyNames()
def get_methods(obj):
    r = browser.execute_script('''
    function get_methods(obj){
        var methods = [];
        for (var m in obj) {
            if (typeof obj[m] == "function") {
                methods.push(m);
            }
        }
        return methods.join(",");
    }
    return get_methods(" + obj + ");
    ''')
    return r

#def wait
#http://selenium-python.readthedocs.org/en/latest/waits.html

def wait_for_selector(selector, time=10):
    element = WebDriverWait(browser, time).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    return element

def rand_str(length):
    return b2a_hex(urandom(int(length/2)+1)).decode('ascii')[:length]

def print_links():
    for link in get_links():
        print link["name"], link["uir"]

def print_link_titles():
    for link in get_links():
        print link["name"]

def print_link_locn():
    for link in get_links():
        print link["uri"]

open_link = lambda name: browser.find_element_by_link_text(name).click()

def soup_page(data=None):
    data = data or browser.page_source
    return BeautifulSoup(data)

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

CODECS_IN_FILE={"url" : _CodecInfo(name = 'url',
                                  encode=url_encode,
                                  decode=url_decode),
                }
def getregentry(name):
    return CODECS_IN_FILE[name]
_register(getregentry)

def reload_config():
    execfile(preload)

def accept():
    browser.switch_to.alert.accept()

try:
    if preload:
        if os.path.exists(preload):
            st = os.stat(preload)
            if st.st_uid == os.getuid() \
                   and (not ((stat.S_IMODE(st.st_mode) | 0755) ^ 0755)):
                execfile(preload)
            else:
                stupid = raw_input("Are you stupid enough to execute code "
                                   "someone else may be able to write (yes/NO)?")
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


if IPy_version == '0.10.2':
    if not "__IP" in dir():
        ipshell = IPShellEmbed(['-pi1','selenium \\# >>> '])
    else:
        ipshell = IPShellEmbed()
    ipshell("use the browser object to interface with the browser")
else:
    cfg = Config()
    prompt_config = cfg.PromptManager
    if not "__IP" in dir():
        prompt_config.in_template = 'In <[selenium] \\#>: '
        prompt_config.in2_template = '   .\\D.: '
        prompt_config.out_template = 'Out <[selenium] \\#>: '
    ipshell = InteractiveShellEmbed(config=cfg,
                                    banner1 = ('Dropping in to selenium shell. '
                                               'To interact with the browser use '
                                               'the "browser" object. '),
                                    exit_msg = 'closing browser.')
    ipshell()

try:
    browser.close()
except:
    pass

