import nflgame
import argparse
import xlrd
import string
from pick10 import Pick10Inf


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

spread_idx = 0
num_cols = sheet.ncols   # Number of columns
for row_idx in range(3, sheet.nrows):    # Iterate through rows
    name_obj = sheet.cell(row_idx, 0)
    if not name_obj.value:
        spread_idx = row_idx + 1
        break

    points = 10
    for col_idx in range(1, 11):  # Iterate through columns
        cell_obj = sheet.cell(row_idx, col_idx)  # Get cell object by row, col
        team = cell_obj.value.strip()
        if team:
            pick10.addPick(int(week), name_obj.value, team, points)
        points = points - 1

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

# get schedule and results for the week
games = nflgame.games(2015,week=int(week))

scores = {}

for g in games:
    diff1 = g.score_away - g.score_home
    diff2 = g.score_home - g.score_away
    scores[g.away] = diff1;
    scores[g.home] = diff2;
    pick10.addGame(int(week), g.home, g.away)

team_spread = {}

for x in spreads:
    team_spread[x['und'].upper()] = x['spread']
    pick10.addSpread(int(week), x['und'], x['spread'])
    team_spread[x['fav'].upper()] = -x['spread']
    pick10.addSpread(int(week), x['fav'], -x['spread'])
  


