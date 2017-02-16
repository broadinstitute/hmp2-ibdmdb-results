"""Cloud browser views."""
import re
import sys
import time
import os.path
import datetime
import subprocess

from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


cache_dict = {}
data_fs = '/seq/ibdmdb/data_deposition'
processing_fs = '/seq/ibdmdb/processing'
public_fs = '/seq/ibdmdb/public'

data_cache_file = '/local/ibdmdb/mezzanine/hmp2/data_cache_fs.txt'
processing_cache_file = '/local/ibdmdb/mezzanine/hmp2/processing_cache_fs.txt'
public_cache_file = '/local/ibdmdb/mezzanine/hmp2/public_cache_fs.txt'

def _products_xlate(file):
    if 'mibc_products' in file:
        return file.split('mibc_products/')[1]
    if 'anpan_products' in file:
        return file.split('anpan_products/')[1]
    if 'anadama_products' in file:
        return file.split('anadama_products/')[1]
        

class filesystem(object):
    """ walking the broad directory structure is expensive for web requests.
        This class caches the results of those requests on a daily basis so
        that a speedy return is assured.
    """
    
    def __init__(self, topdir):
        self.topdir = topdir
        self.date = datetime.date.today()
        self.filesystem_cache = self.walk()

    def disk_cache(self):
        if self.topdir.startswith(data_fs):
            with open(data_cache_file, "r") as f:
                for line in f:
                    if line.startswith(self.topdir):
                        yield line

        elif self.topdir.startswith(processing_fs):
            with open(processing_cache_file, "r") as f:
                for line in f:
                    if line.startswith(self.topdir):
                        yield line

        elif self.topdir.startswith(public_fs):
            with open(public_cache_file, "r") as f:
                for line in f:
                    if line.startswith(self.topdir):
                        yield line

    def walk(self):
        cache = []
        for line in self.disk_cache():
            #print >> sys.stderr, "line: " + line
            cache.append(line.strip())
        return cache

    def match(self, target, now):
        if now != self.date:
            print >> sys.stderr, "rebuilding cache for " + self.topdir
            print >> sys.stderr, "now: " + str(now) + " self.data: " + str(self.date)
            self.filesystem_cache = self.walk()
            self.date = now
        
        print >> sys.stderr, "cache has " + str(len(self.filesystem_cache)) + " entries."
        return [file for file in self.filesystem_cache if file.endswith(target)]
    
    def endswith(self, target, now):
        if now != self.date:
            self.filesystem_cache = self.walk()
        return [file for file in self.filesystem_cache if file.endswith(target)]


def walk(topdir, target):
    global cache_dict
    if cache_dict.get(topdir) is None:
        fs = filesystem(topdir)
        cache_dict[topdir] = fs
    return cache_dict.get(topdir).match(target, datetime.date.today())
        

def convert_to_web(files, branch):
    result = []
    for file in files:
        #import sys; print >> sys.stderr, "ofile: ", file
        filesegs = file.split('/')[4:]
        filesegs.insert(0,branch)
        
        f = '/'.join(filesegs)
        #import sys; print >> sys.stderr, "newfile: ", f
        result.append("/tunnel/" + f)
    return result 


