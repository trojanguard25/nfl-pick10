import nflgame

games = nflgame.games(2015,week=1)
games_gen = nflgame.games_gen(2015,week=1)

for g in games:
    print g.home
    print g.away
    print g.score_away
    print g.score_home

