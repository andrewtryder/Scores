#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from BeautifulSoup import BeautifulSoup
import urllib2 

urls = ['http://m.espn.go.com/ncf/scoreboard?groupId=80&date=20121210&fa6d457i37cx0=GO&y=1&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20121126&groupId=80&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20121119&groupId=80&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20121112&groupId=80&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20121029&groupId=80&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20120910&groupId=80&wjb=',
        'http://m.espn.go.com/ncf/scoreboard?date=20120903&groupId=80&wjb=']

gamelinks = []

for url in urls:
    req = urllib2.Request(url)
    html = (urllib2.urlopen(req)).read()
    soup = BeautifulSoup(html)
    games = soup.findAll('div', attrs={'id':re.compile('^game\d+')})
    
    for game in games:
        link = game.find('a')
        link = 'http://m.espn.go.com'+link['href']
        gamelinks.append(str(link))   

print len(gamelinks)

teamdict = {}

for url in gamelinks:
    req = urllib2.Request(url)
    html = (urllib2.urlopen(req)).read()
    soup = BeautifulSoup(html)
    table = soup.find('table', attrs={'class':'wide', 'width':'100%'})
    teamlinks = table.findAll('a', attrs={'class':'bold'})
    for teamlink in teamlinks:
        team = teamlink.text
        link = teamlink['href'].replace('clubhouse?teamId=','').replace('&amp;wjb=','')
        teamdict[team] = 'http://m.espn.go.com/ncf/clubhouse?teamId='+link+'&wjb='
        print team + " = " + 'http://m.espn.go.com/ncf/clubhouse?teamId='+link+'&wjb='

print teamdict
