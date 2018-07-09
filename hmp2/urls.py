from __future__ import unicode_literals

from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin

from mezzanine.core.views import direct_to_template
from django.conf import settings

admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.

urlpatterns = i18n_patterns("",

    # Change the admin prefix here to use an alternate URL for the
    # admin interface, which would be marginally more secure.
    #("^%sadmin/" % settings.SITE_PREFIX, include(admin.site.urls)),
    ("^admin/", include(admin.site.urls)),
)

urlpatterns += patterns('',

    # We don't want to presume how your homepage works, so here are a
    # few patterns you can use to set it up.

    # HOMEPAGE AS STATIC TEMPLATE
    # ---------------------------
    # This pattern simply loads the index.html template. It isn't
    # commented out like the others, so it's the default. You only need
    # one homepage pattern, so if you use a different one, comment this
    # one out.

    url("^$", direct_to_template, {"template": "index.html"}, name="home"),
    #url("^%s$" % settings.SITE_PREFIX, direct_to_template, {"template": "index.html"}, name="home"),
    ##url("^%s$" % settings.SITE_PREFIX, direct_to_template, {"template": "index.html"}, name="home"),

    # HOMEPAGE AS AN EDITABLE PAGE IN THE PAGE TREE
    # ---------------------------------------------
    # This pattern gives us a normal ``Page`` object, so that your
    # homepage can be managed via the page tree in the admin. If you
    # use this pattern, you'll need to create a page in the page tree,
    # and specify its URL (in the Meta Data section) as "/", which
    # is the value used below in the ``{"slug": "/"}`` part.
    # Also note that the normal rule of adding a custom
    # template per page with the template name using the page's slug
    # doesn't apply here, since we can't have a template called
    # "/.html" - so for this case, the template "pages/index.html"
    # should be used if you want to customize the homepage's template.

    #url("^$", "mezzanine.pages.views.page", {"slug": "/"}, name="home"),

    # HOMEPAGE FOR A BLOG-ONLY SITE
    # -----------------------------
    # This pattern points the homepage to the blog post listing page,
    # and is useful for sites that are primarily blogs. If you use this
    # pattern, you'll also need to set BLOG_SLUG = "" in your
    # ``settings.py`` module, and delete the blog page object from the
    # page tree in the admin if it was installed.

    # url("^$", "mezzanine.blog.views.blog_post_list", name="home"),
    #url(r'^%scb/.*/Public/\w+/(?P<type>\w+)/(?P<date>\w+)/(?P<name>\w+)/mibc_products/\w+.html$' % settings.SITE_PREFIX, include('cloud_browser.urls')),
    #url(r'^%scb/.*/Public/\w+/(?P<type>\w+)/(?P<date>\w+)/(?P<name>\w+)/mibc_products/\w+.html$' % settings.SITE_PREFIX, direct_to_template, {"template": "test1.html"}, name="test1"),
    url(r'^%scb/' % settings.SITE_PREFIX, include('cloud_browser.urls')),
    url(r'^%spublic/' % settings.SITE_PREFIX, include('hmp2.hmp2_results.urls')),
    #url(r'^cb/', include('cloud_browser.urls')),
    #url(r'^reports/', include('cloud_browser.urls')),

    # MEZZANINE'S URLS
    # ----------------
    # ADD YOUR OWN URLPATTERNS *ABOVE* THE LINE BELOW.
    # ``mezzanine.urls`` INCLUDES A *CATCH ALL* PATTERN
    # FOR PAGES, SO URLPATTERNS ADDED BELOW ``mezzanine.urls``
    # WILL NEVER BE MATCHED!
    #url("^%slogin/$" % settings.SITE_PREFIX, direct_to_template, {"template": "login.html"}, name="login"),
##    url(r'^%slogin/$' % settings.SITE_PREFIX, 'mezzanine.accounts.views.login'), 
    #url(r'^%slogin/$' % settings.SITE_PREFIX, 'mezzanine.utils.urls.login_redirect'), 
    #url(r'^%saccounts/login/$' % settings.SITE_PREFIX, 'django.contrib.auth.views.login', {'template_name': 'admin/login.html'}), 
##    url("^%slogout/$" % settings.SITE_PREFIX, 'mezzanine.accounts.views.logout'),
    #url(r'^%saccounts/logout/$' % settings.SITE_PREFIX, 'mezzanine.accounts.views.logout'), 

    # If you'd like more granular control over the patterns in
    # ``mezzanine.urls``, go right ahead and take the parts you want
    # from it, and use them directly below instead of using
    # ``mezzanine.urls``.
    ("^", include("mezzanine.urls")),

    # MOUNTING MEZZANINE UNDER A PREFIX
    # ---------------------------------
    # You can also mount all of Mezzanine's urlpatterns under a
    # URL prefix if desired. When doing this, you need to define the
    # ``SITE_PREFIX`` setting, which will contain the prefix. Eg:
    # settings.SITE_PREFIX = "/tunnel"
    # For convenience, and to avoid repeating the prefix, use the
    # commented out pattern below (commenting out the one above of course)
    # which will make use of the ``SITE_PREFIX`` setting. Make sure to
    # add the import ``from django.conf import settings`` to the top
    # of this file as well.
    # Note that for any of the various homepage patterns above, you'll
    # need to use the ``SITE_PREFIX`` setting as well.

##    ("^%s" % settings.SITE_PREFIX, include("mezzanine.urls"))

)

# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.
handler404 = "mezzanine.core.views.page_not_found"
handler500 = "mezzanine.core.views.server_error"
