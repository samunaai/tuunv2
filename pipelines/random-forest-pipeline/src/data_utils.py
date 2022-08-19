from nltk.corpus import stopwords 
from sklearn.model_selection import train_test_split

import numpy as np  
import pandas as pd
import re
  


#creating a function to encapsulate preprocessing, to mkae it easy to replicate on  submission data
def processing(df):
    
    #stopwords are filler words with little semantic content
    stopWords = set(stopwords.words('english'))
    
    
    #lowering and removing punctuation
    df['processed'] = df['text'].apply(lambda x: re.sub(r'[^\w\s]','', x.lower()))
    
    #numerical feature engineering
    #total length of sentence
    df['length'] = df['processed'].apply(lambda x: len(x))
    #get number of words
    df['words'] = df['processed'].apply(lambda x: len(x.split(' ')))
    df['words_not_stopword'] = df['processed'].apply(lambda x: len([t for t in x.split(' ') if t not in stopWords]))
    #get the average word length
    df['avg_word_length'] = df['processed'].apply(lambda x: np.mean([len(t) for t in x.split(' ') if t not in stopWords]) if len([len(t) for t in x.split(' ') if t not in stopWords]) > 0 else 0)
    #get the average word length
    df['commas'] = df['text'].apply(lambda x: x.count(','))

    return(df)



def get_train_test_split(data_dir, test_size):
    
    df = pd.read_csv(data_dir)
    df.dropna(axis=0)
    df.set_index('id', inplace = True) 
#     stopWords = set(stopwords.words('english'))
    df = processing(df)
    features= [c for c in df.columns.values if c  not in ['id','text','author']]
    numeric_features= [c for c in df.columns.values if c  not in ['id','text','author','processed']]
    target = 'author'
    X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=test_size, random_state=42)
    
    return X_train, X_test, y_train, y_test