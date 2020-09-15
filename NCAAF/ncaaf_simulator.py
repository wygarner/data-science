

import sqlite3
import pandas as pd
import math
from joblib import load
import json
import urllib3
import certifi
import sys


http= urllib3.PoolManager(cert_reqs= 'CERT_REQUIRED', ca_certs= certifi.where())

conn= sqlite3.connect('NCAAF.db')

c= conn.cursor()

games_df= pd.read_sql_query('SELECT * FROM games',conn)
# all_plays_df= pd.read_sql_query('SELECT * FROM plays',conn)
ratings_df= pd.read_sql_query('SELECT * FROM ratings',conn)

home_score_model= load('home_score_model.joblib')
away_score_model= load('away_score_model.joblib')

features= ['home_ypp', 'home_success_rate', 'home_ppapsp', 'home_afp', 'home_ppti40', 
            'home_turnovers', 'away_ypp', 'away_success_rate', 'away_ppapsp', 'away_afp', 
            'away_ppti40', 'away_turnovers']


def get_success_rate_ppapsp(df):     
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

    return round(successful_plays_total/total_plays,3),round(total_ppapsp/total_plays,3)

def get_ppti40(df):
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

def get_turnover_rate(df):
    turnover_count=0
    play_results= df['play_type'].value_counts()
    for k,v in play_results.items():
        if k in ['Pass Interception','Fumble Recovery (Opponent)','Interception',
                 'Pass Interception Return','Interception Return Touchdown']:
            turnover_count+=v
            
    return round(turnover_count/play_results.sum(),3)


