"""Cloud browser URLs."""
from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView 


urlpatterns = patterns('hmp2.hmp2_results.views',  
    url(r'^$', RedirectView.as_view(url="hmp2_results_summary", ), name="cloud_browser_index"),
    url(r'^summary.html', 'summary', name="hmp2-summary")
    url(r'^summary/(?P<project>\w+)/(?P<data_type>\w+)/(?P<week>\d+)/$', 'summary', name='hmp2-dataset-summary'),
    url(r'^.*products$', 'products', name="hmp2-products"),
    url(r'^.*rawfiles', 'rawfiles', name="hmp2-raw-files"),
    url(r'^.*metadata', 'metadata', name="hmp2-metadata"),
    url(r'^.*tardownload', 'tardownload', name="hmp2-tardownload"),
)
