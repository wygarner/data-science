

import json
import urllib3
import certifi
import sqlite3
import pandas as pd


conn= sqlite3.connect('NCAAF.db')

c= conn.cursor()

http= urllib3.PoolManager(cert_reqs= 'CERT_REQUIRED', ca_certs= certifi.where())


class Play:
    def __init__(self,plays_dict_list,year,week):
        self.plays_dict_list= plays_dict_list
        self.year= year
        self.week= week
        self.get_data()
        
    def get_data(self):
        for play in self.plays_dict_list:
            if play['play_type'] in ['Pass Incompletion','Pass Completion','Rush','Pass Interception','Sack',
                   'Penalty','Fumble Recovery (Own)','Safety','Pass Reception','Fumble Recovery (Opponent)',
                   'Pass','Interception','Passing Touchdown','Rushing Touchdown','Pass Interception Return',
                   'Interception Return Touchdown']:
                print(play,'\n')
                print(self.plays_dict_list.index(play),',',self.year,',',self.week,'\n')
                self.play_id= play['id']
                self.offense_team= play['offense']
                self.defense_team= play['defense']
                self.drive_id= play['drive_id']
                self.quarter= play['period']
                self.clock= play['clock']['minutes']+(play['clock']['seconds']/60)
                self.yard_line= play['yard_line']
                self.down= play['down']
                self.yards_to_gain= play['distance']
                self.yards_gained= play['yards_gained']
                self.play_type= play['play_type']
                self.ppa= play['ppa']
                games= http.request('GET', 'https://api.collegefootballdata.com/games?year='+str(self.year)+'&week='+str(self.week)+'&team='+self.offense_team.replace(' ','%20').replace('&','%26').replace('é','%C3%A9')+'&seasonType=regular')
                games_dict_list= json.loads(games.data.decode('UTF-8'))
                self.game_id= games_dict_list[0]['id']
                
    def update_table(self):
        c.execute("INSERT INTO plays VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(self.play_id,self.drive_id,
                  self.game_id,self.year,self.week,self.offense_team,self.defense_team,self.clock,self.quarter,
                  self.yard_line,self.down,self.yards_to_gain,self.play_type,self.yards_gained,self.ppa))
        conn.commit()
        

class Drive:
    def __init__(self,drives_dict_list,year,week):
        self.drives_dict_list= drives_dict_list
        self.year= year
        self.week= week
        self.get_data()
        
    def get_data(self):
        for drive in self.drives_dict_list:
            print(drive,'\n')
            print(self.drives_dict_list.index(drive),',',self.year,',',self.week,'\n')
            self.drive_id= drive['id']
            self.game_id= drive['game_id']
            games=http.request('GET','https://api.collegefootballdata.com/games?year='+str(self.year)+'&seasonType=regular&id='+str(self.game_id))
            games_dict_list= json.loads(games.data.decode('UTF-8'))
            self.home_team= games_dict_list[0]['home_team']
            self.offense_team= drive['offense']
            self.defense_team= drive['defense']
            if self.home_team==self.offense_team:
                self.drive_start= drive['start_yardline']
                if drive['end_yardline']>=60:
                    self.inside_40_TF=True
                else:
                    self.inside_40_TF=False
            else:
                self.drive_start= 100-drive['start_yardline']
                if drive['end_yardline']<=40:
                    self.inside_40_TF=True
                else:
                    self.inside_40_TF=False
            self.drive_result= drive['drive_result']
            
    def update_table(self):
        c.execute("INSERT INTO drives VALUES (?,?,?,?,?,?,?,?,?)",(self.drive_id,self.game_id,self.year,self.week,
                  self.offense_team,self.defense_team,self.drive_start,self.drive_result,self.inside_40_TF))
        conn.commit()
        
        
