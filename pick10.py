import pymysql
import nflgame
from datetime import datetime

class Pick10Inf:
    def __init__(self):
        self.conn = pymysql.connect(host='localhost', port=3306, user='dan', passwd='0ldn0teb00k', db='pick10')
        i = datetime.now()
        self.season = int(i.year)
        if int(i.month) <= 3:
            self.season = self.season - 1

    def getNflgameName(self, name):
        if name.upper() == 'ARI':
            return 'ARZ'
        else:
            return name.upper()

    def checkPlayer(self, name):
        cur = self.conn.cursor()
        sql = "SELECT * FROM players where name = '%s'" % name.upper()
        cur.execute(sql)
        if cur.fetchone() == None:
            print "Player name %s not in db" % name.upper() 
            insert_sql = "INSERT INTO players (name) VALUES ('%s')" % name.upper()
            print insert_sql
            cur.execute(insert_sql)
            cur.connection.commit()

        cur.close()

    def checkTeam(self, teamname):
        cur = self.conn.cursor()
        sql = "SELECT * FROM teams where team = '%s'" % self.getNflgameName(teamname)

        #print sql

        cur.execute(sql)
        if cur.fetchone() == None:
            print "Team name %s not in db" % self.getNflgameName(teamname)
            insert_sql = "INSERT INTO teams (team) VALUES ('%s')" % self.getNflgameName(teamname)
            print insert_sql
            cur.execute(insert_sql)
            cur.connection.commit()
        #else:
            #print "Team name %s is in db" % self.getNflgameName(teamname)

        cur.close()

    def addGame(self, week, home, away):
        self.checkTeam(home)
        self.checkTeam(away)
        cur = self.conn.cursor()
        sql = "SELECT * FROM games where home_team = '%s' and away_team = '%s' and week=%d and season=%d" % (self.getNflgameName(home), self.getNflgameName(away), week, self.season)

        #print sql
        cur.execute(sql)
        if cur.fetchone() == None:
            print "game doesn't exist"
            insert_sql = "INSERT INTO games (season, week, home_team, away_team) VALUES (%d, %d, '%s', '%s')" % (self.season, week, self.getNflgameName(home), self.getNflgameName(away))
            print insert_sql
            cur.execute(insert_sql)
            cur.connection.commit()
        else:
            print "game exists"

    def addSpread(self, week, team, spread):
        self.checkTeam(team)
        cur = self.conn.cursor()

        insert_sql = "INSERT INTO spreads (team, week, season, spread) VALUES ('%s', %d, %d, %f) ON DUPLICATE KEY UPDATE spread=%f" % (self.getNflgameName(team), week, self.season, spread, spread)
        #print insert_sql
        cur.execute(insert_sql)
        cur.connection.commit()
        
        cur.close()


    def addPick(self, week, player, team, points):
        self.checkTeam(team)
        self.checkPlayer(player)
        cur = self.conn.cursor()

        insert_sql = "INSERT INTO picks (name, team, week, season, points) VALUES ('%s', '%s', %d, %d, %d) ON DUPLICATE KEY UPDATE points=%d" % (player, self.getNflgameName(team), week, self.season, points, points)
        #print insert_sql

        cur.execute(insert_sql)
        cur.connection.commit()
        
        cur.close()

    def updateGames(self):
        #cur = self.conn.cursor()
        week = 15

        games = nflgame.games(self.season,week=int(week))
        for g in games:
            print g
            self.addGame(week, g.home, g.away)
            #insert_sql = "INSERT INTO games (home_team, away_team, week, season, home_score, away_score) VALUES ('%s', '%s', %d, %d, %d, %d) ON DUPLICATE KEY UPDATE home_score=%d, away_score=%d" % (self.getNflgameName(g.home), self.getNflgameName(g.away), week, self.season, g.score_home, g.score_away, g.score_home, g.score_away)
        
            #cur.execute(insert_sql)
            #cur.connection.commit()
        
        #cur.close()

    def updatePicks(self):
        cur = self.conn.cursor()

        update_sql = 'UPDATE picks p INNER JOIN spreads s ON p.team = s.team AND p.week = s.week AND p.season = s.season SET p.score = s.cover * p.points WHERE s.cover IS NOT NULL;'

        print update_sql

        cur.execute(update_sql)
        cur.connection.commit()
        cur.close()

    def updateScores(self):
        cur = self.conn.cursor()

        # query for all games that are not in final state
        sql = "Select id, week, home_team, away_team, season FROM games WHERE final=0 ORDER BY week"
        cur.execute(sql)

        week = 0
        games = None

        update_sql = ""
        #updated_spreads = {}
        for row in cur:
            print row
            if row[1] != week:
                week = row[1]
                # get schedule and results for the week
                games = nflgame.games(self.season,week=int(week))
                scores = {}
                final = {}
                for g in games:
                    print g
                    scores[self.getNflgameName(g.away)] = g.score_away;
                    scores[self.getNflgameName(g.home)] = g.score_home;
                    final[self.getNflgameName(g.home)] = g.game_over();

            season = row[4]
            table_id = row[0]
            home_team = row[2]
            away_team = row[3]

            home_score = scores[home_team]
            away_score = scores[away_team]

            single_sql = "UPDATE games SET home_score = %d, away_score = %d, final = %d WHERE id=%s;" % (home_score, away_score, final[home_team], table_id)

            if final[home_team] == True:
                away_margin = away_score - home_score
                home_margin = home_score - away_score

                #updated_spreads[home_team] = home_margin
                #updated_spreads[away_team] = away_margin

                home_spread_sql = 'UPDATE spreads SET cover = CASE WHEN spread + %d > 0 THEN 1.0 WHEN spread + %d < 0 THEN 0.0 ELSE 0.5 END WHERE team=\'%s\' AND week=%d AND season=%d;' % (home_margin, home_margin, home_team, week, self.season)
                away_spread_sql = 'UPDATE spreads SET cover = CASE WHEN spread + %d > 0 THEN 1.0 WHEN spread + %d < 0 THEN 0.0 ELSE 0.5 END WHERE team=\'%s\' AND week=%d AND season=%d;' % (away_margin, away_margin, away_team, week, self.season)

                update_sql = update_sql + home_spread_sql + away_spread_sql


            update_sql = update_sql + single_sql


        print update_sql
        if update_sql:
            cur.execute(update_sql)
            cur.connection.commit()


        cur.close()

'''


            diff1 = g.score_away - g.score_home
            diff2 = g.score_home - g.score_away
            pick10.addGame(int(week), g.home, g.away)
'''
