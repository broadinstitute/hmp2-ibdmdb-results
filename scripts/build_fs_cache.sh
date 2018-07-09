#!/bin/sh

DJANGODIR="$( cd "$( dirname "$0" )/../" && pwd )"  

ext=".new"
data_cache_file="${DJANGODIR}/hmp2/data_cache_fs.txt"
processing_cache_file="${DJANGODIR}/hmp2/processing_cache_fs.txt"
public_cache_file="${DJANGODIR}/hmp2/public_cache_fs.txt"

data_cache_dir='/seq/ibdmdb/data_deposition'
processing_cache_dir='/seq/ibdmdb/processing'
public_cache_dir='/seq/ibdmdb/public'

function create_fs
{
  #params: directory output_file
  echo "Building $2 from $1" 1>&2
  if [ -d $1 ]; then
    if [ -d $2 ] || [ -f $2 ]; then
      echo "Warning $2 exists - skipping"
    else
      find $1 -type l -or -type f > $2
    fi
  fi
}

# build the cache files
create_fs $data_cache_dir $data_cache_file$ext
create_fs $processing_cache_dir $processing_cache_file$ext
create_fs $public_cache_dir $public_cache_file$ext

# move cache files into place
mv $data_cache_file$ext $data_cache_file
mv $processing_cache_file$ext $processing_cache_file
mv $public_cache_file$ext $public_cache_file

