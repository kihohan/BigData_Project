#!/usr/bin/env python
# coding: utf-8

# In[1]:


import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


# In[2]:


val = pd.read_csv('PJT002_validation.csv')
train = pd.read_csv('PJT002_train.csv')
test = pd.read_csv('PJT002_test.csv')

train_id = set (train['id'].unique())
val_id = set (val['id'].unique())
val.shape, train.shape, test.shape


# In[3]:


df = pd.concat([val,train,test])
df['fr_yn'] = df['fr_yn'].apply(lambda x: 0 if x == 'N' else 1 if x == 'Y' else -1)
df.shape


# In[4]:


def fillna_linear(data,time_column,column_name):
    data[time_column] = pd.to_datetime(data[time_column])
    data = data.sort_values(by = time_column)
    data[column_name] = data[column_name].interpolate(method = 'linear')

for column_name in ['tmprtr','prcpttn','wnd_spd','wnd_drctn','hmdt']:
    fillna_linear(df,'dt_of_fr',column_name)


# In[5]:


def drop_feature(data, column_name, drop_rate = 0.5):
    percent = data[column_name].isnull().sum() / len(data) 
    print ('{0}: {1}'.format(column_name,round(percent,2)))
    if percent >= drop_rate:
        del df[column_name]
        print ('---------->DELETE: {0}'.format(column_name))


# In[6]:


for i in df:
    drop_feature(df, i, drop_rate = 0.5)
print (df.shape)


# In[7]:


# str이 너무 다양하면 안맞음
def seperate_data_type(data,standard):
    binominal = []
    continuous = []
    for i in data.columns:
        if data[i].nunique() < standard:
            binominal.append(i)
        else:
            continuous.append(i)
    print ('binominal_data:', len(binominal), '개')
    print ('binominal_data:', binominal)
    print ('-------------------------------------------------------------------------------')
    #binominal_data = data[binominal]
    print ('continuous_data:', len(continuous), '개')
    print ('continuous_data:', continuous)
    #continuous_data = data[continuous]
    return binominal,continuous


# In[8]:


binominal_list,continuous_list = seperate_data_type(df,50)


# In[9]:


df_1 = df[binominal_list]


# In[10]:


def imputer_cate_most_frequent(data,column_name):
    data[column_name] = data[column_name].fillna(data[column_name].value_counts().index[0])


# In[11]:


for column_name in df_1:
    imputer_cate_most_frequent(df_1,column_name)


# In[12]:


def dummy_data(data, columns):
    for column in columns:
        data = pd.concat([data, pd.get_dummies(data[column], prefix = column)], axis=1)
        data = data.drop(column, axis=1)
    return data


# In[13]:


dummy_columns = list (set(binominal_list) - set(['fr_yn']))
df_1 = dummy_data(df_1, dummy_columns)


# In[14]:


df_2 = df[continuous_list]


# In[15]:


def imputer_cont_trim_mean(data,column_name):
    from scipy import stats
    try:
        data[column_name] = data[column_name].fillna(stats.trim_mean(data[column_name].dropna(), 0.2))
        data[column_name] = round(data[column_name],2)
    except:
        print ('not_changed ->',column_name)


# In[16]:


for column_name in df_2:
    imputer_cont_trim_mean(df_2,column_name)


# In[17]:


df_2['year'] = df_2['dt_of_fr'].dt.year 
df_2['month'] = df_2['dt_of_fr'].dt.month
df_2['day'] = df_2['dt_of_fr'].dt.day
df_2['hour'] = df_2['dt_of_fr'].dt.hour


# In[18]:


df_2 = df_2.drop(['dt_of_athrztn','dt_of_fr','emd_nm'],1)


# In[49]:


da = pd.concat([df_1,df_2],1)
da = da.reset_index(drop = True)
dt = da.copy()
dt.shape


# In[50]:


# 데이터 나누기
df_val = dt[dt['id'].isin(val_id)]
df_train = dt[dt['id'].isin(train_id)]
df_test = dt[dt['fr_yn'] == -1]
# 마무으리
df_test = df_test.drop(['fr_yn'],1)
df_val = df_val.drop('id',1)
df_train = df_train.drop('id',1)
df_test = df_test.drop('id',1)

df_val.shape, df_train.shape, df_test.shape


# In[51]:


X = df_train.drop('fr_yn',1)
Y = df_train[['fr_yn']]
val_X = df_val.drop('fr_yn',1)
val_Y = df_val[['fr_yn']]


# In[52]:


from sklearn.model_selection import *
from sklearn.metrics import *
Train_X,Test_X,Train_Y,Test_Y = train_test_split(X, Y, test_size = 0.2, random_state = 13)


# In[53]:


import lightgbm as lgb

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    lgb_model = lgb.LGBMClassifier(objective='binary', boosting_type='gbdt',learning_rate = 0.15, n_estimators = 60,
                                   max_bin = 225, metric='auc', num_leaves = 17,default = 'is_unbalance',
                                   random_state = 13)
    lgb_model.fit(Train_X, Train_Y,
                eval_set=[(Test_X, Test_Y)],
                verbose = False,
                early_stopping_rounds = 1000)
    predicted = lgb_model.predict(val_X)
    print ('val_set - precision: {0}'.format(precision_score(val_Y,predicted)))
    print ('val_set - recall: {0}'.format(recall_score(val_Y,predicted)))
    print ('val_set - fl: {0}'.format(f1_score(val_Y,predicted)))


# In[33]:


import xgboost as xgb

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    xgb_model = xgb.XGBClassifier(objective="binary:logistic", learning_rate = 0.15, max_depth = 5,
                                 max_delta_step = 7, max_bin = 512, eval_metric = 'poisson-nloglik',
                                 random_state = 13)
    xgb_model.fit(Train_X, Train_Y,
                eval_set=[(Test_X, Test_Y)],
                verbose = False,
                early_stopping_rounds = 1000)
    y_pred = xgb_model.predict(Test_X)
    predicted = [round(value) for value in y_pred]
    predicted = xgb_model.predict(val_X)
    print ('val_set - precision: {0}'.format(precision_score(val_Y,predicted)))
    print ('val_set - recall: {0}'.format(recall_score(val_Y,predicted)))
    print ('val_set - fl: {0}'.format(f1_score(val_Y,predicted)))


# In[24]:


from sklearn.ensemble import VotingClassifier 

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    vo_model = VotingClassifier(estimators = [('XGB', xgb_model),('LGBM', lgb_model)],
                              voting = 'soft')
    vo_model.fit(Train_X, Train_Y)
    predicted = vo_model.predict(val_X)
    print ('val_set - precision: {0}'.format(precision_score(val_Y,predicted)))
    print ('val_set - recall: {0}'.format(recall_score(val_Y,predicted)))
    print ('val_set - fl: {0}'.format(f1_score(val_Y,predicted)))


# In[60]:


def sub(model,test):
    predicted = model.predict(test)
    sub = pd.DataFrame({'fr_yn': predicted})
    sub['fr_yn'] = sub['fr_yn'].apply(lambda x: 'Y' if x == 1 else 'N')
    sub.to_csv('화재예측과제_Submission.csv', index = False)
    print (sub['fr_yn'].value_counts())


# In[62]:


sub(xgb_model,df_test)


# In[ ]:




