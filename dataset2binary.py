'''
file: dataset2binary.py 

description: converts a dataset (aka dataframe) to a binary data file, and
             alse creates c and fortran code for reading the binary data

input: data in sas, stata, or csv format.  may include a mix of character,
       integer, and float data, in multiple sizes.

output: (1) binary file readable by c or fortran
        (2) c code to read the binary file
        (3) fortran code to read the binary file
        (4) list of columns & formats/dtypes
'''

import sys
import pandas as pd
import numpy as np

if len(sys.argv) == 1:
   print( '-' * 70 + '\n' )
   print( 'Description of dataset2binary:\n')
   print( '   -> reads a stata/sas dataset or a CSV')
   print( '   -> outputs')
   print( '         1 c/fortran readable binary dataset')
   print( '         2 fortran program to read the data and output means')
   print( '         3 c program to read the data and output means')
   print( '         4 format file that can (optionally) be altered ')
   print( '           to specify data types (int8,float16,etc.)\n')
   print( 'Syntax for ds2bin:\n')
   print( '   $ ds2bin filename.ext [ downcast | f=file ]\n')
   print( '   -> filename may include path')
   print( "   -> extension must be 'sas7bdat' (sas), 'dta' (stata), or 'csv'")
   print( "   -> downcast option will attempt to safely cast numerical columns")
   print( "      into smaller dtypes (including float -> integer)")
   print( "   -> f=file is for providing desired number formats")
   print( "      (see the /tmp/file output for syntax\n")
   print( '-' * 70 + '\n' )
   sys.exit() 

# function for automatic downcasting of float to int (but only if it doesn't lead to loss of precision)

def float_to_int( s ):
    if np.issubdtype( s, np.number ):
        if ( s.astype(np.int64) == s ).all():
            return pd.to_numeric( s, downcast='integer' )
        else:
            return s
    else:
        return s

downcast=False
user_formats=False
if len(sys.argv) == 3: 
    if sys.argv[2] == 'downcast':  downcast=True

    if sys.argv[2][:2] == 'f=':
        user_formats=True
        fmt_file = sys.argv[2].partition('=')[2] 
        fmts_in = pd.read_csv(fmt_file, delim_whitespace=True, header=None )

# process the required argument -- filename + extension 
fullname = sys.argv[1]
dataset_name, sep, dataset_type = fullname.partition('.')
if dataset_type == '':  raise Exception("\n\n *** Input dataset must have extension 'sas7bdat', 'dta', or 'csv' ***\n")

path, sep, dataset_name = dataset_name.rpartition('/')

output_bin   = dataset_name + '.bin'
output_f90   = dataset_name + '.f90'
output_c     = dataset_name + '.c'
formats_file = dataset_name + '.formats'

# can i add some sort of hourglass sort of thingy here???
if dataset_type in ['sas7bdat', 'dta', 'csv']: print( '\n' + 80 * '-' + '\nReading ' + sys.argv[1] + '. . . \n' )

if   dataset_type == 'sas7bdat':  df = pd.read_sas(   fullname ) 
elif dataset_type == 'dta':       df = pd.read_stata( fullname ) 
elif dataset_type == 'csv':       df = pd.read_csv(   fullname ) 
else:
    raise Exception("\n\n *** Input dataset must have extension 'sas7bdat', 'dta', or 'csv' ***\n")

# optionally downcast or apply the user-specified formats
if downcast==True:  
    df = df.apply(float_to_int)

if user_formats:
    for col, fmt in zip( fmts_in[0], fmts_in[1] ):
        # apply user formats/dtypes, but only if lossless for integers
        if fmt[:3] != 'int' or ( df[col] == df[col].astype(fmt) ).all(): 
            df[col] = df[col].astype(fmt)
        else:
            print( '***** Column ' + col + ' not downcast to ' + fmt +  ' b/c data values are too large *****\n' )

# output pandas dtypes to formats file 'fmts_out'
fmts_out = open(formats_file,'w')
for col in df.columns:
    fmts_out.write( f'{col: <30}' + str(df[col].dtype) + '\n' ) 
fmts_out.close()

# process any additional arguments 
# for arg in sys.argv[2:]

# output files 'f' & 'c' with variable declarations, to be used in fortran/c binary reads
f    = open(output_f90,'w')
f.write( 'program main\n\n' )
f.write( '   type foo' )

c    = open(output_c,'w')
c.write( '#include <stdio.h>\n' )
c.write( '#include <ctype.h>\n\n' )
c.write( 'int main() {\n\n' )
c.write( '    FILE *fp;\n\n' )
c.write( '    #pragma pack(push,1)\n' )
c.write( '    struct foobar {\n' )

print('\nFirst 5 rows of dataset:\n\n',df.head(5))

# i think we want to convert any missing values ('.') to zeroes or else fortran will sum as NaN?
df = df.fillna(0)

names = df.columns

arrays = [ df[col].values for col in names ]

formats = [ array.dtype.str if array.dtype != 'O' 
            else array.astype(str).dtype.str.replace('<U','S') for array in arrays ] 

#formats = [ array.dtype if array.dtype != 'O' else '%s' % array.astype(str).dtype for array in arrays ] 
#formats = [ array.dtype if array.dtype != 'O' else f'{array.astype(str).dtype}' for array in arrays ] 

rec_array = np.rec.fromarrays( arrays, dtype={'names': names, 'formats': formats} )
rec_array.tofile(output_bin)

