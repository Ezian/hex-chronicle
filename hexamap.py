
#!/usr/bin/env python3

import argparse, glob, sys, os,re
from posixpath import basename

def safe_cast(val, to_type, default=None):
   try:
      return to_type(val)
   except (ValueError, TypeError):
      return default

def parseHexFile(filename):
   error = False, 0, 0 
   # The file must exists
   if not os.path.isfile(filename):
      return error
   # The filename should follow the pattern XXYY-<some_name>.md
   basename = os.path.basename(filename)
   m = re.match('^(\d{2})(\d{2})-.*\.md$', basename)
   if m is None:
      return error
   
   x = int(m.group(1))
   y = int(m.group(2))
   
   return True, x, y

def generateFromFiles(files):
   print(files)

if __name__ == "__main__":   
   parser = argparse.ArgumentParser()
   parser.add_argument("src_path", metavar="path", type=str, nargs='*',
      help="Path to files to be merged; enclose in quotes, accepts * as wildcard for directories or filenames")


   args = parser.parse_args()
   
   hexfiles = dict()
      
   for arg in args.src_path:
      files = glob.glob(arg)

      if not files:
         print('File does not exist: ' + arg, file=sys.stderr)
      for file in files:
         isHexFile, x, y = parseHexFile(file)
         if isHexFile:
            hexfiles[x,y] = file
   
   generateFromFiles(hexfiles)
         