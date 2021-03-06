import nflgame
import argparse
import xlrd
import string
import pymysql


class Pick10Inf:
    def __init__(self):
        self.conn = pymysql.connect(host='localhost', port=3306, user='dan', passwd='0ldn0teb00k', db='pick10')

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
        sql = "SELECT * FROM games where home_team = '%s' and away_team = '%s' and week=%d" % (self.getNflgameName(home), self.getNflgameName(away), week)

        #print sql
        cur.execute(sql)
        if cur.fetchone() == None:
            print "game doesn't exist"
            insert_sql = "INSERT INTO games (week, home_team, away_team) VALUES (%d, '%s', '%s')" % (week, self.getNflgameName(home), self.getNflgameName(away))
            print insert_sql
            cur.execute(insert_sql)
            cur.connection.commit()
        else:
            print "game exists"

    def addSpread(self, week, team, spread):
        self.checkTeam(team)
        cur = self.conn.cursor()

        insert_sql = "INSERT INTO spreads (team, week, spread) VALUES ('%s', %d, %f) ON DUPLICATE KEY UPDATE spread=%f" % (self.getNflgameName(team), week, spread, spread)
        #print insert_sql
        cur.execute(insert_sql)
        cur.connection.commit()
        
        cur.close()


    def addPick(self, week, player, team, points):
        self.checkTeam(team)
        self.checkPlayer(player)
        cur = self.conn.cursor()

        insert_sql = "INSERT INTO picks (name, team, week, points) VALUES ('%s', '%s', %d, %d) ON DUPLICATE KEY UPDATE points=%d" % (player, self.getNflgameName(team), week, points, points)
        #print insert_sql

        cur.execute(insert_sql)
        cur.connection.commit()
        
        cur.close()


parser= argparse.ArgumentParser(description='NFL Pick10 status.')

parser.add_argument('-i', '--input', help='Weekly Excel Spreadsheet', required=True)

args = parser.parse_args()

pick10 = Pick10Inf()

wb = xlrd.open_workbook(args.input)
from xlrd.sheet import ctype_text

print wb

sheet_names = wb.sheet_names()
print('Sheet Names', sheet_names)

sheet = wb.sheet_by_name('Weekly Sheet')

week_cell = sheet.cell(0,0)

print week_cell

week = string.split(week_cell.value)[1]

row = sheet.row(2)
'''
print('(Column #) type:value')
for idx, cell_obj in enumerate(row):
    cell_type_str = ctype_text.get(cell_obj.ctype, 'unknown type')
    print('(%s) %s %s' % (idx, cell_type_str, cell_obj.value))
'''

# Print all values, iterating through rows and columns
#

picks = {}
spread_idx = 0
num_cols = sheet.ncols   # Number of columns
for row_idx in range(3, sheet.nrows):    # Iterate through rows
    #print ('-'*40)
    #print ('Row: %s' % row_idx)   # Print row number
    name_obj = sheet.cell(row_idx, 0)
    if not name_obj.value:
        spread_idx = row_idx + 1
        break

    picks[name_obj.value] = []
    points = 10
    for col_idx in range(1, 11):  # Iterate through columns
        cell_obj = sheet.cell(row_idx, col_idx)  # Get cell object by row, col
        team = cell_obj.value.strip()
        picks[name_obj.value].insert(0, team)
        if team:
            pick10.addPick(int(week), name_obj.value, team, points)
        points = points - 1
        #print ('Column: [%s] cell_obj: [%s]' % (col_idx, cell_obj))

spreads = []
spread = ''
spread_found = False
fav = ''
fav_found = False
und = ''
und_found = False
for row_idx in range(spread_idx, sheet.nrows):
    for col_idx in range(1, num_cols):
        cell_obj = sheet.cell(row_idx, col_idx)
        if not cell_obj.value:
            spread_found = False
            fav_found = False
            und_found = False
        elif cell_obj.ctype == xlrd.XL_CELL_TEXT and cell_obj.value.isspace():
            spread_found = False
            fav_found = False
            und_found = False
        elif not fav_found:
            fav_found = True
            fav = cell_obj.value
        elif not spread_found:
            spread_found = True
            if cell_obj.value == 'Pk':
                spread = 0.0
            else:
                spread = cell_obj.value
        elif not und_found:
            und_found = True
            und = cell_obj.value

        if fav_found and spread_found and und_found:
            match = {}
            match['fav'] = fav
            match['spread'] = spread
            match['und'] = und
            spreads.append(match)
            spread_found = False
            fav_found = False
            und_found = False

print spreads

print len(spreads)

# get schedule and results for the week
games = nflgame.games(2015,week=int(week))

scores = {}

for g in games:
    diff1 = g.score_away - g.score_home
    diff2 = g.score_home - g.score_away
    scores[g.away] = diff1;
    scores[g.home] = diff2;
    pick10.addGame(int(week), g.home, g.away)

print scores

team_spread = {}

for x in spreads:
    team_spread[x['und'].upper()] = x['spread']
    pick10.addSpread(int(week), x['und'], x['spread'])
    team_spread[x['fav'].upper()] = -x['spread']
    pick10.addSpread(int(week), x['fav'], -x['spread'])
   
print team_spread

covers = {}
for key, value in scores.iteritems():
    nfl_key = getNflgameName(key)
    spread = team_spread[nfl_key]
    if spread + value > 0:
        covers[nfl_key] = 1
    elif spread + value == 0:
        covers[nfl_key] = 0.5
    else:
        covers[nfl_key] = 0

print covers

final_scores = {}
for name, games in picks.iteritems():
    print name
    total_score = 0
    points = 1
    for g in games:
        if g:
            print points, getNflgameName(g)
            total_score = total_score + points * covers[getNflgameName(g)]
        points = points + 1

    final_scores[name] = total_score
        
for name, score in final_scores.iteritems():
    print "%s, %f" % (name, score)

# create standard keys between picks, spread and nflgames

# store picks and mn score
## go row by row
## select name
## store picks in a dict? picks['dan']['10']? or arr? picks['dan'][0] array with 0 index MN score?

# store spread values

# calculate results

# output results
## xml? html?

# store results in db
## use postgres db like used in nfldb? or use existing mysql db?
