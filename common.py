def read_stopwords(filename):
    words = set()
    with open(filename) as f:
        for word in f.readlines():
            words.add(word.strip())
    return words
