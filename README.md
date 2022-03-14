# dataset2binary
Convert a dataset/dataframe (CSV/sas/stata) into a binary data file and create c/fortran code to read it

## Getting started
Just download, copy, or clone dataset2binary.py.  Requires numpy & pandas.  Tested with numpy 1.20.1 and pandas 1.2.4 but should work with any recent versions. A help screen is produced when dataset2binary is run without any arguments.

## Expected use case
* If you need to read a somewhat large dataset with mixed (char/int/float) types into c or fortran, this automates most of the work by both converting the data itself and providing the c and fortran code to read the data.  This can save a lot of coding time and also will be faster than reading CSV/ascii data.
* If your data is all of one type (e.g. all 8 byte floats) then this program will still work fine, but you'll likely get a faster read time by just reading in a simple array rather than doing it via structure/derived type as dataset2binary will do.

## Testing notes
* There are no automated tests at this time.  See create_test_data.py for a small python program that creates a small CSV and stata (dta) that you can test on your system.
* The most recent tests of dataset2binary were performed with gcc/gfortran version 10.2.1 on a red hat linux system.  The c/fortran code is pretty simple, so it is likely to work with most versions of gcc/gfortran (both new and old).
* The fortran version of the code has been used for production work with no known issues.  The c version has not been tested as extensively.

## Known issues
* The c code reads in character data without a newline.  As such the code will compile and run, but you'd probably need to add a newline manually if you want to do anything useful with the character variables.
* The c code has been tested with 4 & 8 byte integers.  I am not sure if it will work with 1 or 2 byte integers from SAS or Stata.  If necessary you can specify integers to be 4 or 8 bytes in the format file. A more automated solution could be considered in the future.
* Not an issue, but dataset2binary will default to 8 bytes for integers & reals, whereas it will stay in a more compact form if you have a compressed Stata dataset, for example.  Note that this can be customized for any data by specifying the format file.
* Issues and pull requests are welcome!

## Caveat
While this program has been tested on a linux system, it is likely to also work on MacOS and Windows.  But note that it is likely to be necessary to run dataset2binary on the same system that you run the c or fortran code, as binary files are not generally portable across different OSes.

## General description of the code and some notes
* In a nutshell, dataset2binary uses pandas to read the CSV/stata/sas data and converts it to an array.  It then uses "tofile" in numpy to output a binary file.  These things of course can be done manually with pandas/numpy but there are a number of tedious things to keep track of and lots of things that can go wrong.  Additionally, writing the c and fortran code to read the binary data can be fairly time consuming.  The goal here was to automate this as much as possible.
* As noted, the code uses pandas to read the CSV/stata/sas dataset.  Consequently, adding additional input formats should be trivial for anything pandas can read.
