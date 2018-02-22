"""
The DRF Engine doen'st encode JSON-LD. This is a temporary workaround that
that extends JSONRender. The render method adds the '@' symbol whenever a 
field's name starts 'context' or 'id' or 'type'. I also added an KEY_ORDER
list to render in the correct order. (@context should always be on top)
https://groups.google.com/forum/#!topic/django-rest-framework/uwSHhSHwTVo
"""

from collections import OrderedDict
import re

__author__ = 'guglielmo'
__author__ = 'jana.rajakumar@utoronto.ca'

from rest_framework.renderers import JSONRenderer

# Used from https://github.com/iiif-prezi/iiif-prezi/blob/master/iiif_prezi/factory.py
KEY_ORDER = ["@context", "@id", "@type", "@value", "@language", "label", "value",
             "metadata", "description", "thumbnail", "rendering", "attribution", "license",
             "logo", "format", "height", "width", "startCanvas",
             "viewingDirection", "viewingHint", "navDate",
             "profile", "seeAlso", "search", "formats", "qualities", "supports",
             "scale_factors", "scaleFactors", "tile_width", "tile_height", "tiles", "sizes",
             "within", "motivation", "stylesheet", "resource", "contentLayer",
             "on", "default", "item", "style", "full", "selector", "chars", "language", 
             "sequences", "structures", "canvases", "resources", "images", "otherContent" ] 
KEY_ORDER_HASH = dict([(KEY_ORDER[x],x) for x in range(len(KEY_ORDER))])


def ld(data):
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            if value:
                if re.match(r'^context(.*)', key):
                    new_key = "@context"
                elif re.match(r'^id(.*)', key):
                    new_key = "@id"
                elif re.match(r'^type(.*)', key):
                    new_key = "@type"
                else:
                    new_key = key
                new_dict[new_key] = ld(value)
        return OrderedDict(sorted(new_dict.items(), key=lambda x: KEY_ORDER_HASH.get(x[0], 1000)))

    if isinstance(data, (list, tuple)):
        for i in range(len(data)):
            data[i] = ld(data[i])
        return data

    return data


class JSONLDRenderer(JSONRenderer):
    def render(self, data, *args, **kwargs):
        return super(JSONLDRenderer, self).render(
            ld(data), *args, **kwargs)
