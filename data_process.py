#%%

#Realizado en Python 2.7.16

import pandas as pd
import numpy as np
import re

tsv_path = 'data/datos_data_engineer.tsv'

#Leemos el archivo

def read_file(path):
    data = pd.read_csv(tsv_path, sep='\t', encoding ='UTF-16LE')
    return data

#Suponiendo que un id tiene que ser numerico y ademas no puede tener logitud >4 
# y un account_id tiene que ser numerico y solo puede tener longitud = 6


def check_cols_values(value):
    regex_id = '^[0-9]{1,4}$'
    regex_first_last_name = '^[a-zA-Z]+$'
    regex_account_number = '^[0-9]{6}$'
    regex_email = '^\S+@\S+$'

    if bool(re.search(regex_id, value)):
        return 'id'
    elif bool(re.search(regex_first_last_name, value)):
        return 'first_name'
    elif bool(re.search(regex_account_number, value)):
        return 'account_number'
    elif bool(re.search(regex_email, value)):
        return 'email'
    else:
        return False


def sort_bad_values(df):
   
    for index, row in df[df.isnull().any(axis=1)].iterrows():
        values = {'id': row[0], 'first_name': row[1], 'last_name': row[2], 'account_number': row[3], 'email': row[4]}

        try:
            true_values = {}

            for k, v in values.items():
                if not pd.isnull(v):
                    result = check_cols_values(v)
                    if result != k:
                        true_values[result] = v
                        df.loc[index, k] = np.nan
                    else:
                        pass
            
            for k_,v_ in true_values.items():
                    df.loc[index, k_] = v_
        except:
            print('No se pudo procesar la fila')
        
    return df


def save_data(df):
    df.to_csv('data/datos_limpios.csv', encoding = 'utf-8', sep = '|')


if __name__ == "__main__":
    datos = read_file(tsv_path)
    sort_bad_values(datos)
    save_data(datos)

