import ujson, subprocess, codecs, sys, glob, re, numpy, unicodedata, time
from collections import Counter

id_pattern = re.compile(".*?/(.*).json.bz2")

stoplist = set()

target_dir = sys.argv[1]
stoplist_file = sys.argv[2]

with open(stoplist_file) as stop_reader:
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
for bz2_file in glob.glob(f"{target_dir}/*.json.bz2"):

    match = id_pattern.search(bz2_file)
    if not match:
        print(f"skipping {bz2_file}")
        continue
    
    volume_id = match.group(1)
    
    bzcat_process = subprocess.Popen(["bzcat", bz2_file], stdout=subprocess.PIPE)

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