class Game:
    def __init__(self,games_dict_list):
        self.games_dict_list= games_dict_list
        self.get_data()
        self.update_table()
        
    def get_data(self):
        for game in self.games_dict_list:
            self.game_id= game['id']
            self.year= game['season']
            self.week= game['week']
            print(game,'\n')
            print('index: ',self.games_dict_list.index(game),',',self.year,',',self.week,'\n')
            self.home_team= game['home_team']
            self.away_team= game['away_team']
            self.home_score= game['home_points']
            self.away_score= game['away_points']
            
            self.plays_df= pd.read_sql_query('SELECT * FROM plays WHERE plays.game_id=?',
                                             conn,params=[self.game_id])
            self.drives_df= pd.read_sql_query('SELECT * FROM drives WHERE drives.game_id=?',
                                              conn,params=[self.game_id])
            
            if len(self.plays_df)>0 and len(self.drives_df)>0:
                home_team_plays= self.plays_df['offense_team']==self.home_team
                home_team_drives= self.drives_df['offense_team']==self.home_team
                away_team_plays= self.plays_df['offense_team']==self.away_team
                away_team_drives= self.drives_df['offense_team']==self.away_team
                self.home_team_plays_df= self.plays_df.iloc[home_team_plays.values]
                self.home_team_drives_df= self.drives_df.iloc[home_team_drives.values]
                self.away_team_plays_df= self.plays_df.iloc[away_team_plays.values]
                self.away_team_drives_df= self.drives_df.iloc[away_team_drives.values]
                
                if len(self.away_team_plays_df)>0 and len(self.home_team_plays_df)>0:
                    self.ypp_tuple= self.get_ypp()
                    self.home_success_rate_ppapsp= self.get_success_rate_ppapsp(self.home_team_plays_df)
                    self.away_success_rate_ppapsp= self.get_success_rate_ppapsp(self.away_team_plays_df)
                    self.afp_tuple= self.get_afp()
                    self.home_ppti40= self.get_ppti40(self.home_team_drives_df)
                    self.away_ppti40= self.get_ppti40(self.away_team_drives_df)
                    self.home_turnovers= self.get_turnover_rate(self.home_team_plays_df)
                    self.away_turnovers= self.get_turnover_rate(self.away_team_plays_df)
                    
    def update_table(self):
        home_ypp= self.ypp_tuple[0]
        away_ypp= self.ypp_tuple[1]
        home_success_rate= self.home_success_rate_ppapsp[0]
        away_success_rate= self.away_success_rate_ppapsp[0]
        home_total_plays= self.home_success_rate_ppapsp[2]
        away_total_plays= self.away_success_rate_ppapsp[2]
        home_ppapsp= self.home_success_rate_ppapsp[1]
        away_ppapsp= self.away_success_rate_ppapsp[1]
        home_afp= self.afp_tuple[0]
        away_afp= self.afp_tuple[1]
        home_ppti40= self.home_ppti40
        away_ppti40= self.away_ppti40
        home_turnovers= self.home_turnovers
        away_turnovers= self.away_turnovers
        
        if 45<=home_total_plays<=105 and 42<=away_total_plays<=106:
            c.execute("INSERT INTO games VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(self.game_id,
                      self.year,self.week,self.home_team,self.away_team,home_ypp,home_success_rate,home_ppapsp,
                      home_afp,home_ppti40,home_turnovers,away_ypp,away_success_rate,away_ppapsp,away_afp,
                      away_ppti40,away_turnovers,home_total_plays,away_total_plays,self.home_score,self.away_score))
        conn.commit()
                    
    def get_ypp(self):
        home_team_ypp= round(self.home_team_plays_df['yards_gained'].sum()/len(self.home_team_plays_df),3)
        away_team_ypp= round(self.away_team_plays_df['yards_gained'].sum()/len(self.away_team_plays_df),3)
    
        return home_team_ypp,away_team_ypp

    def get_success_rate_ppapsp(self,df):     
        total_plays=0
        successful_plays_total=0
        total_ppapsp=0
        for i in range(1,5):
            if i==1:
                yard_modifier=.5
            elif i==2:
                yard_modifier=.7
            else:
                yard_modifier=1
            down= df['down']==i
            down_df= df.iloc[down.values]
            successful_plays= down_df['yards_gained']>=(down_df['yards_to_gain']*yard_modifier)
            successful_plays_df= down_df.iloc[successful_plays.values]
            total_plays+=len(down_df)
            successful_plays_total+=len(successful_plays_df)
            total_ppapsp+=successful_plays_df['ppa'].sum()
    
        return round(successful_plays_total/total_plays,3),round(total_ppapsp/total_plays,3),total_plays

    def get_afp(self):
        home_team_afp= round(self.home_team_drives_df['drive_start'].sum()/len(self.home_team_drives_df),3)
        away_team_afp= round(self.away_team_drives_df['drive_start'].sum()/len(self.away_team_drives_df),3)
        
        return home_team_afp, away_team_afp

    def get_ppti40(self,df):
        inside_40= df['inside_40_TF']=='1'
        inside_40_df= df.iloc[inside_40.values]
        drive_results= inside_40_df['drive_result'].value_counts()
        try:
            td_count= drive_results['TD']
        except(KeyError):
            td_count=0
        try:
            fg_count= drive_results['FG']
        except(KeyError):
            fg_count=0
            
        total_count= drive_results.sum()
        points= (td_count*7)+(fg_count*3)
        
        if points==0 or total_count==0:
            return 0
        else:
            return round(points/total_count,3)

    def get_turnover_rate(self,df):
        turnover_count=0
        play_results= df['play_type'].value_counts()
        for k,v in play_results.items():
            if k in ['Pass Interception','Fumble Recovery (Opponent)','Interception',
                     'Pass Interception Return','Interception Return Touchdown']:
                turnover_count+=v
                
        return round(turnover_count/play_results.sum(),3)
        
    
def main():
    for year in range(2014,2020):
        for week in range(1,16):
            plays= http.request('GET', 'https://api.collegefootballdata.com/plays?seasonType=regular&year='+str(year)+'&week='+str(week))
            plays_dict_list= json.loads(plays.data.decode('UTF-8'))
            drives=http.request('GET', 'https://api.collegefootballdata.com/drives?seasonType=regular&year='+str(year)+'&week='+str(week))
            drives_dict_list= json.loads(drives.data.decode('UTF-8'))
            Play(plays_dict_list,year,week)
            Drive(drives_dict_list,year,week)
            
    for year in range(2014,2020):
        games=http.request('GET','https://api.collegefootballdata.com/games?year='+str(year)+'&seasonType=regular')
        games_dict_list= json.loads(games.data.decode('UTF-8'))
        Game(games_dict_list)
        
        
main()


            
            
            
























            