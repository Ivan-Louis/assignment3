__author__ = 'Louis'

import os
from html_handler import handle_html
from vsmRetrieve import retrieveVsm
import whoosh.scoring as scoring
from whoosh.fields import Schema, TEXT, ID
from whoosh import qparser
import whoosh.index as index
from xml.dom import minidom
from bs4 import BeautifulSoup

#files and directories
indexDir = "../data/index"
inputDir = "../csiro-corpus"
outputBase = "../output/baseline.out"
outputImpro = "../output/improved.out"
queriesFile = "../data/queries.xml"
temp = "testdocs"

# Method for loading an xml file of queries
def loadQueries():
    queries = []
    xmldoc = minidom.parse(queriesFile)
    for query in xmldoc.getElementsByTagName("query"):
        id = query.getAttribute('id')
        text = query.firstChild.nodeValue
        queries.append({'id': id, 'text': text})

    return queries

# Creating the index. This calls the handle_html method that returns a dictionary with ID and content
# of each file under csiro-corpus
def createIndex():
    schema = Schema(id=ID(stored=True), content=TEXT)

    if not os.path.exists(indexDir):
        os.mkdir(indexDir)
    ix = index.create_in(indexDir, schema)

    writer = ix.writer(procs=2, limitmb=512, multiwite=True)

    for file in os.listdir(inputDir):
        #print(file)
        fileloc = inputDir +"/"+ file
        docs = handle_html(fileloc)
        for doc in docs:
            try:
                writer.add_document(id=doc['id'].decode(),  content=doc['content'].decode())
            except:
                writer.add_document(id=doc['id'],  content=doc['content'])

    writer.commit()
    ix.close()

# Method for making the baseline retrival of the files. Uses vector space model with TFIDF
def makeBaseline(ixDir, outFile):
    ix = index.open_dir(ixDir)

    # Use the reader to get statistics
    reader = ix.reader()
    #searcher = Searcher(reader, weighting=TF_IDF, closereader=True)
    queries = loadQueries()

    outfile = open(outFile, "w")
    field = "content"
    for query in queries:
        print("Processing query number", query['id'])
        with ix.searcher(weighting=scoring.TF_IDF()) as searcher:
            qp = qparser.QueryParser(field, schema=ix.schema)
            q = qp.parse(query['text'])

            results = searcher.search(q, limit=50)
            for r in results[:50]:
                outfile.write(query['id']+ " Q0 " + r['id'] + " " + str(r.score)[0:6] + "\n")

    outfile.close()
    ix.close()

def makeImpro(ixDir, outFile):
    ix = index.open_dir(ixDir)

    # Use the reader to get statistics
    reader = ix.reader()
    #searcher = Searcher(reader, weighting=TF_IDF, closereader=True)
    queries = loadQueries()

    outfile = open(outFile, "w")
    field = "content"
    for query in queries:
        print("Processing query number", query['id'])
        with ix.searcher(weighting=scoring.BM25F()) as searcher:
            qp = qparser.QueryParser(field, schema=ix.schema)
            q = qp.parse(query['text'])

            results = searcher.search(q, limit=50)
            for r in results[:50]:
                outfile.write(query['id']+ " Q0 " + r['id'] + " " + str(r.score)[0:6] + "\n")

    outfile.close()
    ix.close()


if __name__ == '__main__':
    #createIndex()  # note that this has to be done only once

    #makeBaseline(indexDir, outputBase)
    makeImpro(indexDir, outputImpro)
    print("done")
