import numpy, sys, base64

num_dimensions = 100

b64_file = sys.argv[1]
vocab_file = sys.argv[2]

vocabulary = []
reverse_vocabulary = {}

with open(vocab_file) as vocab_file:
    for word in vocab_file:
        word = word.rstrip()
        reverse_vocabulary[word] = len(vocabulary)
        vocabulary.append(word)

projection_matrix = numpy.random.normal(0, 1, (len(vocabulary), num_dimensions))
projection_matrix, R = numpy.linalg.qr(projection_matrix, mode="reduced")

old_r_diagonal = numpy.abs(numpy.diag(R))

for iteration in range(10):
    with open(b64_file) as docs_file:
    
        new_matrix = numpy.zeros((len(vocabulary), num_dimensions))
    
        line_num = 0
    
        for line in docs_file:
            volume_id, _, b64_string = line.split("\t")
            word_ids = numpy.frombuffer(base64.b64decode(b64_string.rstrip().encode("ascii")), dtype="uint16")
        
            row_sums = numpy.sum(projection_matrix[word_ids,:], axis=0)
            new_matrix[word_ids,:] += row_sums
        
            line_num += 1
            if line_num % 10000 == 0:
                print(line_num)

    new_projection_matrix, new_R = numpy.linalg.qr(new_matrix, mode="reduced")
    
    r_diagonal = numpy.abs(numpy.diag(new_R))
    
    ordered_column_indices = numpy.flip(numpy.argsort(r_diagonal))
    r_diagonal = r_diagonal[ordered_column_indices]
    #print(r_diagonal[:15])
    diff = numpy.sum((r_diagonal - old_r_diagonal) ** 2)
    print(diff, numpy.sum(r_diagonal[:15]))
    
    projection_matrix = new_projection_matrix[:, ordered_column_indices]
    #projection_matrix = new_projection_matrix
    old_r_diagonal = r_diagonal

with open("embeddings.txt", "wt") as outfile:
    outfile.write("{} {}\n".format(len(vocabulary), num_dimensions))
    for word_id, word in enumerate(vocabulary):
        if word == "":
            word = "XXXXX"
        outfile.write("{} {}\n".format(word, " ".join([str(x) for x in projection_matrix[word_id,:]])))
