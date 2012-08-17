# coding=utf8
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import urllib2
from BeautifulSoup import BeautifulSoup
import re
import string
import datetime
import time

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Scores')

@internationalizeDocstring
class Scores(callbacks.Plugin):
    """Add the help for "@plugin help Scores" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def _validate(self, date, format):
        """Return true or false for valid date based on format."""
        try:
            datetime.datetime.strptime(date, format) # format = "%m/%d/%Y"
            return True
        except ValueError:
            return False

    def _b64decode(self, string):
        """Returns base64 encoded string."""
        import base64
        return base64.b64decode(string)

    def _fetch(self, optargs):
        """Internal function to fetch what we need."""
        
        url = self._b64decode('aHR0cDovL20uZXNwbi5nby5jb20v') + '%s&wjb=' % optargs.lower()
        
        #self.log.info(url)
        
        try:
            req = urllib2.Request(url)
            html = (urllib2.urlopen(req)).read()
            return html
        except:
            return None


    # start public functions. 
    #def nfl(self, irc, msg, args, optdate):
    def nfl(self, irc, msg, args):
        """
        Display NFL scores.
        """
        
        url = 'nfl/scoreboard?'
        html = self._fetch(url)
        
        if html == 'None':
            irc.reply("Cannot fetch NFL scores.")
            return
            
        html = html.replace('class="ind alt', 'class="ind')
        
        if "No games" in html:
            irc.reply("No games on today.")
            return

        soup = BeautifulSoup(html)
        divs = soup.findAll('div', attrs={'id':re.compile('game.*?')})

        object_list = []

        for div in divs:
            rows = div.findAll('a')
            for row in rows:
                game = row.text.strip()
                game = game.replace(', NFL','').replace(', ESPN', '').replace(', FOX','').replace(', CBS','').replace(', NBC','')
                if row.findParent('div').findParent('div').find('b', attrs={'class':'red'}):
                    game = game.replace('*', ircutils.mircColor('<RZ>','red'))
                else:
                    game = game.replace('*', ircutils.mircColor('<>','red'))
                game = game.replace('Half', ircutils.mircColor('H', 'yellow'))
                game = game.replace('Final', ircutils.mircColor('F', 'red'))
                game = game.replace('1st', ircutils.mircColor('1st', 'green'))
                game = game.replace('2nd', ircutils.mircColor('2nd', 'green'))
                game = game.replace('3rd', ircutils.mircColor('3rd', 'green'))
                game = game.replace('4th', ircutils.mircColor('4th', 'green'))
                
            
                if " at " not in game: # handles games in progress.
                    gamesplit = game.split(' ') 
                    awayteam = gamesplit[0]
                    awayscore = gamesplit[1]
                    hometeam = gamesplit[2]
                    homescore = gamesplit[3]
                    time = gamesplit[4:]
                    time = " ".join(time)
                    
                    # bold the leader
                    if int(awayscore) > int(homescore):
                        awayteam = ircutils.bold(awayteam)
                        awayscore = ircutils.bold(awayscore)
                    elif int(homescore) > int(awayscore):
                        hometeam = ircutils.bold(hometeam)
                        homescore = ircutils.bold(homescore)
                
                    game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " " + time) 

                object_list.append(game)

        allgames = string.join([item for item in object_list], " | ")

        irc.reply(allgames)

    #nfl = wrap(nfl, [optional('somethingWithoutSpaces')])
    nfl = wrap(nfl)

    
    def mlb(self, irc, msg, args, optdate):
        """
        Display MLB scores.
        """
    
        if optdate:
            testdate = self._validate(optdate, '%Y%m%d')
            if not testdate:
                irc.reply("Invalid year. Must be YYYYmmdd.")
                return
        #else:
        #    optdate = datetime.datetime.now().strftime("%Y%m%d")

        url = 'mlb/scoreboard?'

        if optdate:
            url += 'date=%s' % optdate

        html = self._fetch(url)
        if html == 'None':
            irc.reply("Cannot fetch mlb scores.")
            return
            
        html = html.replace('class="ind alt', 'class="ind')
        
        if "No games" in html:
            irc.reply("No games on today.")
            return

        soup = BeautifulSoup(html)
        rows = soup.findAll('div', attrs={'class':'ind', 'style':'white-space: nowrap;'})

        object_list = []

        for row in rows:
            game = row.find('a').text.strip() # rather simple parse here.
            game = game.replace('SDG', 'SD').replace('SFO', 'SF').replace('TAM', 'TB').replace('WAS', 'WSH').replace('KAN', 'KC').replace('CHW', 'CWS') # teams.
            game = game.replace(', ESPN', '').replace(', MLBN', '').replace(', TBS', '').replace(' PM','').replace(' AM','').replace(', ESP2', '')
            game = game.replace('Del', ircutils.mircColor('DLY', 'yellow'))
            
            if " at " not in game: # handles games in progress.
                game = game.replace('Bot ','B').replace('Top ','T').replace('Mid ','M').replace('End ','E') # innings
                game = game.replace('st','').replace('th','').replace('rd','').replace('nd','') # abbr
                gamesplit = game.split(' ') 
                awayteam = gamesplit[0]
                awayscore = gamesplit[1]
                hometeam = gamesplit[2]
                homescore = gamesplit[3]
                innings = gamesplit[4]

                # bold the leader
                if int(awayscore) > int(homescore):
                    awayteam = ircutils.bold(awayteam)
                    awayscore = ircutils.bold(awayscore)
                elif int(homescore) > int(awayscore):
                    hometeam = ircutils.bold(hometeam)
                    homescore = ircutils.bold(homescore)
                
                game = str(awayteam + " " + awayscore + " " + hometeam + " " + homescore + " ") 
                if innings.startswith('F'):
                    innings = innings.replace('Final','F')
                    game += ircutils.mircColor(innings, 'red')
                else:
                    game += ircutils.mircColor(innings, 'green')

            object_list.append(game)

        allgames = string.join([item for item in object_list], " | ")

        irc.reply(allgames)

    mlb = wrap(mlb, [optional('somethingWithoutSpaces')])
    
Class = Scores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
