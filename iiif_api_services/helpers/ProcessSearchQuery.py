
def process_search_query(search_query):
    query = {}
    for key, val in search_query.items():
        if ("=" in key):  # pragma: no cover
            val = key.split("=")[1] if len(key.split("=")) > 1 else ""
            key = key.split("=")[0]
        query[key.strip()+'__icontains'] = val.strip()
    return query
