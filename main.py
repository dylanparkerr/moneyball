import pybaseball as pyb
import pandas as pd
import requests as req
import datetime

def get_team_id(team_abr: str):
    teams = pyb.team_ids(2019)
    return teams.query(f"franchID == '{team_abr}'")['teamIDfg'].to_string().split(" ")[-1]


def get_current_offense_roster(team_abr: str):
    id = get_team_id(team_abr)

    resp = req.get(f'https://www.fangraphs.com/api/depth-charts/roster?teamid={id}')
    full_roster = resp.json()

    offense_roles = ['1','2','3','4','5','6','7','8','9','Bench']
    offense_roster = []
    for player in full_roster:
        if player['role'] in offense_roles:
            order = 10 if player['role'] == 'Bench' else int(player['role'])
            offense_roster.append({
                'name': player['player'],
                'id': int(player['playerid2']),
                'order': order
            })

    resp = req.get(f'https://www.fangraphs.com/api/depth-charts/past-lineups?teamid={id}') 
    latest_game = resp.json()[0]
    todays_roster_out = latest_game['gameList']['gameDate'] == datetime.date.today().strftime('%#m/%#d/%Y')
    if todays_roster_out:
        new_offense_order =[]
        for player in latest_game['dataPlayers']:
            new_offense_order.append({
                'name': player['playerName'],
                'id': int(player['playerid']),
                'order': player['BO']
            })
        existing_ids = {player['id'] for player in new_offense_order} 

        for player in offense_roster:
            if player['id'] not in existing_ids:
                new_offense_order.append({
                    'name': player['name'],
                    'id': player['id'],
                    'order': 10 # on the bench for this game
                })
        offense_roster = sorted(new_offense_order, key=lambda d: d['order'])
    # print(offense_roster)
    return offense_roster


def get_batting_stats(team_abr: str, start_date='', end_date=''):
    team_id = get_team_id(team_abr)
    roster = get_current_offense_roster(team_abr)
    batting_df = pd.DataFrame()

    bat_stats = pyb.batting_stats(start_season=datetime.date.today().year, team=team_id, qual=0, position='np', start_date=start_date, end_date=end_date)

    for player in roster:
        batting_df = pd.concat([batting_df, bat_stats.query(f'IDfg == {player["id"]}')])

    cols = [
        'Name'
        # ,'IDfg'
        ,'HR'
        ,'RBI'
        ,'wOBA'
        ,'wRC+'
        ,'WAR'
        ,'OPS'
    ]
    print(batting_df[cols].to_string(index=False))


def batting_stats_panel(team):
    today = datetime.date.today().strftime('%Y-%m-%d') 
    seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    thirty_days_ago = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
    print('-----------------------------------------------------------------------')
    print(f'{team} Season')
    get_batting_stats(team)

    print('-----------------------------------------------------------------------')
    print(f'{team} Last 7 Days')
    get_batting_stats(team, start_date=seven_days_ago, end_date=today)

    print('-----------------------------------------------------------------------')
    print(f'{team} Last 30 Days')
    get_batting_stats(team, start_date=thirty_days_ago, end_date=today)


def main():
    team = 'ATL'

    today = datetime.date.today()
    year = today.year
    formated_date = today.strftime("%A, %#b %#d")

    # find opponent
    schedule = pyb.schedule_and_record(year,team)
    todays_game = schedule.query(f"Date == '{formated_date}'")
    opponent = todays_game['Opp'].to_string().split(" ")[-1]
    home_or_away = todays_game['Home_Away'].to_string().split(" ")[-1]

    if home_or_away == 'Home':
        print(f'Game on {formated_date}: {opponent} @ {team}')
    else:
        print(f'Game on {formated_date}: {team} @ {opponent}')
    print()
    
    batting_stats_panel(team)
    batting_stats_panel(opponent)


if __name__ == "__main__":
    main()

