import Stemmer
import sys
import os
import re
import json

import common
import xml.etree.ElementTree as ET


def parse_file(path):
    data = {}
    tree = ET.parse(path)

    text = tree.find('text')
    if text is not None:
        body = text.find('body')
        if body is not None:
            for p in body:
                data[int(p.get('n'))] = p.text
    return data


def build_index(inputDir):
    stemmer = Stemmer.Stemmer('english')
    stopwords = common.read_stopwords('stopwords.txt')

    docs = []
    index = {}
    tokens = 0

    for dirName, subdirList, fileList in os.walk(inputDir):
        for fileName in fileList:
            if fileName.endswith('.xml'):
                path = os.path.join(dirName, fileName)
                try:
                    data = parse_file(path)
                except ET.ParseError:
                    continue
                doc_id = len(docs)
                docs.append(path)
                for n in data:
                    text = data[n]
                    for word in re.findall('[\w\']+', text):
                        word = stemmer.stemWord(word).lower()
                        if not word or word in stopwords:
                            continue
                        tokens += 1
                        if word in index:
                            word_entries = index[word]
                        else:
                            word_entries = []
                            index[word] = word_entries

                        if not word_entries or word_entries[len(word_entries) - 1][0] != doc_id:
                            word_entries.append((doc_id, {n}))
                        else:
                            word_entries[len(word_entries) - 1][1].add(n)
    for word in index:
        word_entries = index[word]
        for i in range(len(word_entries)):
            word_entries[i] = (word_entries[i][0], sorted(word_entries[i][1]))
    with open('docs.dat', 'w') as of:
        json.dump(docs, of)
    with open('terms.dat', 'w') as of:
        json.dump(index, of)
    print "Tokens: {}".format(tokens)
    print "Terms: {}".format(len(index))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage:\n\tpython indexer.py <input dir>"
        sys.exit(1)

    build_index(sys.argv[1])