def tar(fnames):
    proc = subprocess.Popen(
        ["tar", "--create", "--files-from=-", 
         "--file=-", "--dereference", "--hard-dereference"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
        )
    for fname in fnames:
        if not os.path.isfile(fname):
            continue
        print >> proc.stdin, fname
    proc.stdin.close()
    return proc.stdout


def summary(request, path='', template="hmp2-summary.html"):

    path = request.path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    
    #import sys; print >> sys.stderr, "path: " + path
    container_path, object_path = os.path.split(path)
    if object_path == "summary.html":

        template="hmp2-summary.html"
        # get all *.html files in public folder that resize immediately under a 'mibc_products' directory
        # strip out summary.html file itself
        tmpfiles = walk("/seq/ibdmdb/public", "complete.html")
        for tfile in list(tmpfiles):
            tfilesegs = tfile.split("/")
            #indx = tfilesegs.index('mibc_products')
            #if indx != len(tfilesegs) - 2:
            #    tmpfiles.remove(tfile)

        htmlfiles = convert_to_web(tmpfiles, "public")
        types = []
        week = []
        study = []
        detail = []
        products = []
        charts = []
        raw = []
        metafiles = []
        start=True
        for file in htmlfiles:
            #import sys; print >> sys.stderr, "nfile: " + file
            study.append(file.split('/')[3])
            if file.split('/')[4] == 'WGS':
                types.append("Metagenomes")
            else:
                types.append(file.split('/')[4])
            theweek = "20" + file.split('/')[5]
            theweek = theweek[:4] + '.' + theweek[4:]
            week.append(theweek)
            # products
            segs = file.split('/')[:-1]
            segs.append("products")
            if file.split('/')[4] == 'Metabolites':
                products.append(None)
            else:
                products.append('/'.join(segs))
            # charts
            segs = file.split('/')[:-1]
            segs.append("charts")
            if file.split('/')[4] == 'Metabolites':
                charts.append(None)
            else:
                charts.append('/'.join(segs))
            # raw
            segs = file.split('/')[:-1]
            segs.append("rawfiles")
            #if file.split('/')[4] == 'Metabolites':
            #    raw.append(None)
            #else:
            #    raw.append('/'.join(segs))
            raw.append('/'.join(segs))

            meta = file.split('/')[:-1]
            meta.append("metadata")
            metafiles.append('/'.join(meta))

        csvfiles = map(os.path.basename, walk("/seq/ibdmdb/public", ".csv"))
        joined_meta_file = sorted([f for f in csvfiles if "project_metadata" in f],
                                  key=lambda f: int(re.sub(r'\D+', '', f) or 0))[-1]
        unjoined_meta_file = sorted([f for f in csvfiles if "unjoined_metadata" in f],
                                    key=lambda f: int(re.sub(r'\D+', '', f) or 0))[-1]
        
        return render_to_response(
            template,
            {
                'path': path,
                'size': len(htmlfiles),
                'range': range(len(htmlfiles)),
                'types': types,
                'study': study,
                'week': week,
                'detail': detail,
                'products': products,
                'charts': charts,
                'rawfiles': raw,
                'htmlfiles': htmlfiles,
                'metafiles': metafiles,
                'joined_meta_file': joined_meta_file,
                'unjoined_meta_file': unjoined_meta_file,
            },
            context_instance=RequestContext(request)
            )

    else:
        raise Http404("No object at: %s" % object_path)

def path_list(path):
    segs = path.split('/')
    segs.pop(0)
    return segs 

def products(request, path='', template="hmp2-products.html"):

    path = request.path
    #import sys; print >> sys.stderr, "biomfiles"
    #import sys; print >> sys.stderr, "path: " + path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    #import sys; print >> sys.stderr, "object_path: " + object_path
    if object_path == "products":

        barchart = "barchart"
        pcoa = None
        heatmap = None
        rawfiles = []
        productfiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        #import sys; print >> sys.stderr, "startpath: " + startpath
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #import sys; print >> sys.stderr, "finishpath: " + finishpath
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = path_list(path)[-3]
        week = path_list(path)[-4]
        type = path_list(path)[-5]
        study = path_list(path)[-6]
        sanitized_type = type
 
        #import sys; print >> sys.stderr, "type: " + type

        if type == "WGS":
            sanitized_type = "Metegenomes"

        webproducts = []
        data_extensions = ['.biom']
        rawpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr, "rawpath: " + rawpath
        #possible_rawfiles = walk(rawpath)
        filetypes = { 
            '.biom': { 
                "name": "Taxonomic Profiles (BIOM)",
                "slug": "biomtype"
                }, 
            '.tar.bz2': { 
                "name": "Functional Profiles", 
                "slug": "functype" 
                }, 
            '_tax.txt': { 
                "name": "Taxonomic Profiles (Text)",
                "slug": "taxproftype"
                },
            ".png": {
                "name": "Figures",
                "slug": "figtype"
                },
            ".merged.tsv": {
                "name": "Merged Tables",
                "slug": "merged",
                },
            }

        jsonfiles = dict()
        for file in walk(rawpath, ".json"):
            jsonfiles[ file.replace('.json', '') ] = _products_xlate(file)
        for ftype in filetypes.iterkeys():
            for file in walk(rawpath, ftype):
                filetypes[ftype]['keep'] = True
                webproducts.append(
                    dict(f=_products_xlate(file), 
                         l=jsonfiles.get(file.replace(ftype, '')),
                         t=ftype)
                    )
                
        to_del = []
        for k in filetypes:
            keep = filetypes[k].pop('keep', False)
            if not keep:
                to_del.append(k)
        for k in to_del:
            del filetypes[k]

        selected = ""
        for s in ("_tax.txt", ".biom", ".tar.bz2", '.png'):
            if s in filetypes:
                selected = s
                break

        productpath= "/tunnel/cb/document/Public/" + '/'.join(path_list(path)[2:-1])

        return render_to_response(template,
                              {'path': path,
                               'sdate': startdate,
                               'fdate': finishdate,
                               'week': week,
                               'user': user,
                               'type': sanitized_type,
                               'study': study,
                               'productpath': productpath,
                               'productfiles': webproducts,
                               'filetypes': filetypes,
                               'selected': selected},
                              context_instance=RequestContext(request))


def taxonomy(request, path='', template="hmp2-taxonomy.html"):

    path = request.path
    #import sys; print >> sys.stderr, "taxonomy"
    #import sys; print >> sys.stderr, "path: " + path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    #import sys; print >> sys.stderr, "object_path: " + object_path
    if object_path == "charts":

        barchart = "barchart"
        pcoa = None
        heatmap = None
        rawfiles = []
        productfiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        #import sys; print >> sys.stderr, "startpath: " + startpath
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #import sys; print >> sys.stderr, "finishpath: " + finishpath
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = path_list(path)[-3]
        week = path_list(path)[-4]
        type = path_list(path)[-5]
        study = path_list(path)[-6]
        sanitized_type = type
 
        rawbarpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr,"rawbarpath: " + rawbarpath
        barchart = []
        for file in walk(rawbarpath, 'bar_charts.html'):
            if 'mibc_products' in file:
                barchart.append(file.split('mibc_products/')[1])
            if 'anpan_products' in file:
                barchart.append(file.split('anpan_products/')[1])
            if 'anadama_products' in file:
                barchart.append(file.split('anadama_products/')[1])
            #print >> sys.stderr,"barchart: " + barchart[0]

        barpath = "/tunnel/cb/document/Public/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr,"barpath: " + barpath

        if type == "16S":
            sanitized_type = type
        elif type == "WGS":
            sanitized_type = "Metegenomes"

        charts = []
        rawpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr, "rawpath: " + rawpath
        #possible_rawfiles = walk(rawpath)
        for chart in os.listdir(rawpath):
            if chart.endswith(".png"):
                charts.append(chart)
        #charts.append("otu_table_merged_meta.biom.pcl_pcoa_plot-BarcodeSequence.png")
        #charts.append("otu_table_merged_meta.biom.pcl_pcoa_plot-LinkerPrimerSequence.png")
        #charts.append("otu_table_merged_meta.biom.pcl_pcoa_plot-Description.png")

        chartpath = "/tunnel/cb/document/Public/" + '/'.join(path_list(path)[2:-1])
        return render_to_response(template,
                              {'path': path,
                               'sdate': startdate,
                               'fdate': finishdate,
                               'week': week,
                               'user': user,
                               'type': sanitized_type,
                               'study': study,
                               'barpath': barpath,
                               'barchart': barchart,
                               'barchartrange': range(len(barchart)),
                               'chartpath': chartpath,
                               'charts': charts,
                               'chartrange' : range(len(charts))},
                              context_instance=RequestContext(request))


def rawfiles(request, path='', template="hmp2-rawfiles.html"):

    path = request.path
    #import sys; print >> sys.stderr, "rawfiles"
    #import sys; print >> sys.stderr, "path: " + path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    #import sys; print >> sys.stderr, "object_path: " + object_path
    if object_path == "rawfiles":

        rawfiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        #import sys; print >> sys.stderr, "startpath: " + startpath
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #import sys; print >> sys.stderr, "finishpath: " + finishpath
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = path_list(path)[-3]
        week = path_list(path)[-4]
        type = path_list(path)[-5]
        study = path_list(path)[-6]
        sanitized_type = type
 
        #import sys; print >> sys.stderr, "type: " + type

        if type == "WGS":
            sanitized_type = "Metegenomes"

        data_extensions = ['.fa']
        rawpath = "/seq/ibdmdb/processing/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr, "rawpath: " + rawpath
        #if type == "16S":
        logfiles = dict()
        for file in walk(rawpath, '.log'):
            logfiles[file.replace('_clean.log', '.fastq')] = _products_xlate(file)
        for ftype in ('.fa', '.fastq', '.csv'):
            for file in walk(rawpath, ftype):
                rawfiles.append(
                    dict(f=_products_xlate(file), l=logfiles.get(file))
                    )

        # convert rawpath to web accessible path
        rawpath = "/tunnel/static/" + '/'.join(path_list(path)[2:-1])

        return render_to_response(template,
                              {'path': path,
                               'sdate': startdate,
                               'fdate': finishdate,
                               'week': week,
                               'user': user,
                               'type': sanitized_type,
                               'study': study,
                               'rawpath': rawpath,
                               'rawfiles': rawfiles,
                               'logfiles': logfiles},
                              context_instance=RequestContext(request))



def metadata(request, path='', template="hmp2-metadata.html"):

    path = request.path
    #import sys; print >> sys.stderr, "rawfiles"
    #import sys; print >> sys.stderr, "path: " + path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    #import sys; print >> sys.stderr, "object_path: " + object_path
    if object_path == "metadata":

        metafiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        #import sys; print >> sys.stderr, "startpath: " + startpath
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        #import sys; print >> sys.stderr, "finishpath: " + finishpath
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = path_list(path)[-3]
        week = path_list(path)[-4]
        type = path_list(path)[-5]
        study = path_list(path)[-6]
        sanitized_type = type
 
        #import sys; print >> sys.stderr, "type: " + type

        if type == "WGS":
            sanitized_type = "Metegenomes"

        data_extensions = ['.txt']
        metapath = "/seq/ibdmdb/processing/" + '/'.join(path_list(path)[2:-1])
        #print >> sys.stderr, "rawpath: " + rawpath
        #possible_rawfiles = walk(rawpath)
        for file in walk(metapath, 'map.txt'):
            if file.endswith('mibc_products/map.txt'):
                metafiles.append(file.split('mibc_products/')[1])
            if file.endswith('anpan_products/map.txt'):
                metafiles.append(file.split('anpan_products/')[1])
            if file.endswith('anadama_products/map.txt'):
                metafiles.append(file.split('anadama_products/')[1])
        if len(metafiles) > 0:
            print >> sys.stderr,"metafiles: " + metafiles[0] + " size: " + str(len(metafiles))


        # convert metapath to web accessible path
        metapath = "/tunnel/cb/document/Processing/" + '/'.join(path_list(path)[2:-1])
        print >> sys.stderr, "metapath: " + metapath

        #try:
        #    dum, extension = os.path.splitext(metafiles[0])
        #except IndexError:
        #    print >> sys.stderr, "IndexError: "
        return render_to_response(template,
                              {'path': path,
                               'sdate': startdate,
                               'fdate': finishdate,
                               'week': week,
                               'user': user,
                               'type': sanitized_type,
                               'study': study,
                               'metapath': metapath,
                               'metafiles': metafiles,
                               'metafilerange' : range(len(metafiles))},
                              context_instance=RequestContext(request))

def tardownload(request, path='', template=""):
    pathdict = {"products": "/seq/ibdmdb/processing",
                  "charts": "/seq/ibdmdb/public",
                "rawfiles": "/seq/ibdmdb/processing",
                "metadata": "/seq/ibdmdb/processing"}

    head, tail = os.path.split(request.GET['fromurl'])
    base = pathdict.get(tail, None)
    if not base:
        raise Http404()
    middle = re.sub(r'^/tunnel/public/', '', head)
    tarfile = tar([ os.path.join(base, middle, fname) for fname in request.GET.getlist('fs') ])
    resp = HttpResponse(tarfile, content_type="application/x-tar")
    resp['Content-Disposition'] = "attachment; filename=ibdmdb_download.tar"
    return resp
    
    
