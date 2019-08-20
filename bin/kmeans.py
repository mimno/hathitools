import numpy, sys

vocabulary = []
reverse_vocabulary = {}

num_clusters = int(sys.argv[2])

with open(sys.argv[1]) as infile:
    
    matrix_shape = [int(x) for x in infile.readline().split()]
    
    embeddings = numpy.zeros(matrix_shape)
    
    for line in infile:
        fields = line.rstrip().split()
        
        word_id = len(vocabulary)
        vocabulary.append(fields[0])
        reverse_vocabulary[fields[0]] = word_id
        
        embeddings[word_id,:] = numpy.array([float(x) for x in fields[1:]])


lengths = numpy.sqrt(numpy.sum(embeddings ** 2, axis=1))
lengths[ lengths == 0.0 ] = 1.0

embeddings /= lengths[:, numpy.newaxis]

#normalizer = 1.0 / numpy.sqrt(numpy.sum(embeddings ** 2, axis=1))
#embeddings *= normalizer[:, numpy.newaxis]

choices = numpy.random.choice(matrix_shape[0], num_clusters, replace=False)
centroids = embeddings[choices]

cosines = numpy.dot(embeddings, centroids.transpose())
nearest = numpy.argmax(cosines, axis=1)

cluster_sizes = numpy.bincount(nearest)
#print(cluster_sizes)

for iteration in range(50):
    
    ## recalculate means
    for cluster in range(num_clusters):
        centroids[cluster] = numpy.mean(embeddings[numpy.where(nearest == cluster),:], axis = 1)
    normalizer = 1.0 / numpy.sqrt(numpy.sum(centroids ** 2, axis=1))
    centroids *= normalizer[:, numpy.newaxis]
    
    ## copy nearest by value
    old_nearest = list(nearest)

    cosines = numpy.dot(embeddings, centroids.transpose())
    nearest = numpy.argmax(cosines, axis=1)
    cluster_sizes = numpy.bincount(nearest)
    #print(cluster_sizes)

with open("vocab_clusters.txt", "wt") as outfile:
    for word_id, cluster in enumerate(nearest):
        outfile.write("{}\t{}\n".format(cluster, vocabulary[word_id]))

for cluster in range(num_clusters):
    sorted_words = [vocabulary[i] for i in numpy.where(nearest == cluster)[0]]
    print("> " + " ".join(sorted_words[0:100]))
