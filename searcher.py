import Stemmer
import json
import os
from pyparsing import Word, infixNotation, opAssoc, alphas, nums
import sys
import re
import common
import xml.etree.ElementTree as ET


def unite_lists(l1, l2, extract=lambda x: x, merge=lambda x, y: x):
    i = 0
    j = 0
    n = len(l1)
    m = len(l2)
    res = []
    while i < n and j < m:
        x = extract(l1[i])
        y = extract(l2[j])
        if x < y:
            res.append(l1[i])
            i += 1
        elif x == y:
            res.append(merge(l1[i], l2[j]))
            i += 1
            j += 1
        else:
            res.append(l2[j])
            j += 1
    while i < n:
        res.append(l1[i])
        i += 1
    while j < m:
        res.append(l2[j])
        i += 1
    return res


def intersect_lists(l1, l2, extract=lambda x: x, merge=lambda x, y: x):
    i = 0
    j = 0
    n = len(l1)
    m = len(l2)
    res = []
    while i < n and j < m:
        x = extract(l1[i])
        y = extract(l2[j])
        if x < y:
            i += 1
        elif x == y:
            res.append(merge(l1[i], l2[j]))
            i += 1
            j += 1
        else:
            j += 1
    return res


def subtract_lists(l1, l2, extract=lambda x: x):
    i = 0
    j = 0
    n = len(l1)
    m = len(l2)
    res = []
    while i < n and j < m:
        x = extract(l1[i])
        y = extract(l2[j])
        if x < y:
            res.append(l1[i])
            i += 1
        elif x == y:
            i += 1
            j += 1
        else:
            j += 1
    while i < n:
        res.append(l1[i])
        i += 1
    return res


def find(s):
    if ' ' in s:
        return reduce(intersect, (find(word) for word in s.split()))
    else:
        s = _stemmer.stemWord(s)
        if not s or s in _stopwords or s not in index:
            return [], False
        return index[s], True


def intersect((l1, f1), (l2, f2)):
    if not f1:
        l1, l2 = l2, l1
    if f1 and f2:
        return intersect_lists(l1, l2, __extract, __merge_intersect), True
    elif f1:
        return subtract_lists(l1, l2, __extract), True
    else:
        return unite_lists(l1, l2, __extract, __merge_unite), False


def unite((l1, f1), (l2, f2)):
    if not f1:
        l1, l2 = l2, l1
    if f1 and f2:
        return unite_lists(l1, l2, __extract, __merge_unite), True
    elif f1:
        return subtract_lists(l2, l1, __extract), False
    else:
        return intersect_lists(l1, l2, __extract, __merge_intersect), False


__extract = lambda x: x[0]
__merge_unite = lambda x, y: (x[0], unite_lists(x[1], y[1]))
__merge_intersect = lambda x, y: (x[0], intersect_lists(x[1], y[1]))


class Term(object):
    def __init__(self, t):
        self.text = t[0].strip()

    def eval(self):
        return find(self.text)


class BinOp(object):
    def __init__(self, t):
        self.args = t[0][0::2]


class And(BinOp):
    def eval(self):
        return intersect(self.args[0].eval(), self.args[1].eval())


class Or(BinOp):
    def eval(self):
        return unite(self.args[0].eval(), self.args[1].eval())


class Not(object):
    def __init__(self, t):
        self.arg = t[0][1]

    def eval(self):
        l, f = self.arg.eval()
        return l, not f


def print_snippet(entry):
    doc = docs[entry[0]]
    print doc
    if os.path.isfile(doc):
        try:
            tree = ET.parse(doc)
            text = tree.find('text')
            if text is not None:
                body = text.find('body')
                if body is not None:
                    if entry[1]:
                        n = entry[1][0]
                        for p in body:
                            if int(p.get('n')) == n:
                                print p.text
                                break
                    else:
                        head = body.find('head')
                        if head is not None:
                            print head.text
        except ET.ParseError:
            pass
    print


def search(query):
    query = ' '.join(word.lower() for word in re.findall('[\w\'()]+', query))
    query = replace_operators(query)

    term = Word(alphas + nums + "'")
    term.setParseAction(Term)
    expr = infixNotation(term,
                         [
                             ("~", 1, opAssoc.RIGHT, Not),
                             ("&", 2, opAssoc.LEFT, And),
                             ("|", 2, opAssoc.LEFT, Or),
                         ])
    expr_tree = expr.parseString(query)[0]
    res = expr_tree.eval()
    if res[1]:
        for entry in res[0]:
            print_snippet(entry)


with open('docs.dat') as _f:
    docs = json.load(_f)
with open('terms.dat') as _f:
    index = json.load(_f)
_stopwords = common.read_stopwords('stopwords.txt')
_stemmer = Stemmer.Stemmer('english')


def replace_operators(s):
    s = re.sub(r'not(\W)', r'~\1', s)
    s = re.sub(r'(\W)and(\W)', r'\1&\2', s)
    s = re.sub(r'(\W)or(\W)', r'\1|\2', s)
    s = s.replace('(', ' (')

    s = re.sub(r'([\w\')]+) +(?!(&|\|))', r'\1 & ', s)
    return s

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage:\n\tpython searcher.py <query>"
        sys.exit(1)

    search(sys.argv[1])
