from mido import MidiFile
import pandas as pd
import json

def get_value(string,attr):
    string = string.replace('<','').replace('>','')
    string = string.split(' ')
    a_list = []
    for i in string:
        if i.find(attr+'=') == -1:
            a_list.append('remove')
        else:
            a_list.append(int(i.replace(attr+'=','').replace(')', '').replace(',', '')))
    a_list = list(set(a_list))
    if len(a_list) == 1:
        return float('nan')
    else:
        a_list.remove('remove')
        return a_list[0]
           
    
            
def time_dur(d_start,d_end,df_tempo):
    
    '''
    d_start = 0
    d_end = 53978
    '''
    d_diff = d_end-d_start
    
    tempo_table = df_tempo[['DUR_START','DUR_END','TIME_FACTOR']]
    tempo_table = tempo_table.sort_values('DUR_START')
    tempo_table = tempo_table.reset_index(drop=True)
    
    tempo_table['Range'] = 0
    
    for r in range(0,len(tempo_table)):
        if d_start >= tempo_table['DUR_START'][r] and d_start < tempo_table['DUR_END'][r]:
            tempo_table['Range'][r] = 1
        else: 
            pass
    
        if d_end > tempo_table['DUR_START'][r] and d_end <= tempo_table['DUR_END'][r]:
            tempo_table['Range'][r] = 1
        else:
            pass

    ind_list = list(tempo_table.index[tempo_table['Range']==1])
    
    tempo_table = tempo_table[(tempo_table.index>=ind_list[0]) & (tempo_table.index<=ind_list[len(ind_list)-1])]
    tempo_table = tempo_table.reset_index(drop=True)
    
    if len(ind_list)>1:
        tempo_table['Head_Tail'] = tempo_table['DUR_END'] - tempo_table['DUR_START']
        tempo_table['Head_Tail'][0] = tempo_table['DUR_END'][0] - d_start
        tempo_table['Head_Tail'][len(tempo_table)-1] = d_end - tempo_table['DUR_START'][len(tempo_table)-1]
    else:
        tempo_table['Head_Tail'] = d_end - d_start
        
    tempo_table['Time'] = tempo_table['Head_Tail'] * tempo_table['TIME_FACTOR']
    
    return tempo_table['Time'].sum()/1000        


def export_midi(file):
    df_time = pd.DataFrame()
    f = file
    mid = MidiFile(f, clip=True)

    channel_num = len(mid.tracks) - 1

    a = []
    b = []
    c = []
    for x in range(0,len(mid.tracks)):
        for y in range(0,len(mid.tracks[x])):
            a.append(str(mid.tracks[x][y]))
            b.append(x)
            c.append(y)

    del mid,x,y

    df_mid = pd.DataFrame(data={'MESSAGE':a,'CHANNEL':b,'ORDER':c})
    del a,b,c

    df_tempo = df_mid[df_mid['CHANNEL']==0]
    df_midi = df_mid[df_mid['CHANNEL']!=0]
    del df_mid
    ##########################################################################

    df_midi['NOTE'] = df_midi['MESSAGE'].apply(lambda x: get_value(x,'note'))
    df_midi['DUR_START'] = df_midi['MESSAGE'].apply(lambda x: get_value(x,'time'))
    df_midi['VELOCITY'] = df_midi['MESSAGE'].apply(lambda x: get_value(x,'velocity'))
    df_midi = df_midi.sort_values(['CHANNEL','ORDER']).reset_index(drop=True)

    for i in range(1,len(df_midi)):
        if df_midi['CHANNEL'][i] > df_midi['CHANNEL'][i-1]:
            pass
        else:
            df_midi['DUR_START'][i] = df_midi['DUR_START'][i-1] + df_midi['DUR_START'][i]    
    del i

    df_midi = df_midi[pd.notna(df_midi['NOTE'])]
    df_midi = df_midi[pd.notna(df_midi['VELOCITY'])]
    df_midi = df_midi.sort_values(['CHANNEL','ORDER']).reset_index(drop=True)

    df_midi['NOTE'][df_midi['VELOCITY']==0] = float('nan') 


    df_midi = df_midi.drop(columns='MESSAGE')
    df_midi = df_midi.groupby(['CHANNEL','DUR_START']).agg({'ORDER':'max','VELOCITY':'mean','NOTE':lambda x: list(x)}).reset_index(level=['CHANNEL','DUR_START'])


    df_midi['DUR_END'] = df_midi['DUR_START'].shift(-1)



    for c in range(0,channel_num):
        max_order = df_midi['ORDER'][df_midi['CHANNEL']==c+1].max()
        df_midi['DUR_END'][(df_midi['ORDER']==max_order) & (df_midi['CHANNEL']==c+1)] = float('nan')
    del c, max_order,channel_num

    df_midi = df_midi.dropna()
    df_midi = df_midi[df_midi['VELOCITY']!=0]
    df_midi = df_midi[['CHANNEL','ORDER','NOTE','DUR_START','DUR_END']]

    df_midi['NOTE'] = df_midi['NOTE'].apply(lambda x: [int(y) for y in x if str(y) != 'nan'])
    df_midi = df_midi.reset_index(drop=True)
    for i in range(0,len(df_midi)):
        df_midi['NOTE'][i].sort()
    del i

    # df_midi['D'] = df_midi['DUR_START'] -  df_midi['DUR_END'].shift(1)

    ##########################################################################



    df_tempo['TEMPO'] = df_tempo['MESSAGE'].apply(lambda x: get_value(x,'tempo'))
    df_tempo['DUR_START'] = df_tempo['MESSAGE'].apply(lambda x: get_value(x,'time'))
    df_tempo = df_tempo.sort_values('ORDER').reset_index(drop=True)

    for i in range(1,len(df_tempo)):
        df_tempo['DUR_START'][i] = df_tempo['DUR_START'][i-1] + df_tempo['DUR_START'][i]
    df_tempo = df_tempo.dropna()
    del i

    df_tempo['DUR_END'] = df_tempo['DUR_START'].shift(-1)
    df_tempo = df_tempo.drop_duplicates(subset='DUR_START',keep='last')

    df_tempo['DUR_END'] = df_tempo['DUR_END'].fillna(df_midi['DUR_END'].max())

    df_tempo['TIME_FACTOR'] = df_tempo['TEMPO'] /192



    ##########################################################################


    df_midi['TIME_START'] = df_midi['DUR_START'].apply(lambda x: time_dur(0,x,df_tempo.copy()))
    df_midi['TIME_END'] = df_midi['DUR_END'].apply(lambda x: time_dur(0,x,df_tempo.copy()))

    del df_tempo

    df_midi['SONG'] = f.replace('.mid','')
    df_time = df_time.append(df_midi)
    print(len(df_midi))
    return df_midi.to_json(orient='records')