for index,row in games_df.iterrows():
    print(row,'\n')
    try:
        if row['week']==1:
            home_offense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.offense_team=? AND plays.year=? AND plays.week<?',
                                                 conn,params=[row['home_team'],row['year']-1,16])
            home_defense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.defense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['home_team'],row['year']-1,16])
            away_offense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.offense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['away_team'],row['year']-1,16])
            away_defense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.defense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['away_team'],row['year']-1,16])
            
            home_offense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.offense_team=? AND drives.year=? AND drives.week<?',
                                                 conn,params=[row['home_team'],row['year']-1,16])
            home_defense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.defense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['home_team'],row['year']-1,16])
            away_offense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.offense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['away_team'],row['year']-1,16])
            away_defense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.defense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['away_team'],row['year']-1,16])
            
            home_ratings= pd.read_sql_query('SELECT * FROM ratings WHERE ratings.team=? AND ratings.year=? AND ratings.week=?',
                                                     conn,params=[row['home_team'],row['year'],row['week']])
            away_ratings= pd.read_sql_query('SELECT * FROM ratings WHERE ratings.team=? AND ratings.year=? AND ratings.week=?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
            
            home_offense_rating= math.log10(math.log10(home_ratings['offense']/100)+1)+1
            home_defense_rating= math.log10(math.log10(home_ratings['defense']/100)+1)+1
            
            away_offense_rating= math.log10(math.log10(away_ratings['offense']/100)+1)+1
            away_defense_rating= math.log10(math.log10(away_ratings['defense']/100)+1)+1
            
            home_wins=0
            away_wins=0
            home_score_list=[]
            away_score_list=[]
            
            for i in range(0,1001):
                home_offense_plays_sample= home_offense_plays.sample(n=75)
                home_defense_plays_sample= home_defense_plays.sample(n=75)
                away_offense_plays_sample= away_offense_plays.sample(n=75)
                away_defense_plays_sample= away_defense_plays.sample(n=75)
                
                home_offense_drives_sample= home_offense_drives.sample(n=75)
                home_defense_drives_sample= home_defense_drives.sample(n=75)
                away_offense_drives_sample= away_offense_drives.sample(n=75)
                away_defense_drives_sample= away_defense_drives.sample(n=75)
                
                home_offense_ypp= round(home_offense_plays_sample['yards_gained'].sum()/len(home_offense_plays_sample),3)*home_offense_rating
                home_defense_ypp= round(home_defense_plays_sample['yards_gained'].sum()/len(home_defense_plays_sample),3)*home_defense_rating
                away_offense_ypp= round(away_offense_plays_sample['yards_gained'].sum()/len(away_offense_plays_sample),3)*away_offense_rating
                away_defense_ypp= round(away_defense_plays_sample['yards_gained'].sum()/len(away_defense_plays_sample),3)*away_defense_rating
                
                home_offense_success_rate_ppapsp= get_success_rate_ppapsp(home_offense_plays_sample)
                home_defense_success_rate_ppapsp= get_success_rate_ppapsp(home_defense_plays_sample)
                away_offense_success_rate_ppapsp= get_success_rate_ppapsp(away_offense_plays_sample)
                away_defense_success_rate_ppapsp= get_success_rate_ppapsp(away_defense_plays_sample)
        
                home_offense_afp= round(home_offense_drives_sample['drive_start'].sum()/len(home_offense_drives_sample),3)*home_offense_rating
                home_defense_afp= round(home_defense_drives_sample['drive_start'].sum()/len(home_defense_drives_sample),3)*home_defense_rating
                away_offense_afp= round(away_offense_drives_sample['drive_start'].sum()/len(away_offense_drives_sample),3)*away_offense_rating
                away_defense_afp= round(away_defense_drives_sample['drive_start'].sum()/len(away_defense_drives_sample),3)*away_defense_rating
                
                home_offense_ppti40= get_ppti40(home_offense_drives_sample)*home_offense_rating
                home_defense_ppti40= get_ppti40(home_defense_drives_sample)*home_defense_rating
                away_offense_ppti40= get_ppti40(away_offense_drives_sample)*away_offense_rating
                away_defense_ppti40= get_ppti40(away_defense_drives_sample)*away_defense_rating
                
                home_offense_turnovers= get_turnover_rate(home_offense_plays_sample)*home_offense_rating
                home_defense_turnovers= get_turnover_rate(home_defense_plays_sample)*home_defense_rating
                away_offense_turnovers= get_turnover_rate(away_offense_plays_sample)*away_offense_rating
                away_defense_turnovers= get_turnover_rate(away_defense_plays_sample)*away_defense_rating
                
                home_ypp= (home_offense_ypp+away_defense_ypp)/2
                home_success_rate= ((home_offense_success_rate_ppapsp[0]*home_offense_rating)+(away_defense_success_rate_ppapsp[0]*away_defense_rating))/2
                home_ppapsp= ((home_offense_success_rate_ppapsp[1]*home_offense_rating)+(away_defense_success_rate_ppapsp[1]*away_defense_rating))/2
                home_afp= (home_offense_afp+away_defense_afp)/2
                home_ppti40= (home_offense_ppti40+away_defense_ppti40)/2
                home_turnovers= (home_offense_turnovers+away_defense_turnovers)/2
                
                away_ypp= (away_offense_ypp+home_defense_ypp)/2
                away_success_rate= ((away_offense_success_rate_ppapsp[0]*away_offense_rating)+(home_defense_success_rate_ppapsp[0]*home_defense_rating))/2
                away_ppapsp= ((away_offense_success_rate_ppapsp[1]*away_offense_rating)+(home_defense_success_rate_ppapsp[1]*home_defense_rating))/2
                away_afp= (away_offense_afp+home_defense_afp)/2
                away_ppti40= (away_offense_ppti40+home_defense_ppti40)/2
                away_turnovers= (away_offense_turnovers+home_defense_turnovers)/2
                
                game_d= dict()
                game_d[features[0]]= home_ypp
                game_d[features[1]]= home_success_rate
                game_d[features[2]]= home_ppapsp
                game_d[features[3]]= home_afp
                game_d[features[4]]= home_ppti40
                game_d[features[5]]= home_turnovers
                game_d[features[6]]= away_ypp
                game_d[features[7]]= away_success_rate
                game_d[features[8]]= away_ppapsp
                game_d[features[9]]= away_afp
                game_d[features[10]]= away_ppti40
                game_d[features[11]]= away_turnovers
                
                game_df= pd.DataFrame(data= game_d,index=[0])
                
                home_score= round(home_score_model.predict(game_df).tolist()[0],3)
                away_score= round(away_score_model.predict(game_df).tolist()[0],3)
                
                print(home_score,' - ',away_score,'\n')
                
                if home_score>away_score:
                    home_wins+=1
                else:
                    away_wins+=1
                    
                home_score_list.append(home_score)
                away_score_list.append(away_score)
                    
            home_win_rate= round(home_wins/1000,3)
            away_win_rate= round(away_wins/1000,3)
            average_home_score= round(sum(home_score_list)/len(home_score_list),3)
            average_away_score= round(sum(away_score_list)/len(away_score_list),3)
            
            lines=http.request('GET','https://api.collegefootballdata.com/lines?year='+str(row['year'])+'&seasonType=regular&home='+row['home_team']+'&away='+row['away_team'])
            lines_dict_list= json.loads(lines.data.decode('UTF-8'))
            
            spread= ''
            over_under=''
            try:
                for elem in lines_dict_list[0]['lines']:
                    if type(elem['formattedSpread'])!='NoneType':
                        spread= elem['formattedSpread']
                    if type(elem['overUnder'])!='NoneType':
                        over_under= elem['overUnder']
            except(IndexError):
                print('No line')
            
            print(home_win_rate,'\n')
            print(away_win_rate,'\n')
            print(average_home_score,' - ',average_away_score,'\n')
            
            c.execute("INSERT INTO predictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(row['game_id'],row['year'],row['week'],
                        row['home_team'],row['away_team'],home_win_rate,away_win_rate,average_home_score,
                        average_away_score,row['home_score'],row['away_score'],spread,over_under))
            conn.commit()   
            
        else:
            home_offense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.offense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['home_team'],row['year'],row['week']])
            home_defense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.defense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['home_team'],row['year'],row['week']]) 
            away_offense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.offense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
            away_defense_plays= pd.read_sql_query('SELECT * FROM plays WHERE plays.defense_team=? AND plays.year=? AND plays.week<?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
            
            home_offense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.offense_team=? AND drives.year=? AND drives.week<?',
                                                 conn,params=[row['home_team'],row['year'],row['week']])
            home_defense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.defense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['home_team'],row['year'],row['week']])
            away_offense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.offense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
            away_defense_drives= pd.read_sql_query('SELECT * FROM drives WHERE drives.defense_team=? AND drives.year=? AND drives.week<?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
           
            home_ratings= pd.read_sql_query('SELECT * FROM ratings WHERE ratings.team=? AND ratings.year=? AND ratings.week=?',
                                                     conn,params=[row['home_team'],row['year'],row['week']])
            away_ratings= pd.read_sql_query('SELECT * FROM ratings WHERE ratings.team=? AND ratings.year=? AND ratings.week=?',
                                                     conn,params=[row['away_team'],row['year'],row['week']])
        
            home_offense_rating= math.log10(math.log10(home_ratings['offense']/100)+1)+1
            home_defense_rating= math.log10(math.log10(home_ratings['defense']/100)+1)+1
            
            away_offense_rating= math.log10(math.log10(away_ratings['offense']/100)+1)+1
            away_defense_rating= math.log10(math.log10(away_ratings['defense']/100)+1)+1
            
            home_wins=0
            away_wins=0
            home_score_list=[]
            away_score_list=[]
            
            for i in range(0,1001):
                if row['week']==2:
                    home_offense_plays_sample= home_offense_plays.sample(n=30)
                    home_defense_plays_sample= home_defense_plays.sample(n=30)
                    away_offense_plays_sample= away_offense_plays.sample(n=30)
                    away_defense_plays_sample= away_defense_plays.sample(n=30)
                    
                    home_offense_drives_sample= home_offense_drives.sample(n=30)
                    home_defense_drives_sample= home_defense_drives.sample(n=30)
                    away_offense_drives_sample= away_offense_drives.sample(n=30)
                    away_defense_drives_sample= away_defense_drives.sample(n=30)
                else:
                    home_offense_plays_sample= home_offense_plays.sample(n=75)
                    home_defense_plays_sample= home_defense_plays.sample(n=75)
                    away_offense_plays_sample= away_offense_plays.sample(n=75)
                    away_defense_plays_sample= away_defense_plays.sample(n=75)
                    
                    home_offense_drives_sample= home_offense_drives.sample(n=75)
                    home_defense_drives_sample= home_defense_drives.sample(n=75)
                    away_offense_drives_sample= away_offense_drives.sample(n=75)
                    away_defense_drives_sample= away_defense_drives.sample(n=75)
                
                home_offense_ypp= round(home_offense_plays_sample['yards_gained'].sum()/len(home_offense_plays_sample),3)*home_offense_rating
                home_defense_ypp= round(home_defense_plays_sample['yards_gained'].sum()/len(home_defense_plays_sample),3)*home_defense_rating
                away_offense_ypp= round(away_offense_plays_sample['yards_gained'].sum()/len(away_offense_plays_sample),3)*away_offense_rating
                away_defense_ypp= round(away_defense_plays_sample['yards_gained'].sum()/len(away_defense_plays_sample),3)*away_defense_rating
                
                home_offense_success_rate_ppapsp= get_success_rate_ppapsp(home_offense_plays_sample)
                home_defense_success_rate_ppapsp= get_success_rate_ppapsp(home_defense_plays_sample)
                away_offense_success_rate_ppapsp= get_success_rate_ppapsp(away_offense_plays_sample)
                away_defense_success_rate_ppapsp= get_success_rate_ppapsp(away_defense_plays_sample)
        
                home_offense_afp= round(home_offense_drives_sample['drive_start'].sum()/len(home_offense_drives_sample),3)*home_offense_rating
                home_defense_afp= round(home_defense_drives_sample['drive_start'].sum()/len(home_defense_drives_sample),3)*home_defense_rating
                away_offense_afp= round(away_offense_drives_sample['drive_start'].sum()/len(away_offense_drives_sample),3)*away_offense_rating
                away_defense_afp= round(away_defense_drives_sample['drive_start'].sum()/len(away_defense_drives_sample),3)*away_defense_rating
                
                home_offense_ppti40= get_ppti40(home_offense_drives_sample)*home_offense_rating
                home_defense_ppti40= get_ppti40(home_defense_drives_sample)*home_defense_rating
                away_offense_ppti40= get_ppti40(away_offense_drives_sample)*away_offense_rating
                away_defense_ppti40= get_ppti40(away_defense_drives_sample)*away_defense_rating
                
                home_offense_turnovers= get_turnover_rate(home_offense_plays_sample)*home_offense_rating
                home_defense_turnovers= get_turnover_rate(home_defense_plays_sample)*home_defense_rating
                away_offense_turnovers= get_turnover_rate(away_offense_plays_sample)*away_offense_rating
                away_defense_turnovers= get_turnover_rate(away_defense_plays_sample)*away_defense_rating
                
                home_ypp= (home_offense_ypp+away_defense_ypp)/2
                home_success_rate= ((home_offense_success_rate_ppapsp[0]*home_offense_rating)+(away_defense_success_rate_ppapsp[0]*away_defense_rating))/2
                home_ppapsp= ((home_offense_success_rate_ppapsp[1]*home_offense_rating)+(away_defense_success_rate_ppapsp[1]*away_defense_rating))/2
                home_afp= (home_offense_afp+away_defense_afp)/2
                home_ppti40= (home_offense_ppti40+away_defense_ppti40)/2
                home_turnovers= (home_offense_turnovers+away_defense_turnovers)/2
                
                away_ypp= (away_offense_ypp+home_defense_ypp)/2
                away_success_rate= ((away_offense_success_rate_ppapsp[0]*away_offense_rating)+(home_defense_success_rate_ppapsp[0]*home_defense_rating))/2
                away_ppapsp= ((away_offense_success_rate_ppapsp[1]*away_offense_rating)+(home_defense_success_rate_ppapsp[1]*home_defense_rating))/2
                away_afp= (away_offense_afp+home_defense_afp)/2
                away_ppti40= (away_offense_ppti40+home_defense_ppti40)/2
                away_turnovers= (away_offense_turnovers+home_defense_turnovers)/2
                
                game_d= dict()
                game_d[features[0]]= home_ypp
                game_d[features[1]]= home_success_rate
                game_d[features[2]]= home_ppapsp
                game_d[features[3]]= home_afp
                game_d[features[4]]= home_ppti40
                game_d[features[5]]= home_turnovers
                game_d[features[6]]= away_ypp
                game_d[features[7]]= away_success_rate
                game_d[features[8]]= away_ppapsp
                game_d[features[9]]= away_afp
                game_d[features[10]]= away_ppti40
                game_d[features[11]]= away_turnovers
                
                game_df= pd.DataFrame(data= game_d,index=[0])
                
                home_score= round(home_score_model.predict(game_df).tolist()[0],3)
                away_score= round(away_score_model.predict(game_df).tolist()[0],3)
                
                print(home_score,' - ',away_score,'\n')
                
                if home_score>away_score:
                    home_wins+=1
                else:
                    away_wins+=1
                    
                home_score_list.append(home_score)
                away_score_list.append(away_score)
                    
            home_win_rate= round(home_wins/1000,3)
            away_win_rate= round(away_wins/1000,3)
            average_home_score= round(sum(home_score_list)/len(home_score_list),3)
            average_away_score= round(sum(away_score_list)/len(away_score_list),3)
            
            lines=http.request('GET','https://api.collegefootballdata.com/lines?year='+str(row['year'])+'&seasonType=regular&home='+row['home_team']+'&away='+row['away_team'])
            lines_dict_list= json.loads(lines.data.decode('UTF-8'))
            
            spread= ''
            over_under=''
            try:
                for elem in lines_dict_list[0]['lines']:
                    if type(elem['formattedSpread'])!='NoneType':
                        spread= elem['formattedSpread']
                    if type(elem['overUnder'])!='NoneType':
                        over_under= elem['overUnder']
            except(IndexError):
                print('No line')
            
            print(home_win_rate,'\n')
            print(away_win_rate,'\n')
            print(average_home_score,' - ',average_away_score,'\n')
            
            c.execute("INSERT INTO predictions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(row['game_id'],row['year'],row['week'],
                        row['home_team'],row['away_team'],home_win_rate,away_win_rate,average_home_score,
                        average_away_score,row['home_score'],row['away_score'],spread,over_under))
            conn.commit()
    except(TypeError):
        print('No data')

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    