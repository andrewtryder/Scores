#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from BeautifulSoup import BeautifulSoup
import urllib2
import sqlite3

def _checkteam(optteam):
    optsport = 'ncf'
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute("SELECT full FROM teams WHERE short=? AND sport=?", (optteam, optsport))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        return None
    else:
        return True

urls = [
    'http://m.espn.go.com/ncf/scoreboard?date=20130903&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20130910&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20130917&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20130924&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131001&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131008&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131015&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131022&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131029&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131105&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131112&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131119&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131126&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20131203&wjb=&groupId=80',
    'http://m.espn.go.com/ncf/scoreboard?date=20130903&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20130910&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20130917&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20130924&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131001&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131008&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131015&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131022&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131029&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131105&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131112&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131119&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131126&wjb=&groupId=81',
    'http://m.espn.go.com/ncf/scoreboard?date=20131203&wjb=&groupId=81'
    ]

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

print "GAMELINKS LENGTH: {0}".format(len(gamelinks))

teamdict = {}

for url in gamelinks:
    req = urllib2.Request(url)
    html = (urllib2.urlopen(req)).read()
    soup = BeautifulSoup(html)
    table = soup.find('table', attrs={'class':'wide', 'width':'100%'})
    teamlinks = table.findAll('a', attrs={'class':'bold'})
    for teamlink in teamlinks:
        team = teamlink.getText().replace('&amp;', '&').replace(';', '')
        if not _checkteam(team):  # team is NOT in the DB for sport.
            if team not in teamdict:
                link = teamlink['href'].replace('clubhouse?teamId=','').replace('&amp;wjb=','')
                teamdict[team] = 'http://m.espn.go.com/ncf/clubhouse?teamId='+link+'&wjb='
                print team + " = " + 'http://m.espn.go.com/ncf/clubhouse?teamId='+link+'&wjb='

print "MISSING TEAMS: {0}".format(len(teamdict))
# now grab those teams.
for k, url in teamdict.items():
    req = urllib2.Request(url)
    html = (urllib2.urlopen(req)).read()
    soup = BeautifulSoup(html)
    tn = soup.find('td', attrs={'class':'teamHeader', 'valign':'middle'}).find('b').getText()
    print "INSERT INTO teams (sport, full, short) VALUES ('ncf', '{0}', '{1}');".format(tn, k)
