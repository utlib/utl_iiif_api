"""
The DRF Engine doesn't encode JSON-LD. This is a workaround that extends JSONRender.
The render method adds the '@' symbol for fields 'context', 'id' and 'type'.
Also specified is an KEY_ORDER list to render in the correct order.
"""

from collections import OrderedDict
import re
import json

__author__ = 'jana.rajakumar@utoronto.ca'

from rest_framework.renderers import JSONRenderer

# Used from https://github.com/iiif-prezi/iiif-prezi/blob/master/iiif_prezi/factory.py
KEY_ORDER = ["@context", "id", "@id", "@type", "@value", "@language", "label", "value",
             "metadata", "description", "thumbnail", "rendering", "attribution", "license",
             "logo", "format", "chars", "height", "width", "startCanvas",
             "viewingDirection", "viewingHint", "navDate",
             "profile", "seeAlso", "search", "formats", "qualities", "supports",
             "scale_factors", "scaleFactors", "tile_width", "tile_height", "tiles", "sizes",
             "within", "motivation", "stylesheet", "resource", "contentLayer",
             "on", "default", "item", "style", "full", "selector", "chars", "language", "service", "related",
             "collections", "manifests", "members", "sequences", "structures", "canvases", 
             "resources", "images", "otherContent", "ranges",
             "type", "total", "count", "first", "last", "partOf", "next", "items",
             "internalUseOnly", "name", "order", "belongsTo", "hidden", 'ownedBy', 'error', 'object', 
             'username', 'requestPath', 'requestMethod', 'remoteAddress', 'responseCode', 'startTime', 'endTime', 'queueID', 'responseBody', 'requestBody' ] 
KEY_ORDER_HASH = dict([(KEY_ORDER[x],x) for x in range(len(KEY_ORDER))])


def ld(data):
    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            if value:
                if re.match(r'^AT(.*)', key):
                    new_key = "@"+key[2:]
                else:
                    new_key = key
                if key in ["belongsTo", "children"]:
                    pass
                else:
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
