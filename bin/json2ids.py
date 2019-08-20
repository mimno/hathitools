import json, sys

## Three functions from https://github.com/htrc/htrc-feature-reader/blob/master/examples/ID_to_Rsync_Link.ipynb

def id_encode(id):
    return id.replace(":", "+").replace("/", "=").replace(".", ",")

def id2path(id):
    clean_id = id_encode(id)
    path = []
    while len(clean_id) > 0:
        val, clean_id = clean_id[:2], clean_id[2:]
        path.append(val)
    return '/'.join(path)

def id_to_rsync(htid):
    '''
    Take an HTRC id and convert it to an Rsync location for syncing Extracted
    Features
    '''
    libid, volid = htid.split('.', 1)
    volid_clean = id_encode(volid)
    filename = '.'.join([libid, volid_clean, 'json.bz2'])
    path = '/'.join([libid, 'pairtree_root', id2path(volid).replace('\\', '/'),
                     volid_clean, filename])
    return path

with open(sys.argv[1]) as reader:
    
    workset = json.load(reader)
    for work in workset:
        print(id_to_rsync(work["volumeIdentifier"]))
