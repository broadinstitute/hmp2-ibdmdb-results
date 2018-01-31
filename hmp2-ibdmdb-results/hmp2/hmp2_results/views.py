"""Cloud browser views."""
import re
import sys
import time
import os
import datetime
import itertools
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
    import sys; print >> sys.stderr, file
    if 'mibc_products' in file:
        return file.split('mibc_products/')[1]
    if 'anpan_products' in file:
        return file.split('anpan_products/')[1]
    if 'anadama_products' in file:
        return file.split('anadama_products/')[1]
    else:
        return os.path.basename(file)

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
            cache.append(line.strip())
        return cache

    def match(self, targets, tags, now):
        if now != self.date:
            print >> sys.stderr, "rebuilding cache for " + self.topdir
            print >> sys.stderr, "now: " + str(now) + " self.data: " + str(self.date)
            self.filesystem_cache = self.walk()
            self.date = now
        
        print >> sys.stderr, "cache has " + str(len(self.filesystem_cache)) + " entries."
        files = [file for file in self.filesystem_cache for target in targets if file.endswith(target)]
        if tags:
            files = [file for file in files if any(tag in file for tag in tags)]
        return files
    
    def endswith(self, target, now):
        if now != self.date:
            self.filesystem_cache = self.walk()
        return [file for file in self.filesystem_cache if file.endswith(target)]


def walk(topdir, targets, tags=[]):
    global cache_dict
    if cache_dict.get(topdir) is None:
        fs = filesystem(topdir)
        cache_dict[topdir] = fs
    return cache_dict.get(topdir).match(targets, tags, datetime.date.today())
        

def convert_to_web(files, branch):
    result = []
    for file in files:
        import sys; print >> sys.stderr, "ofile: ", file
        filesegs = file.split('/')[4:]
        filesegs.insert(0,branch)
        
        f = '/'.join(filesegs)
        import sys; print >> sys.stderr, "newfile: ", f
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
    
    container_path, object_path = os.path.split(path)
    if object_path == "summary.html":

        template="hmp2-summary.html"
        tmpfiles = walk("/seq/ibdmdb/public", ["complete.html"])
        for tfile in list(tmpfiles):
            tfilesegs = tfile.split("/")

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
            study.append(file.split('/')[3])
            if file.split('/')[4] == 'WGS':
                types.append("Metagenomes")
            elif file.split('/')[4] == 'MTX':
                types.append("Metatranscriptomes")
            elif file.split('/')[4] == 'HTX':
                types.append("Host Transcriptomes")
            elif file.split('/')[4] == 'HG':
                types.append("Host Genomes")
            else:
                types.append(file.split('/')[4])
            theweek = "20" + file.split('/')[5]
            theweek = theweek[:4] + '.' + theweek[4:]
            week.append(theweek)
            # products
            segs = file.split('/')[:-1]
            segs.append("products")
            if file.split('/')[4] == 'HG':
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
            if file.split('/')[4] == 'Metabolites':
                raw.append(None)
            elif file.split('/')[4] == "HTX":
                raw.append(None)
            elif files.split('/')[4] == "Serology":
                raw.append(None)                
            else:
                raw.append('/'.join(segs))

            meta = file.split('/')[:-1]
            meta.append("metadata")
            metafiles.append('/'.join(meta))

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
                'reports': types,
                'charts': charts,
                'rawfiles': raw,
                'htmlfiles': htmlfiles,
                'metafiles': metafiles,
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
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    if object_path == "products":

        barchart = "barchart"
        pcoa = None
        heatmap = None
        rawfiles = []
        productfiles = []
        product_info = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = "carze"
        week = path_list(path)[-2]
        type = path_list(path)[-3]
        study = path_list(path)[-4]
        sanitized_type = type
 
        if type == "WGS":
            sanitized_type = "Metagenomes"
            product_info = [
                {'label': 'Gene Calls', 'desc': 'Contain GFF3 + Protein CDS'}
            ]
        elif type == "MTX":
            sanitized_type = "Metatranscriptomes"
        elif type == "Proteomics":
            product_info = [
                             {'label': '1pep', 'desc': '1 Peptide per Protein'},
                             {'label': '2pep', 'desc': '2 Peptides per Protein'}
                           ]

        webproducts = []
        data_extensions = ['.biom']
        rawpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])

        filetypes = { 
            'taxbiomtype': { 
                "ext": ["taxonomic_profile.biom"],
                "name": "Taxonomic Profiles (BIOM)",
                "slug": "taxbiomtype"
                }, 
            'funcbiomtype': { 
                "ext": ["_picrust.biom"],
                "name": "Functional Profiles (BIOM)",
                "slug": "funcbiomtype"
                }, 
            'functarball': { 
                "ext": ["_humann2.tar.bz2"],
                "name": "Functional Profiles", 
                "slug": "functarball" 
                }, 
            "rolluptype": {
                "ext": ["ppm.tsv.gz"],
                "name": "Peptide Roll Up (Text)",
                "slug": "rolluptype"
                },
            "rollupbiomtype": {
                "ext": ["ppm.biom.gz"],
                "name": "Peptide Roll Up (BIOM)",
                "slug": "rollupbiomtype"
                },
            "assembly_contigs": {
                "ext": ["_contigs.fna.gz"],
                "name": "Contigs",
                "slug": "assembly_contigs"
            },
            "assembly_genes": {
                "ext": ["_genes.tar.bz2"],
                "name": "Gene Calls",
                "slug": "assembly_genes"
            },
            'elisaftype': {
                "ext": ["_ELISA_Data.tsv"],
                "name": "ELISA",
                "slug": "elisatype"
            },
            'taxproftype': { 
                "ext": ["taxonomic_profile.tsv"],
                "name": "Taxonomic Profiles (Text)",
                "slug": "taxproftype"
                },
            "merged": {
                "ext": ["s.tsv.gz", "s.biom.gz", "s.csv.gz"],
                "name": "Merged Tables",
                "slug": "merged",
            }
        }

        jsonfiles = dict()
        for file in walk(rawpath, [".json"]):
            jsonfiles[ file.replace('.json', '') ] = _products_xlate(file)
        for ftype in filetypes.iterkeys():
            for file in walk(rawpath, filetypes[ftype].get('ext'), filetypes[ftype].get('tags', [])):
                if 'metaphlan' in file:
                    continue
                elif 'merge' in file:
                    continue

                filetypes[ftype]['keep'] = True
                webproducts.append(
                    dict(f=_products_xlate(file), 
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
        for s in ("functarball", "taxbiomtype", "merged", "taxproftype", 
                  "rolluptype", "rollupbiomtype", "mbx_counts",
                  "assembly_contigs", "assembly_genes"):
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
                               'product_info': product_info,
                               'productpath': productpath,
                               'productfiles': webproducts,
                               'filetypes': filetypes,
                               'selected': selected},
                              context_instance=RequestContext(request))


