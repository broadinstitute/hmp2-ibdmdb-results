import os
import sys

HELP="""%prog 

%prog - build_fs_cache

Program builds a cached copy of the filesystem for use by
mezzanine when interacting with public html requests.  This
program is designed to be run via cron.

Note: This caching is necessary due to the latency imposed
by the Broad filesystem 'iodine'.  10.29.2014 KRB
"""

data_cache_file = '/local/ibdmdb/mezzanine/hmp2/data_cache_fs.txt'
processing_cache_file = '/local/ibdmdb/mezzanine/hmp2/processing_cache_fs.txt'
public_cache_file = '/local/ibdmdb/mezzanine/hmp2/public_cache_fs.txt'

data_cache_dir = '/seq/ibdmdb/data_deposition'
processing_cache_dir = '/seq/ibdmdb/processing'
public_cache_dir = '/seq/ibdmdb/public'

def walk(dir):
    for topdir, dirs, files in os.walk(dir):
        for file in files: 
            yield os.path.join(topdir, file)

def build(dir, cache_file):
    print >> sys.stdout, "Building " + cache_file + "..."
    with open(cache_file, 'w') as f:
        for file in walk(dir):
            print >> f, file

def main():
    build(data_cache_dir, data_cache_file + ".new")
    os.rename(data_cache_file + ".new", data_cache_file)

    build(processing_cache_dir, processing_cache_file + ".new")
    os.rename(processing_cache_file + ".new", processing_cache_file)

    build(public_cache_dir, public_cache_file + ".new")
    os.rename(public_cache_file + ".new", public_cache_file)

if __name__ == '__main__':
    main()

