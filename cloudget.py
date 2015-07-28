#!/usr/bin/env python
# cloudget v0.69
# release date: July 27, 2015
# author: vvn < lost @ nobody . ninja >

import sys, argparse, subprocess, os, re, random, requests, string, time, traceback
from datetime import date, datetime
from urlparse import urlparse
from subprocess import PIPE, check_output, Popen

try:
   import cfscrape
except:
   pass
   try:
      os.system('pip install cfscrape')
      import cfscrape
   except:
      print('unable to install the cfscrape module via pip. this script requires cfscrape to run. get it here: https://github.com/Anorov/cloudflare-scrape')
      sys.exit(1)

intro = '''
=========================================
------------ CLOUDGET v0.69 -------------
=========================================
------------- author : vvn --------------
----- lost [at] nobody [dot] ninja ------
=========================================
------ support my work: buy my EP! ------
---------- http://dreamcorp.us ----------
----- facebook.com/dreamcorporation -----
-------- thanks for the support! --------
=========================================
'''

print(intro)

try:
   from BeautifulSoup import BeautifulSoup
except:
   pass
   try:
      os.system('pip install BeautifulSoup')
      from BeautifulSoup import BeautifulSoup
   except:
      print('BeautifulSoup module is required to run the script.')
      sys.exit(1)

global cfurl
global usecurl
global writeout
global depth
global useproxy
global debug
global depth
usecurl = 0
writeout = 0
depth = 0
useproxy = 0
debug = 0
depth = 0
links = 0

parser = argparse.ArgumentParser(description="a script to automatically bypass anti-robot measures and download links from servers behind a cloudflare proxy")
 
parser.add_argument('-u', '--url', action='store', help='[**REQUIRED**] full cloudflare URL to retrieve, beginning with http(s)://', required=True)
parser.add_argument('-o', '--out', help='save returned content to \'download\' subdirectory', action='store_true', required=False)
parser.add_argument('-l', '--links', help='scrape content returned from server for links', action='store_true', required=False)
parser.add_argument('-c', '--curl', nargs='?', default='empty', const='curl', dest='curl', metavar='CURL_OPTS', help='use cURL. use %(metavar)s to pass optional cURL parameters. (for more info try \'curl --manual\')', required=False)
parser.add_argument('-p', '--proxy', action='store', metavar='PROXY_SERVER:PORT', help='use a proxy to connect to remote server at [protocol]://[host]:[port] (example: -p http://localhost:8080) **only use HTTP or HTTPS protocols!', required=False)
parser.add_argument('-d', '--debug', help='show detailed stack trace on exceptions', action='store_true', required=False)
parser.add_argument('--version', action='version', version='%(prog)s v0.69 by vvn <lost@nobody.ninja>, released july 27, 2015.')

args = parser.parse_args()
if args.out:
   writeout = 1
if args.links:
   links = 1
if args.debug:
   debug = 1
if args.proxy:
   useproxy = 1
   proxy = args.proxy
   if not re.search(r'^(http[s]?|socks(4[a]?|5)?)', proxy):
      print("\ninvalid argument supplied for proxy server. must specify as [protocol]://[server]:[port], where [protocol] is either http or https. (for example, http://127.0.0.1:8080) \n")
      sys.exit(1)
   x = urlparse(args.proxy)
   proxyhost = str(x.netloc)
   proxytype = str(x.scheme)
if args.curl in 'empty':
   usecurl = 0
elif args.curl is 'curl':
   usecurl = 1
else:
   usecurl = 1
   global curlopts
   curlopts = args.curl
   
cfurl = args.url
   
print("\nURL TO FETCH: %s \n" % cfurl)

if 'proxy' in locals():
   if 'https' in proxytype:
      proxystring = {'https': '%s' % proxyhost}
   else:
      proxystring = {'http': '%s' % proxyhost}
   print("using %s proxy server: %s \n" % (str(proxytype.upper()), str(proxyhost)))
else:
   proxystring = None
   print("not using proxy server \n")
   
checklinks = ''

if links == 1:
   checklinks = 'yes'
