import sys, numpy

def read_vectors(filename):
    model = {}
    
    with open(filename) as infile:
        model["vocabulary"] = []
        model["reverse_vocabulary"] = {}
        
        matrix_shape = [int(x) for x in infile.readline().split()]
    
        model["embeddings"] = numpy.zeros(matrix_shape)
        
        for line in infile:
            fields = line.rstrip().split()
        
            word_id = len(model["vocabulary"])
            model["vocabulary"].append(fields[0])
            model["reverse_vocabulary"][fields[0]] = word_id
        
            model["embeddings"][word_id,:] = numpy.array([float(x) for x in fields[1:]])
            
    return model

model = read_vectors(sys.argv[1])
embeddings = model["embeddings"]

lengths = numpy.sqrt(numpy.sum(embeddings ** 2, axis=1))
lengths[ lengths == 0.0 ] = 1.0

embeddings /= lengths[:, numpy.newaxis]

for query_word in sys.argv[2:]:
    query_id = model["reverse_vocabulary"][query_word]
    scores = numpy.dot(embeddings, embeddings[query_id,:])
    sorted_list = sorted(list(zip(scores, model["vocabulary"])), reverse=True)
    
    for score, word in sorted_list[0:20]:
        print("{:.3f}\t{}".format(score, word))
