Supybot-Scores
======

Purpose

    Supybot plugin for displaying live sports scores.
    So far, it supports:
        - MLB, NBA, NFL, CFB, NCB, WCB, NHL, Golf, NASCAR, F1, Indycar, D1BB and Tennis.

Instructions

    Should work fine in an up-to-date Limnoria/supybot install with python 2.6+.
    Install via Git and `git pull` to grab updates as I continue to push.

Commands

    nba [--date YYMMDD] - to fetch basketball scores.
    nhl [--date YYMMDD] - to fetch hockey scores.
    nfl - to fetch football scores
    mlb [--date YYMMDD] - to fetch baseball scores
    cfb [conf] - to fetch college football scores (NCAA DIV. I-A (FBS))
    ncb [conf] - to fetch college basketball scores (NCAA DIV. I-A (FBS))
    wcb [conf] - to fetch women's college basketball scores (NCAA DIV. I-A (FBS))
    wnba [--date YYMMDD] - to fetch WNBA scores.
    tennis [mens|womens|mensdoubles|womensdoubles] - to fetch tennis scores.
    golf [pga|web.com|champions|lpga|euro]- to fetch golf scores
    nascar [nationwide|sprintcup|trucks] - show an active race/stats. (works for nationwide/sprint cup)
    d1bb - fetch Division 1 baseball scores.

Command Specifics

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

Config Variables

    There are a few documented and undocumented options.

    First, I have a corresponding database that can display "full teams" vs. their abbreviation (ex: NYK)

    - /msg <bot> config plugins.Scores.fullteams True/False

    This is helpful for searching (ex: !nba New York) but also takes up more room.