else:
   checklinks = 'no'
   
if not re.match(r'^http$', cfurl[:4]):
   print("incomplete URL provided: %s \r\ntrying with http:// prepended..")
   cfurl = "http://" + cfurl

depth = 0

def getCF(cfurl, links):

   checkcurl = ''

   if usecurl == 1:
      checkcurl = 'yes'
   else:
      checkcurl = 'no'
   print("using curl: %s \n" % checkcurl)
   print("harvesting links: %s \n" % checklinks)
   
   p = urlparse(cfurl)
   part = p.path.split('/')[-1]
   path = p.path.strip(part)
   if '/' not in path[:1]:
      path = '/' + path
   toplevel = p.scheme + '://' + p.netloc
   parent = toplevel + path
   childdir = path.strip('/')
   domaindir = os.path.join('download', p.netloc)
   parentdir = os.path.join(domaindir, childdir)

   if writeout == 1:
      global outfile
      p = urlparse(cfurl)
      if not os.path.exists('download'):
         os.makedirs('download')
      domaindir = os.path.join('download', p.netloc)
      outfile = cfurl.split('?')[0]
      outfile = outfile.split('/')[-1]
      filename = cfurl.lstrip('https:').strip('/')
      filename = filename.rstrip(outfile)
      dirs = filename.split('/')
      a = 'download'
      for dir in dirs:
         a = os.path.join(a, dir)
         if not os.path.exists(a):
            os.makedirs(a)
      if len(outfile) < 1 or outfile in p.netloc:
         outfile = 'index.html'
         outdir = filename
      else:  
         part = outfile
         outdir = filename.rstrip(part)
      fulloutdir = os.path.join('download', outdir)
      outfile = outfile.strip('/')
      if not os.path.exists(fulloutdir):
         os.makedirs(fulloutdir)
      print("output file: %s \n" % outfile)
      global savefile
      savefile = os.path.join(fulloutdir, outfile)
      cwd = os.getcwd()
      fullsavefile = os.path.join(cwd, savefile)
      print("full path to output file: %s \n" % fullsavefile)

   print("sending request..\n")
   scraper = cfscrape.create_scraper()
   ualist = [
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36', 
'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko', 
'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko', 
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)', 
'Mozilla/5.0 (compatible; MSIE 9.0; AOL 9.7; AOLBuild 4343.19; Windows NT 6.1; WOW64; Trident/5.0; FunWebProducts)', 
'Mozilla/5.0 (Windows NT 6.3; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36', 
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36', 
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36', 
'Mozilla/5.0 (Windows NT 6.1 WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36', 
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A', 
'Mozilla/5.0 (X11; SunOS i86pc; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; FreeBSD amd64; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; FreeBSD i386; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; Linux i586; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; OpenBSD amd64; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; OpenBSD alpha; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; OpenBSD sparc64; rv:38.0) Gecko/20100101 Firefox/38.0', 
'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20121202 Firefox/17.0 Iceweasel/17.0.1', 
'Opera/9.80 (X11; Linux i686; Ubuntu/14.10) Presto/2.12.388 Version/12.16', 
'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14 Mozilla/5.0 (Windows NT 6.0; rv:2.0) Gecko/20100101 Firefox/4.0 Opera 12.14', 
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0) Opera 12.14'
] 
   n = random.randint(0,len(ualist)) - 1
   ua = ualist[n].strip()

   if usecurl == 1:
      r = scraper.get(cfurl, stream=True, verify=False, allow_redirects=True, proxies=proxystring)
      print("status: ")
      print(r.status_code)
      print("\ngetting cookies for %s.. \n" % cfurl)
      cookie_arg = cfscrape.get_cookie_string(cfurl)
      if cookie_arg:
         req = "GET / HTTP/1.1\r\n"
         req += "Cookie: %s\r\nUser-Agent: %s\r\n" % (cookie_arg, ua)
         houtput = check_output(["curl", "--cookie", cookie_arg, "-A", ua, "-I", cfurl])
         curlstring = '--cookie \'' + cookie_arg + '\' -A \'' + ua + '\' -L -k '
         if 'curlopts' in locals():
            curlstring = '--cookie \'' + cookie_arg + '\' ' + curlopts + ' -A \'' + ua + '\' -k '
      else:
         req = "GET / HTTP/1.1\r\n"
         req += "User-Agent: %s\r\n" % ua
         houtput = check_output(["curl", "-A", ua, "-I", cfurl])
         curlstring = '-A \'' + ua + '\' -L -k '
         if 'curlopts' in locals():
            curlstring = '-# ' + curlopts + ' -A \'' + ua + '\' -k '
      if proxy:
         curlstring += '-x %s ' % proxy
      print(reqd)
      print("\nHEADERS: \n%s \n" % str(houtput))
      msg = "\nfetching %s using cURL.. \n" % cfurl
      if writeout == 1:
         if os.path.exists(savefile):
            resumesize = os.path.getsize(savefile)
            print("\n%s already exists! \n" % outfile)
            print("\nlocal file size: %s bytes \n" % str(resumesize))
            checkresume = raw_input('choose an option [1-3]: 1) resume download, 2) start new download, 3) skip. --> ')
            while not re.match(r'^[1-3]$', checkresume):
               checkresume = raw_input('invalid input. enter 1 to resume, 2 to start new, or 3 to skip --> ')
            if checkresume == '1':
               curlstring = curlstring + '-C - -o \'' + savefile + '\' '
               msg = "\ntrying to resume download using cURL to %s.. \n" % savefile
            elif checkresume == '2':
               curlstring = curlstring + '-O '
               msg = "\nstarting new download to %s.. \n" % savefile
            else:
               msg = "\nskipping download for %s \n" % outfile
         else:
            curlstring = curlstring + '-O '
            msg = "\ntrying to download using cURL to %s.. \n" % savefile
         #command_text = 'cd download && { curl ' + curlstring + cfurl + ' ; cd -; }'
      else:
         msg = "\nfetching %s using cURL.. \n" % cfurl
      command_text = 'curl ' + curlstring + cfurl
      print(msg)
      print("\nsubmitting cURL command string: \n%s \n" % command_text)
      output = Popen(command_text, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
      result, errors = output.communicate()
      if result is not None:
         ht = BeautifulSoup(str(result))
         cpass = ht.find('input', {'name': 'pass'})
         if cpass:
            cloudpass = cpass.get('value')
            cloudsch = ht.find('input', {'name': 'jschl_vc'}).get('value')
            reurl = ht.find('form').get('action')
            if reurl:
               print("form action: %s \n" % reurl)
            if '/' in path[:1]:
               path = path[1:]
            parent = p.scheme + '://' + p.netloc + path
            submitstr = 'pass=' + cloudpass + '&jschl_vc=' + cloudsch + '&challenge-form=submit'
            #locstr = 'Location: http://' + p.netloc + path + '?' + submitstr
            #header = '-H \'' + locstr + '\' -L ' + cfurl
            go = parent + reurl
            cs = '-e ' + p.netloc + ' --data-urlencode \'' + submitstr + '\' ' + curlstring
            if writeout == 0:
               cs = cs + '-v '
            else:
               cs = '--ignore-content-length ' + curlstring
               #command = 'cd download && { curl ' + cs + cfurl + ' ; cd -; }'
         else:
            cs = curlstring + '-e ' + p.netloc + ' '
            if writeout == 0:
               cs += '-v '
               #command = 'cd download && { curl ' + cs + cfurl + ' ; cd -; }'
         if re.search(r'(\.htm[l]?|\.php|\.[aj]sp[x]?|\.cfm|\/)$',cfurl) or re.search(r'(\.htm[l]?|\.php|\.[aj]sp[x]?|\.cfm)$', outfile):
            print(ht.prettify())
      else:
         if errors:
            print("\nerror: %s\n" % str(errors))
         cs = curlstring + ' -i '
         if writeout == 0:
            cs += '-v --no-keepalive '
         else:
            cs = '--ignore-content-length ' + cs
            #command = 'cd download && { curl ' + cs + cfurl + ' ; cd -; }'
      command = 'curl ' + cs + cfurl
      print("submitting cURL request:\n%s \n" % command)
      output = Popen(command, shell=True, stdout=PIPE, stderr=PIPE, stdin=PIPE)
      response, errors = output.communicate()
      res = BeautifulSoup(str(response))
      res = res.prettify()
      if response:
         print("\nresponse: \n %s \n" % str(res))
      if errors:
         print("\nerrors: \n %s \n" % str(errors))

   elif usecurl == 0 and writeout == 1: # min values r, dlmsg, dld, df, checkresume
      getkb = lambda a: round(float(float(a)/1024),2)
      getmb = lambda b: round(float(float(b)/1048576),2)
      print("\ngetting %s... \n" % cfurl)
      if os.path.exists(savefile): # FOUND SAVED FILE
         resumesize = os.path.getsize(savefile)
         ksize = getkb(resumesize)
         msize = getmb(resumesize)
         sizeqt = 'kb'
         fsize = ksize
         if msize > 1:
            sizeqt = 'mb'
            fsize = msize
         existsize = str(fsize) + ' ' + sizeqt
         print("\n%s already exists! \n" % outfile)
         print("\nlocal file size: %s \n" % existsize)
         checkresume = raw_input('choose an option [1-3]: 1) resume download, 2) start over with fresh download, 3) skip. --> ')
         while not re.match(r'^[1-3]$', checkresume):
            checkresume = raw_input('invalid input. enter 1 to resume, 2 to start new, or 3 to skip --> ')
         if checkresume == '1': # RESUME DOWNLOAD AT LAST LOCAL BYTE
            dld = int(resumesize)
            resumeheader = {'Range': 'bytes=%s-' % str(dld)}
            dlmsg = "\nattempting to resume download for %s. this may take awhile depending on file size... \n" % outfile
            df = open(savefile, 'a+b')
         elif checkresume == '2': # DISREGARD SAVED FILE, START DOWNLOAD FROM TOP
            resumeheader = None
            dlmsg = "\nwriting content to \'download\' directory as file %s. this may take awhile depending on file size... \n" % outfile
            dld = 0
            df = open(savefile, 'wb+')
         else: # SKIPPING DOWNLOAD
            resumeheader = None
            df = open(savefile, 'r+')
            dlmsg = "\nskipping download for %s\n" % outfile
   
      else: # NEW DOWNLOAD REQUEST
         checkresume = '2'
         dld = 0
         df = open(savefile, 'wb+')
         resumeheader = None
         dlmsg = "\nwriting content to \'download\' directory as file %s. this may take awhile depending on file size... \n" % outfile
   
      print(dlmsg)
   
      if not checkresume == '3': # IF NOT SKIPPING
         r = scraper.get(cfurl, stream=True, headers=resumeheader, verify=False, allow_redirects=True, proxies=proxystring)
         filesize = r.headers.get('Content-Length')
         filetype = r.headers.get('Content-Type')
         start = time.clock()
         #today = datetime.now()
         #startdate = date.strftime(today,"%m-%d-%Y %H:%M:%S ")
         #print("start time: %s \n" % startdate)
         with df as dlfile:
            if filesize is not None and 'text' not in filetype:
               bytesize = int(filesize)
               kbsize = getkb(bytesize)
               mbsize = getmb(bytesize)
               qt = 'bytes'
               size = bytesize
               if kbsize > 10:
                  qt = 'kb'
                  size = kbsize
                  if mbsize > 1 :
                     qt = 'mb'
                     size = mbsize
               print('\nfile size: ' + str(size) + ' %s \n' % qt)
               for chunk in r.iter_content(chunk_size=2048):
                  if chunk:
                     dld += len(chunk)
                     dlfile.write(chunk)
                     done = int((50 * int(dld)) / int(filesize))
                     dldkb = getkb(dld)
                     dldmb = getmb(dld)
                     unit = 'bytes'
                     prog = str(round(dld,2))
                     if dldkb > 1:
                        unit = 'kb   '
                        prog = str(round(dldkb,2))
                        if dldmb > 1:
                           unit = 'mb   '
                           prog = str(round(dldmb,2))
                     sys.stdout.write("\rdownloaded: %s %s   [%s%s] %d kb/s" % (prog, unit, '#' * done, ' ' * (50 - done), 0.128 * (dldkb / (time.clock() - start))))
                     dlfile.flush()
                     os.fsync(dlfile.fileno())
                  else:
                     break
            elif filesize and 'text' in filetype:
               dlfile.write(r.content)
               dlfile.flush()
               os.fsync(dlfile.fileno())
            else:
               for chunk in r.iter_content(chunk_size=1024):
                  if chunk:
                     dld += len(chunk)
                     dlfile.write(chunk)
                     dlfile.flush()
                     os.fsync(dlfile.fileno())
                  else:
                     break
         print("\r\nfile %s saved! \n" % outfile)
         fin = time.clock() - start
         totalsecs = fin * 360
         elapsed = "%s seconds " % str(totalsecs)
         if totalsecs > 60:
            totalmins = float(totalsecs / 60)
            mins = int(totalmins)
            if mins == 1:
               unitmin = "minute"
            else:
               unitmin = "minutes"
            strmin = str(mins) + " " + str(unitmin)
            secs = round((totalsecs % 60), 3)
            elapsed = str(strmin) + " " + str(secs)
            if totalmins > 60:
               totalhours = float(totalmins / 60 )
               hours = int(totalmins / 60)
               if hours == 1:
                  unithr = "hour"
               else:
                  unithr = "hours"
               strhr = str(hours) + " " + str(unithr)
               mins = round((totalmins % 60),3)
               elapsed = "%s, %s mins, %s secs" % (strhr, mins, secs)
            else:
               hours = 0
         else:
            hours = 0
            mins = 0
            secs = round(totalsecs,3)
            elapsed = "%s seconds" % str(secs)
         #ended = datetime.now()
         #enddate = date.strftime(ended,"%m-%d-%Y %H:%M:%S ")
         #print("end time: %s \n" % enddate)
         print("\ndownload time elapsed: %s \n" % str(elapsed))
         time.sleep(4)
         print('\r\n--------------------------------------------------------\r\n')
               
      else:
         print("\nskipped download from %s.\r\nfile has not been modified.\n" % cfurl)
      
      r = scraper.get(cfurl, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
      if 'text' in r.headers.get('Content-Type'):
         html = BeautifulSoup(r.text)
         bs = html.prettify()
         print(bs)
         print('\r\n--------------------------------------------------------\r\n')
      else:
         found = -1
      
   def getlinks(cfurl):
      r = scraper.get(cfurl, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
      html = BeautifulSoup(r.text)
      bs = html.prettify()
      linkresult = html.findAll('a')
      if len(linkresult) > 0:
         foundlinks = len(linkresult)
         print('\nFOUND LINKS AT %s:\n' % cfurl)
         for link in linkresult:
            b = link.get('href')
            b = str(b)
            print(b)
         print('')
      else:
         print('\nNO LINKS FOUND.\n')
         foundlinks = 0
      return foundlinks
      
   def selectdir(usedirremote):
      r = scraper.get(usedirremote, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
      html = BeautifulSoup(r.text)
      findlinks = html.findAll('a')
      dirlist = []
      for link in findlinks:
         b = link.get('href')
         if not re.match(r'^((\.\.)?\/)$', str(b)):
            if re.search(r'^(.*)(\/)$', str(b)):
               dirlist.append(b)
      
      p = urlparse(usedirremote)
      part = p.path.split('/')[-1]
      path = p.path.rstrip(part)
      if '/' not in path[:1]:
         path = '/' + path
      toplevel = p.scheme + '://' + p.netloc
      parent = toplevel + path
      
      i = 0
      dirtotal = len(dirlist)
      if dirtotal > 0:
         print('\nFOUND %d DIRECTORIES: \n' % dirtotal)
         while i < dirtotal:
            sel = i + 1
            print(str(sel) + ' - ' + str(dirlist[i]))
            i += 1
         print('')
         lim = dirtotal + 1
         matchtop = r'^(%s)(\/)?$' % toplevel
         if not re.match(matchtop,usedirremote):
            print('0 - RETURN UP ONE LEVEL TO PARENT DIRECTORY \n')
            startsel = '0-%d' % dirtotal
         else:
            startsel = '1-%d' % dirtotal
         selectdir = raw_input('make a selection [%s] --> ' % startsel)
         if not int(selectdir) in range(0, lim):
            selectdir = raw_input('invalid entry. please enter a selection %s --> ' % startsel)
         if selectdir == '0':
            usedirremote = parent
            subcont = 0
         else:
            n = int(selectdir) - 1
            usedir = dirlist[n]
            usedirremote = parent + usedir
            subcont = 1
      else:
         print('\nNO DIRECTORIES FOUND. searching in current directory..\n')
         subcont = 0
         usedirremote = parent + part
      return usedirremote, subcont, parent

   if links == 1:
      if 'found' not in locals():
         found = getlinks(cfurl)
         keep = 1
         
      while found > 0 and keep is not 0:
         def followlinks(bx):
            links = 0
            s = scraper.get(bx, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
            shtml = BeautifulSoup(s.text)
            sfindlinks = shtml.findAll('a')
            slen = len(sfindlinks)
            i = 0
            while i < slen:
               for slink in sfindlinks:
                  sl = slink.get('href')
                  if not re.match(r'^((\.\.)?\/)$', str(sl)):
                     sx = bx + sl
                     if '/' in sl[-1]:
                        followlinks(sx)
                     print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % sx)
                     try:
                        getCF(sx, links)
                     except KeyboardInterrupt:
                        print("\r\nskipping %s... \n" % sx)
                        continue
                     except (KeyboardInterrupt, SystemExit):
                        print("\r\nrequest cancelled by user\n")
                        break
                     except Exception, e:
                        print("\r\nan exception has occurred: %s \n" % str(e))
                        raise
                  else:
                     print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % bx)
                     try:
                        getCF(bx, links)
                     except KeyboardInterrupt:
                        print("\r\nskipping %s... \n" % bx)
                        continue
                     except (KeyboardInterrupt, SystemExit):
                        print("\r\nrequest cancelled by user\n")
                        break
                     except Exception, e:
                        print("\r\nan exception has occurred: %s \n" % str(e))
                        raise
                        sys.exit(1)
                  i += 1
                  
         follow = raw_input('fetch harvested links? enter Y/N --> ')
         while not re.search(r'^[yYnN]$', follow):
            follow = raw_input('invalid entry. enter Y to follow harvested links or N to quit --> ')
      
         if follow.lower() == 'y':
            r = scraper.get(cfurl, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
            html = BeautifulSoup(r.text)
            findlinks = html.findAll('a')
            s = []
            checkfordirs = 0
            for d in findlinks:
               if '/' in d.get('href')[-1]:
                  if not re.search(r'^(.*)(\/)$', str(d)):
                     s.append(str(d))
                     checkfordirs = 1
            
            if len(s) > 1 and checkfordirs == 1:
               if 'followdirs' not in locals():
                  followdirs = raw_input('follow directories? enter Y/N --> ')
                  while not re.search(r'^[yYnN]$', followdirs):
                     followdirs = raw_input('invalid entry. enter Y to follow directories or N to only retrieve files --> ')
                  if followdirs.lower() == 'y':
                     depth = 1
                  else:
                     depth = 0
                     break
               else:
                  if followdirs.lower() == 'y':
                     depth += 1
                  else:
                     depth -= 1
            else:
               followdirs = 'n'
               
            if findlinks:
               total = len(findlinks)
            else:
               total = 0
            if writeout == 1:
               if not os.path.exists(parentdir):
                  os.makedirs(parentdir)
            if total > 0:
               if followdirs.lower() == 'n':
                  links = 0
                  for link in findlinks:
                     b = link.get('href')
                     if not re.search(r'^(.*)(\/)$', str(b)):
                        b = parent + b
                        print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % b)
                        try:
                           getCF(b, links)
                        except KeyboardInterrupt:
                           print("\r\nskipping %s...\n" % b)
                           continue
                        except (KeyboardInterrupt, SystemExit):
                           print("\r\nrequest cancelled by user\n")
                           keep = 0
                           break
                        except Exception, e:
                           print("\r\nan exception has occurred: %s \n" % str(e))
                           raise
                        finally:
                           found = 0
                     else:
                        found = 0
                        continue
               elif followdirs.lower() == 'y' and depth > 0:
                  choosedir = raw_input("choose subdirectory? Y/N --> ")
                  while not re.match(r'^[YyNn]$', choosedir):
                     choosedir = raw_input("invalid entry. enter Y to pick subdirectory or N to download everything --> ")
                  if choosedir.lower() == 'n':
                     links = 0
                     for link in findlinks:
                        b = link.get('href')
                        bx = parent + b
                        if re.search(r'^(.*)(\/)$', str(b)):
                           followlinks(bx)
                        else:         
                           print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % bx)
                           try:
                              getCF(bx, links)
                              found = found - 1
                           except KeyboardInterrupt:
                              print("\r\nskipping %s... \n" % bx)
                              continue
                           except (KeyboardInterrupt, SystemExit):
                              print("\r\nrequest cancelled by user\n")
                              break
                           except Exception, e:
                              print("\r\nan exception has occurred: %s \n" % str(e))
                              raise
                              sys.exit(1)
                  else:
                     subcont = 1
                     usedirremote = cfurl
                     while subcont is not 0:
                        if subcont < 1:
                           break
                        usedirremote, subcont, parent = selectdir(usedirremote)
                        depth += 1
                        checksubdir = raw_input("enter 1 to select this directory, 2 to choose a subdirectory, or 3 to go back to parent directory --> ")
                        while not re.match(r'^[1-3]$', checksubdir):
                           checksubdir = raw_input("invalid input. enter a value 1-3 --> ")
                        if checksubdir is not 2:
                           break
                           
                     print('\nrequesting harvested URL: %s \r\n(press CTRL + C to skip) \n' % usedirremote)
                     try:
                        getCF(usedirremote, links)
                        found = found - 1
                     except KeyboardInterrupt:
                        print("\r\nskipping %s... \n" % usedirremote)
                     except (KeyboardInterrupt, SystemExit):
                        print("\r\nrequest cancelled by user\n")
                        keep = 0
                        break
                     except Exception, e:
                        print("\r\nan exception has occurred: %s \n" % str(e))
                        raise
                        sys.exit(1)
            
               elif followdirs.lower() == 'y' and depth < 1:
                  for link in findlinks:
                     b = link.get('href')
                     if not re.match(r'^((\.\.)?\/)$', str(b)):
                        bx = parent + b
                        print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % bx)
                        try:
                           getCF(bx, links)
                           found = found - 1
                        except KeyboardInterrupt:
                           print("\r\nskipping %s... \n" % bx)
                           continue
                        except (KeyboardInterrupt, SystemExit):
                           print("\r\nrequest cancelled by user\n")
                           break
                        except Exception, e:
                           print("\r\nan exception has occurred: %s \n" % str(e))
                           raise
                           sys.exit(1)
                        finally:
                           links = 0
                     else:
                        continue
                     
                     found = found - 1
                     
               else:
                  for link in findlinks:
                     b = link.get('href')
                     while b:
                        if not re.search(r'^(.*)(\/)$', str(b)):
                           b = parent + b
                           print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % b)
                           try:
                              getCF(b, links)
                           except KeyboardInterrupt:
                              print("\r\nskipping %s...\n" % b)
                              continue
                           except (KeyboardInterrupt, SystemExit):
                              print("\r\nrequest cancelled by user\n")
                              break
                           except Exception, e:
                              print("\r\nan exception has occurred: %s \n" % str(e))
                              raise
                        else:
                           continue
                        found = found - 1
         
            else:
               print("\ndid not find any links\n")
               found = found - 1
               keep = 0
               break
               
         else:
            r = scraper.get(cfurl, stream=True, verify=False, proxies=proxystring, allow_redirects=True)
            html = BeautifulSoup(r.text)
            findlinks = html.findAll('a')
            links = 0
            for link in findlinks:
               b = link.get('href')
               while b:
                  if not re.search(r'^(.*)(\/)$', str(b)):
                     b = parent + b
                     print("\nrequesting harvested URL: %s \r\n(press CTRL + C to skip)\n" % b)
                     try:
                        getCF(b, links)
                     except KeyboardInterrupt:
                        print("\r\nskipping %s...\n" % b)
                        continue
                     except (KeyboardInterrupt, SystemExit):
                        print("\r\nrequest cancelled by user\n")
                        break
                     except Exception, e:
                        print("\r\nan exception has occurred: %s \n" % str(e))
                        raise
                  else:
                     continue
                     
         print("\nno more links to fetch at %s.\n" % cfurl)
         cpath = p.path.strip('/')
         cpaths = cpath.split('/')
         lastpath = cpaths[-1]
         if len(lastpath) < 1 and len(cpaths) > 1:
            lastpath = cpaths[-2]
         cfurl = cfurl.strip('/')
         matchtop = r'^(%s)$' % toplevel
         if re.match(matchtop, cfurl):
            keep = 0
            print("\nfinished following all links.\n")
            break
         else:
            cfurl = cfurl.rstrip(lastpath)
            print('\ntrying %s.. \n' % cfurl)
   
