"""A simple search engine in python."""

import re, pathlib, collections, array, struct, csv, math, os


# === Phase 1: Split text into words

def words(text):
    return re.findall(r"\w+", text.lower())


# === Phase 2: Create an index

Document = collections.namedtuple("Document", "filename size")
Hit = collections.namedtuple("Hit", "doc_id offsets")
Fileoffsets = collections.namedtuple("Fileoffsets", "filename offsets")

def make_index(dir):
    print("inside make_index")
    dir = pathlib.Path(dir)
    tiny_dir = dir / ".tiny"
    tiny_dir.mkdir(exist_ok=True)

    # Build the index in memory.
    documents = []
    index = collections.defaultdict(list)  # {str: [Hit]}
    terms = {}  # {str: (int, int)}

    for path in dir.glob("**/*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        doc_words = words(text)
        doc = Document(path.relative_to(dir), len(doc_words))
        doc_id = len(documents)
        documents.append(doc)

        # Build an index for this one document.
        doc_index = collections.defaultdict(
            lambda: Hit(doc_id, array.array('I')))
        for i, word in enumerate(words(text)):
            doc_index[word].offsets.append(i)

        # Merge that into the big index.
        for word, hit in doc_index.items():
            index[word].append(hit)

    # Save the document list.
    with (tiny_dir / "documents.csv").open('w', encoding="utf-8") as f:
        out = csv.writer(f)
        for doc in documents:
            print("document",doc)
            out.writerow(doc)

    # Save the index itself.
    with (tiny_dir / "index.dat").open('wb') as f:
        start = 0
        for word, hits in index.items():
            bytes = b""
            for hit in hits:
                bytes += struct.pack("=II",
                                     hit.doc_id,
                                     len(hit.offsets))
                bytes += hit.offsets.tobytes()
            f.write(bytes)
            terms[word] = (start, len(bytes))
            start += len(bytes)

    # Save the table of terms.
    with (tiny_dir / "terms.csv").open('w',  encoding="utf-8") as f:
        out = csv.writer(f)
        for word, (start, length) in terms.items():
            out.writerow([word, start, length])


# === Phase 3: Querying the index

class Index:
    """Object for querying a .tiny index."""

    def __init__(self, dir):
        """Create an Index that reads `$DIR/.tiny`."""
        dir = pathlib.Path(dir)
        tiny_dir = dir / ".tiny"
        self.dir = dir
        self.index_file = tiny_dir / "index.dat"
        print("inside constructor",tiny_dir) 
        self.documents = []
        #for [line, max_tf] in csv.reader((tiny_dir / "documents.csv").open('r')):
           # self.documents.append(Document(pathlib.Path(line), int(max_tf)))
        for [line,max_tf] in csv.reader((tiny_dir / "documents.csv").open('r')):
              self.documents.append(Document(pathlib.Path(line), int(max_tf)))   
            #print(" from document.csv",line,max_tf)
       
        self.terms = {}
        for word, start, length in csv.reader((tiny_dir / "terms.csv").open('r')):
            self.terms[word] = (int(start), int(length))
        
    def lookup(self, word):
        """Return a list of Hits for the given word."""
        if word not in self.terms:
            return []

        start, length = self.terms[word]
        with self.index_file.open('rb') as f:
            f.seek(start)
            bytes = f.read(length)

        read_pos = 0
        hits = []
        while read_pos < len(bytes):
            doc_id, hit_count = struct.unpack("=II", bytes[read_pos:read_pos+8])
            read_pos += 8
            offset_bytes = bytes[read_pos:read_pos + 4 * hit_count]
            read_pos += 4 * hit_count
            offsets = array.array('I')
            offsets.frombytes(offset_bytes)
            hits.append(Hit(doc_id, offsets))
        assert read_pos == len(bytes)
        return hits

    def search(self, query, sampledir):
        """Find documents matching the given query.

        Return a list of (document, score) pairs."""
        dir = pathlib.Path(sampledir)
        tiny_dir = dir / ".tiny"
        tiny_dir.mkdir(exist_ok=True)
        scores = collections.defaultdict(float)
        offsets = []
        for word in words(query):
            #print("word",word)
            hits = self.lookup(word)
               
            if hits:
                df = len(hits) / len(self.documents)
                idf = math.log(1 / df)
                for hit in hits:
                    #print(self.documents[hit.doc_id].filename)
                    fname = self.documents[hit.doc_id].filename
                    #print(hit.offsets)
                    offsets.append(Fileoffsets(fname, hit.offsets))
                    tf = 1000 * len(hit.offsets) / self.documents[hit.doc_id].size
                    scores[hit.doc_id] += tf * idf
        print("fname offsets", offsets)
        results = sorted(scores.items(),
                         key=lambda pair: pair[1],
                         reverse=True)
        #print("results",results)
        abs_path = os.getcwd()
        #print("abs path", abs_path)
        line_number = "Phrase not found"
       # file = open(tiny_dir/"**/*.txt","r")
        for path in dir.glob("**/*.txt"): 
            #print("path",path)
            abs_file_path = os.path.join(abs_path, path)
            #print("abs file path", abs_file_path)
            with open(path) as file:
            #file = open(abs_file_path)
                try:
                    content = file.readlines()
                    #print(content)
                    #index = [x for x in range(len(content)) if query in content[x].lower()]
                    index = content.index(query) 
                    #for number, line in enumerate(file):
                        #if query in line:
                            #line_number = number
                            #break
                            #print(line,line_number)
                    print(index)        
                except:
                    continue
        return offsets
        #return [(self.documents[doc_id], line_number)
                #for doc_id, line_number in results[:10]]



