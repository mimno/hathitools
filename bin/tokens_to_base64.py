import sys, base64, numpy

## First construct the vocabulary

vocabulary = []
reverse_vocabulary = {}

with open(sys.argv[1]) as vocab_file:
    for line in vocab_file:
        word = line.rstrip()
        word_id = len(vocabulary)
        vocabulary.append(word)
        reverse_vocabulary[word] = word_id

token_id_buffer = numpy.zeros(10000, dtype="u2")

## Now read the file
with open(sys.argv[2]) as docs_file, open(sys.argv[3], "w") as b64_file:
    for line in docs_file:
        (volume_id, _, text) = line.split("\t")
        tokens = text.rstrip().split(" ")

        num_valid_tokens = 0
        for token in tokens:
            if token in reverse_vocabulary:
                token_id_buffer[num_valid_tokens] = reverse_vocabulary[token]
                num_valid_tokens += 1

        b64_file.write("{}\tX\t{}\n".format(volume_id, base64.b64encode(token_id_buffer[:num_valid_tokens]).decode("ascii")))