# numpy dtype notes:  can have the following prefix characters, but may not be present at all
# source:  https://docs.scipy.org/doc/numpy-1.15.1/reference/generated/numpy.dtype.html
# =   native
# <   little-endian
# >   big-endian
# |   not applicable

indent = 6 * ' ' 
prev_fmt = ''
count = 1
numerical_cols = []
first_column = True

for fmt, col in zip( formats, names ):

    if fmt == prev_fmt and count < 8:

        pre    = ', '
        pre_c  = ', '

        count += 1

    else:

        # try to figure out the formats in this way:
        # if first or second character is "i" then it is an integer
        # e.g. 'i', '<i', and '|i' are all integers (similar for floats and characters)

        post_c = ''

        # debugging print
        if False:
            print('i formats',fmt,fmt[:2],fmt.partition('i')[-1])
            print('f formats',fmt,fmt[:2],fmt.partition('f')[-1])
            print('S formats',fmt,fmt[:2],fmt.partition('S')[-1],'\n')
      
        if   'i' in fmt[:2]:  pre = '\n' + indent + 'integer*'   + fmt.partition('i')[-1] +  ' :: '
        elif 'f' in fmt[:2]:  pre = '\n' + indent + 'real*'      + fmt.partition('f')[-1] +  ' :: ' 
        elif 'S' in fmt[:2]:  pre = '\n' + indent + 'character(' + fmt.partition('S')[-1] + ') :: '
        else:                 raise Exception('Unknown format: ',fmt)
      
        if 'i' in fmt[:2]:  
            if   fmt.partition('i')[-1] == '4':  pre_c = indent + 'int '
            elif fmt.partition('i')[-1] == '8':  pre_c = indent + 'long '
            else:                                raise Exception('Unknown format: ',fmt)
        elif 'f' in fmt[:2]:  
            if   fmt.partition('f')[-1] == '4':  pre_c = indent + 'float '
            elif fmt.partition('f')[-1] == '8':  pre_c = indent + 'double '
            else:                                raise Exception('Unknown format: ',fmt)
        elif 'S' in fmt[:2]:  
            pre_c  = indent + 'char ' 
            post_c = '[' + fmt.partition('S')[-1] + ']'
        else:    
            raise Exception('Unknown format: ',fmt)

        count = 1

        if first_column: 
            pre_c = '\n' + pre_c
            first_column = False
        else:          
            pre_c = ' ;\n' + pre_c

    if 'i' in fmt[:2] or 'f' in fmt[:2]: numerical_cols += [col] 

    if count <  9:  
        f.write(pre   + col          )
        c.write(pre_c + col + post_c )
    else: 
        f.write(pre   + col +          '\n')
        f.write(pre_c + col + post_c + '\n')

    prev_fmt = fmt

rows = str(len(df))

# write out the rest of the fortran code

f.write('\n   end type foo\n')
f.write('\n   type(foo) :: foo_in\n') 
f.write('\n   real(8) :: means(' + str(len(numerical_cols)) + ')\n\n')
f.write("   open( 13, file='" + output_bin + "', form='unformatted', access='stream' )\n\n" )
f.write('   do i = 1, ' + rows + '\n')
f.write('\n      read(13) foo_in\n\n')
for i, col in enumerate(numerical_cols):
    f.write('      means(' + str(i+1) + ') = means(' + str(i+1) + ') + foo_in%' + col + '\n') 
f.write('\n      !!! if( i < 6 ) print *, foo_in\n')
f.write('\n   end do\n')
f.write('\n   print *, new_line("a"), "   numerical columns                   means ", new_line("a")\n\n')
for i, col in enumerate(numerical_cols):
    f.write("   print '(a20,f24.5)', '" + col + "',  means(" + str(i+1) + ") / " + rows + "\n") 
f.write('\nend program main\n' )

# write out the rest of the c code

c.write( ';\n\n' )
c.write( '    } foo ;\n' )
c.write( '    #pragma pack(pop)\n\n' )
c.write( '    fp = fopen( "' + output_bin + '", "rb"); \n')
c.write( '    if (fp == NULL) { \n')
c.write( '        puts("Cannot open the file."); \n')
c.write( '        return 1; \n')
c.write( '    }\n\n' )
c.write( '    int i_counter = 1 ; \n')
c.write( '    double means[' + str(len(numerical_cols)) + '] = { 0. } ; \n\n')
c.write( '    while (fread(&foo, sizeof(foo), 1, fp) == 1) { \n')
for i, col in enumerate(numerical_cols):
    c.write('        means[' + str(i) + '] += ' + 'foo.' + col + ' ;\n') 
c.write( '        i_counter ++ ; \n' )
c.write( '    }\n' )
c.write('\n    printf( "%cmeans of numerical columns %c %c", 10, 10, 10 );\n')
for i, col in enumerate(numerical_cols):
    c.write('    printf( " ' + col + ' %f %c", means[' + str(i) + '] / ' + rows + '., 10 ) ;\n') 
c.write( '    printf("%c",10) ;\n' )
c.write( '\n    fclose(fp); \n')
c.write( '    return 0; \n\n')
c.write( '    }\n' )

# close all the files
f.close()
c.close()

print( '\nConversion completed' )
print( '\nInput  = ' + fullname )
print( '\nOutput = ' + output_bin + '     (binary data)'  )
print(   '         ' + output_f90 + '     (fortran code)' )
print(   '         ' + output_c + '       (c code)'       )
print(   '         ' + formats_file +   ' (formats)\n'    )

