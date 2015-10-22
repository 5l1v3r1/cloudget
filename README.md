# cloudget 0.72
#### by vvn [ lost @ nobody . ninja ]

 python script to bypass cloudflare from command line, with extensive scraping, link harvesting, and recursive directory downloading. built upon cfscrape module.

**REQUIRES CFSCRAPE AND BEAUTIFULSOUP MODULES TO RUN**

get cfscrape here:

    https://github.com/Anorov/cloudflare-scrape

get BeautifulSoup here:

    http://www.crummy.com/software/BeautifulSoup/

or install using pip:

    pip install cfscrape
    pip install BeautifulSoup

**USAGE:**

    python cloudget.py [-c] [-o] [-l] [-d] [-p <[proxy server]>] -u <[url behind cloudflare proxy]>

**MUST USE COMPLETE URL STARTING WITH http://**

#### OPTIONS:

**-u | --url <[url]>:**
REQUIRED - url behind cloudflare proxy to access

**-o | --out:**
OPTIONAL - download to file

**-c | --curl:**
OPTIONAL - pass URL through cURL

**-l | --links:**
OPTIONAL - find all links in response at URL

**-p | --proxy <[proxy server]>:**
OPTIONAL - connect through HTTP/HTTPS proxy server at http(s)://[host]:[port]
(example: --proxy http://localhost:8080)

**-d | --debug:**
OPTIONAL - turn verbose errors on for debugging, show detailed script info

**-h | --help:**
HELP - show options and exit

**--version:**
OPTIONAL - show version information

**KNOWN BUGS:**

    cURL option (-c) most likely doesn't work with cloudflare URLs.
    for cloudflare URL support don't use -c.