def rawfiles(request, path='', template="hmp2-rawfiles.html"):

    path = request.path
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)

    if object_path == "rawfiles":

        rawfiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = "carze"
        week = path_list(path)[-2]
        type = path_list(path)[-3]
        study = path_list(path)[-4]
        sanitized_type = type
 
        if type == "WGS":
            sanitized_type = "Metagenomes"

        data_extensions = ['.fa']
        rawpath = "/seq/ibdmdb/processing/" + '/'.join(path_list(path)[2:-1])
        logfiles = dict()
        for file in walk(rawpath, ['.log']):
            logfiles[file.replace('_clean.log', '.fastq')] = _products_xlate(file)
            logfiles[file.replace('_clean.log', '.fastq.bz2')] = _products_xlate(file)
            logfiles[file.replace('_clean.log', '.fastq.gz')] = _products_xlate(file)
            logfiles[file.replace('.log', '.fastq.gz')] = _products_xlate(file)
        for ftype in ('.fa', '.fastq', '.csv', '.raw', '.raw.gz', '.fastq.bz2', '.fastq.gz', '.tar', '.bam'):
            for file in walk(rawpath, [ftype]):
                if "knead" in file:
                    continue
                elif "bowtie2" in file:
                    continue
                elif "trimmed" in file:
                    continue
                elif 'truncated' in file:
                    continue
                elif 'sort' in file:
                    continue
                elif 'nonchimeric' in file:
                    continue
                elif 'otu' in file:
                    continue
                elif 'derep' in file:
                    continue
                elif 'clean.fastq' in file:
                    continue

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
    path = path.replace("%20", " ")
    path = path.replace("%3A", ":")
    if path[-1] == '/':
        path = path[:-1]
    container_path, object_path = os.path.split(path)
    
    if object_path == "metadata":

        metafiles = []
        startpath = "/seq/ibdmdb/data_deposition/" + '/'.join(path_list(path)[2:-2])
        startdate = time.ctime(os.path.getctime(startpath))
        finishpath = "/seq/ibdmdb/public/" + '/'.join(path_list(path)[2:-1])
        finishdate = time.ctime(os.path.getctime(finishpath))
        user = path_list(path)[-3]
        week = path_list(path)[-4]
        type = path_list(path)[-5]
        study = path_list(path)[-6]
        sanitized_type = type
 
        if type == "WGS":
            sanitized_type = "Metegenomes"

        data_extensions = ['.txt']
        metapath = "/seq/ibdmdb/processing/" + '/'.join(path_list(path)[2:-1])
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
    pathdict = {"products": "/seq/ibdmdb/public",
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
    
    
