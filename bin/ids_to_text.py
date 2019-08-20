import ujson, subprocess, codecs, sys, glob, re, numpy, unicodedata, time
from collections import Counter

tranche_pattern = re.compile(r"/(..)/(....).ids")

id_tranches = {}

stoplist = set()

with open(sys.argv[1]) as target_reader:
    for line in target_reader:
        line = line.rstrip().replace(":", "+").replace("/", "=")
        id_tranches[line] = False

with open(sys.argv[2]) as ids_reader:
    for line in ids_reader:
        fields = line.rstrip().split("\t")
        if fields[0] in id_tranches:
            id_tranches[ fields[0] ] = fields[1]

if len(sys.argv) == 4:
    with open(sys.argv[3]) as stop_reader:
        for line in stop_reader:
            stoplist.add(line.rstrip())

def strip_punctuation(s):
    start = 0
    end = len(s)
    while unicodedata.category(s[start])[0] != "L":
        start += 1
        if start == end:
            return ""
    while unicodedata.category(s[end-1])[0] != "L":
        end -= 1
    return s[start:end]

# read each file and look through each page
for volume_id in id_tranches:
    # ignore ids not found
    if not id_tranches[volume_id]:
        continue

    tranche_match = tranche_pattern.search( id_tranches[volume_id] )
    if not tranche_match:
        continue
    
    tranche = tranche_match.group(1) ## two digit group id
    file_id = tranche_match.group(2) ## four digit group id

    bz2_file = "{}/{}.json.bz2".format(file_id, volume_id)
            
    tar_process = subprocess.Popen(["tar","xfO","features/{}/{}.tar".format(tranche, file_id),bz2_file],stdout=subprocess.PIPE)
    bzcat_process = subprocess.Popen(["bzcat"], stdin=tar_process.stdout,stdout=subprocess.PIPE)
    tar_process.stdout.close()

    try:
        bookdata = ujson.loads(bzcat_process.communicate()[0])
        
        book_counter = Counter()
        
        for page in bookdata["features"]["pages"]:
            if page["sentenceCount"] >= 5:
                word_counts = page["body"]["tokenPosCount"]
                tokens = word_counts.keys()
                output = []
                
                if len(tokens) >= 10:
                    for i, token in enumerate(tokens):
                        #print(token),
                        norm_token = strip_punctuation(token.lower().strip())
                        if len(token) >= 3 and norm_token not in stoplist:
                            pos_counts = sum(word_counts[token].values())
                            
                            output.append(norm_token)

                print("{}\tX\t{}".format(volume_id, " ".join(output)))
        
    except ValueError as e:
        print("Unable to read {}".format(e))
