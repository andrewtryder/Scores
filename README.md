[![Build Status](https://travis-ci.org/reticulatingspline/Scores.svg?branch=master)](https://travis-ci.org/reticulatingspline/Scores)

# Limnoria plugin for displaying sports scores

## Introduction

It supports: MLB, NBA, NFL, CFB, NCB, WCB, NHL, Golf, NASCAR, F1, Indycar, D1BB and Tennis.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/Scores
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load Scores
```

Now, you're good to go.

## Commands

* nba/nhl/nfl/mlb/ncf/ncb - can match teams to help with limiting output, which is great with ncb/cbb.

Ex: !nba bos - would match a celtics score.
Ex: !ncb michigan - would match anything Michigan.
Ex: !ncf bama - would match anything Bama.

* ncf/ncb/wcb - These can limit games via conferences.

Ex: !ncf SEC - show only SEC Football games.
Ex: !ncb ACC - show only ACC basketball games.
Ex: !wcb Big12 - show only women's college basketball games in the Big 12.

* You can use the ! option with the 4 major pro-sports (mlb, nhl, nba, nfl) to show only active/upcoming games.

Ex: !nfl ! - This will show all games but completed ones.

## Config

Config Variables

I have a corresponding database that can display "full teams" vs. their abbreviation (ex: NYK)

```
/msg <bot> config plugins.Scores.fullteams True/False
```

This is helpful for searching (ex: !nba New York) but also takes up more room.

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.
