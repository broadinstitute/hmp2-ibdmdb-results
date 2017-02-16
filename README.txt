To start the mezzanine application:

$ sudo -u ibdmdb /bin/bash
$ . /local/ibdmdb/SOURCE_THIS
$ . /local/ibdmdb/mezzanine/bin/activate
$ cd /local/ibdmdb/mezzanine/hmp2
# for config file with local socket:
$ gunicorn_django -c /local/ibdmdb/etc/gunicorn.conf
# for port:
$ gunicorn_django -w 2 -b 127.0.0.1:9090 &

# try this now (as of 2/19/15)
$ cd /local/ibdmdb/mezzanine
$ nohup gunicorn -c /local/ibdmdb/etc/gunicorn.conf hmp2.wsgi:application

# Why gunicorn -w 2 -b 127.0.0.1:9090 hmp2:app doesn't work - I'm not sure...

# The mezzanine deployment on ibdmdb-int2 initially scanned the filesystem 
for files to display to the user during web requests.  This prooved a rather
bad idea as the filesystem is slow (and sometimes unresponsive) due to 
sharing it with other groups at the Broad).  Thus, we turned to caching.
A python script called 'build_fs_cache.py' runs nightly and records all
files in the directories:

/seq/ibdmdb/data_deposition
/seq/ibdmdb/processing
/seq/ibdmdb/public

and creates the following caches (containing the files
found under those directories)

/local/ibdmdb/mezzanine/hmp2/data_cache_fs.txt
/local/ibdmdb/mezzanine/hmp2/processing_cache_fs.txt
/local/ibdmdb/mezzanine/hmp2/public_cache_fs.txt

These files are used during web requests to display 
links to the current content on each filesystem area.

