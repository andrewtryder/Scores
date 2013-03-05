Supybot-Scores
======

Purpose

    Supybot plugin for displaying live sports scores. Works with MLB, NBA, NFL, CFB, NCB, NHL, Golf, NASCAR and Tennis.

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
    tennis [mens|womens|mensdoubles|womensdoubles] - to fetch tennis scores.
    golf - to fetch golf scores
    nascar [nationwide|sprintcup] - show an active race/stats. (works for nationwide/sprint cup)

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

    I have a few options that I'll consider "undocumented" as I don't recommend them but you can play with
    via the config variable system. /msg <botname> config search scores

    Each variable name should document itself but I recommend keeping things default.
