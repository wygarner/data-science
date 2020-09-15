

import sqlite3
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from joblib import dump


conn= sqlite3.connect('NCAAF.db')

c= conn.cursor()

games_df= pd.read_sql_query('SELECT * FROM games',conn)


target_list= ['home_score','away_score']
features= list(games_df)

for i in ['game_id','week','year','home_team','away_team','home_offense_plays','away_offense_plays','home_score','away_score']:
    features.remove(i)

train, test = train_test_split(games_df.copy(), random_state=0)

predictions_dict= dict()

for target in target_list:
    error_list=[]
    
    model= MLPRegressor(hidden_layer_sizes=(100,100,100,100,100),activation='relu',solver='adam',alpha=0.0001,
                        batch_size='auto',learning_rate='constant',learning_rate_init=0.001,power_t=0.5,
                        max_iter=200,shuffle=True,random_state=None,tol=0.0001,verbose=False,warm_start=False,
                        momentum=0.9,nesterovs_momentum=True,early_stopping=True,validation_fraction=0.1,
                        beta_1=0.9,beta_2=0.999,epsilon=1e-08,n_iter_no_change=10)
    model.fit(train[features], train[target])
    y_true= train[target]
    y_pred = model.predict(train[features])
    train_error= mean_absolute_error(y_true,y_pred)
    x_true= test[target]
    x_pred= model.predict(test[features])
    test_error= mean_absolute_error(x_true,x_pred)
    error_list.append(train_error)
    error_list.append(test_error)
    
    predictions_dict['predicted_'+target]=x_pred.tolist()
    
    
    print('-----------------------------------------------------------------','\n')
    
    for i in error_list:
        print(i,'\n')
        if error_list.index(i)%2==1:
            print('------------------------','\n')
            
    if target=='home_score':            
        dump(model,'home_score_model.joblib')
    else:
        dump(model,'away_score_model.joblib')

predictions_df= pd.DataFrame.from_dict(predictions_dict)
test.reset_index(drop=True,inplace=True)
result= test.join(predictions_df,how='outer')
actual_results= result['home_score']-result['away_score']
predicted_results= result['predicted_home_score']-result['predicted_away_score']
margin_df= pd.concat([actual_results,predicted_results],axis=1)
actual_tf= margin_df[0]>0
predicted_tf= margin_df[1]>0
tf_df= pd.concat([actual_tf,predicted_tf],axis=1)
correct= len(tf_df[tf_df[0]==tf_df[1]])
accuracy= correct/len(tf_df)
print(accuracy,'\n')










            
            