try:
   getCF(cfurl, links)

except (KeyboardInterrupt, SystemExit):
   print("\r\nrequest cancelled by user\n")
   print("\r\nhit CTRL + C again to exit program, or it will automatically continue in 10 seconds.\n")
   try:
      time.sleep(10)
      getCF(cfurl, links)
   except KeyboardInterrupt:
      sys.exit("\nrequest cancelled by user.\n")
   except Exception, exc:
      print("\nan error has occurred: %s \n" % str(exc))
      sys.exit("unable to continue. check the URL and try again.\n")

except requests.exceptions.ConnectionError, e:
   print("\na connection error occurred: %s \n" % str(e))
   pass
   time.sleep(7)
   print("\nattempting to reconnect to %s...\n" % cfurl)
   try:
      getCF(cfurl, links)
   except Exception, exc:
      print("\nan exception has occurred %s \n" % str(exc))
      raise

except RuntimeError, e:
   print("\na runtime error has occurred: %s \n" % str(e))
   raise

except SyntaxError, e:
   print("\na typo is a silly reason to force a program to terminate..\n")
   print("\nespecially this one:\n %s \n" % str(e))
   raise
   
except IOError, e:
   print("\na connection error has occurred: %s \n" % str(e))
   pass
   time.sleep(7)
   print("\nattempting to reconnect to %s...\n" % cfurl)
   try:
      getCF(cfurl, links)
   except Exception, exc:
      print("\nan exception has occurred %s \n" % str(exc))
      print("unable to continue. please restart the program.\n")
      raise
      exit(1)

except Exception, e:
   print("\nan error has occurred: %s \n" % str(e))
   print("unable to continue. check the parameters and try again.\n")
   raise
   if debug == 1:
      traceback_template = '''Traceback (most recent call last):
      File "%(filename)s", line %(lineno)s, in %(name)s
   %(type)s: %(message)s\n'''
      traceback_details = {
                            'filename': sys.exc_info()[2].tb_frame.f_code.co_filename,
                            'lineno'  : sys.exc_info()[2].tb_lineno,
                            'name'    : sys.exc_info()[2].tb_frame.f_code.co_name,
                            'type'    : sys.exc_info()[0].__name__,
                            'message' : sys.exc_info()[1].message,
                           }
      print
      print(traceback.format_exc())
      #print(traceback.extract_tb(sys.exc_info()[2]))
      print(traceback_template % traceback_details)
   sys.exit(1)

finally:
   print("\nexiting..\n")
   
sys.exit(0)
