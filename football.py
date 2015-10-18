import nflgame
import argparse
import xlrd
import string

parser= argparse.ArgumentParser(description='NFL Pick10 status.')

parser.add_argument('-i', '--input', help='Weekly Excel Spreadsheet', required=True)

args = parser.parse_args()

wb = xlrd.open_workbook(args.input)

print wb

sheet_names = wb.sheet_names()
print('Sheet Names', sheet_names)

sheet = wb.sheet_by_name('Weekly Sheet')

week_cell = sheet.cell(0,0)

print week_cell

week = string.split(week_cell.value)[1]

games = nflgame.games(2015,week=int(week))

for g in games:
    print g.away
    print g.score_away
    print g.home
    print g.score_home

