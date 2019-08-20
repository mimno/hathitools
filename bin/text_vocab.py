from collections import Counter
import sys

word_counts = Counter()
line_num = 0

with open(sys.argv[1]) as infile:
    for line in infile:
        volume, _, text = line.split("\t")
        tokens = text.rstrip().split(" ")
        
        word_counts.update(tokens)

top_words = word_counts.most_common(2 ** 16)
print("\n".join([ w for (w, c) in top_words ]))
