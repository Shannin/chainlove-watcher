#!/usr/bin/env python

from BeautifulSoup import BeautifulSoup
import urllib3
import sys, time, re, subprocess
from daemon import Daemon

class ChainLoverWatcher(Daemon):
    http = urllib3.PoolManager()

    def scrapeChainLove(self):
        try:
            request = self.http.request('GET', 'http://www.chainlove.com')
        except URLError, exception_variable:
            print exception_variable.reason
            self.scrapeAfterDelay(600) # Try again in 10 min
        else:
            page = BeautifulSoup(request.data)

            titleTags = page.findAll('h1', {'id': 'item_title'})
            if len(titleTags) >= 1:
                titleTag = str(titleTags[0])
                title = re.search("<.*>(.*)</.*>", titleTag).group(1)

            priceTags = page.findAll('div', {'id': 'price'})

            if len(priceTags) >= 1:
                priceTag = str(priceTags[0])
                price = re.search("<.*>(.*)</.*>", priceTag).group(1)

            if (title and price):
                self.parseScrapedDetails(title, price)

            # Figure out delay for next scrape, and then scrape
            scripts = page.findAll('script', {'type': 'text/javascript'})
            for script in scripts:
                script = str(script)
                groups = re.search(".*BCNTRY.setupTimerBar\(([0-9]+)\,([0-9]+)\).*", script)
                if groups != None:
                    checkAgainDelay = int(groups.group(1))

            if not checkAgainDelay:
                checkAgainDelay = 720

            self.scrapeAfterDelay(checkAgainDelay + 30)

    def parseScrapedDetails(self, title, price):
        keywords = ['wheel', 'wheelset', 'rim', 'tire']

        shouldSendNotification = False
        for keyword in keywords:
            if keyword in title.lower():
                shouldSendNotification = True

        if shouldSendNotification:
            self.sendNotification(title + ' - ' + price)

    def sendNotification(self, message):
        # send notification
        args = ('/Users/shannin/Projects/ChainLoveWatcher/chainlove-notifier.app/Contents/MacOS/chainlove-notifier', '-title', 'Chain Love', '-open', 'http://www.chainlove.com', '-message', message)
        subprocess.call(args)

    def scrapeAfterDelay(self, delay):
        time.sleep(delay)
        self.scrapeChainLove()

    def run(self):
        self.scrapeAfterDelay(0)


if __name__ == "__main__":
    watcher = ChainLoverWatcher('/tmp/chainlove-watcher.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            watcher.start()
        elif 'stop' == sys.argv[1]:
            watcher.stop()
        elif 'restart' == sys.argv[1]:
            watcher.restart()
        else:
            print "Unknown command"
            sys.exit(2)
            sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
