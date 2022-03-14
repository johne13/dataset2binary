'''
file:  create_test_data.py

description:  creates small datasets (dataframes) with 
              a mix of character, integer, and floats.  
              outputs csv and dta (stata) files.
'''

import pandas as pd
import numpy as np

df = pd.DataFrame( { 's1':list('abcdef') } )
df['s2'] = df.s1 * 2
df['s3'] = df.s2 * 2
df['s4'] = df.s3 * 2

arr = np.arange( 84 ).reshape([6,14])
arr = arr + arr / 10.

df2 = pd.DataFrame( arr, columns=['i' + str(i) for i in range(1, 5) ] + 
                                 ['f' + str(f) for f in range(1,11) ] ) 

for v in ['i1','i2']: df2[v] = df2[v].astype(np.int32)
for v in ['i3','i4']: df2[v] = df2[v].astype(np.int64)
for v in ['f1','f2']: df2[v] = df2[v].astype(np.float32)

df = pd.concat( [ df, df2 ], axis=1 )

df.to_csv('test.csv',index=False)
df.to_stata('test.dta')

print(df.mean())


