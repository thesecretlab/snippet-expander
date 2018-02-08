#!/usr/bin/env python


import git
from tagged_document import TaggedDocument
from source_document import SourceDocument
import logging
import optparse
import sys

SOURCE_FILE_EXTENSIONS = [
    "swift",
    "txt",
    "cs"
]

class Processor(object):
    
    def __init__(self, source_path, tagged_path, source_extensions=["txt"], tagged_extensions=["swift"], language=None, clean=False):
        assert isinstance(source_path, str)
        assert isinstance(tagged_path, str)
        

        self.repo = git.Repo(tagged_path)

        self.tagged_documents = TaggedDocument.find(self.repo, tagged_extensions)
        self.source_documents = SourceDocument.find(source_path, source_extensions)
        self.clean = clean

        self.language = language
    
    def process(self, dry_run=False, suffix=""):

        for doc in self.source_documents:
            assert isinstance(doc, SourceDocument)

            rendered_source = doc.render(self.tagged_documents, language=self.language, clean=self.clean)

            if dry_run:
                logging.info("Would write %s", doc.path)
            else:
                with open(doc.path + suffix, "w") as output_file:
                    output_file.write(rendered_source)
                logging.info("Writing %s", doc.path)
    
    def find_multiply_defined_tags(self):

        from itertools import combinations
        from collections import defaultdict

        duplicate_tags = defaultdict(set)

        tag_groups = {doc.path: doc["HEAD"].tags for doc in self.tagged_documents}

        for group_pair_keys in combinations(tag_groups, 2):

            tags_in_both = tag_groups[group_pair_keys[0]] & tag_groups[group_pair_keys[1]]

            for tag in tags_in_both:
                duplicate_tags[tag].add(group_pair_keys[0])
                duplicate_tags[tag].add(group_pair_keys[1])
        
        logging.debug("\nChecking for multiple tag definitions.")
            
        for tag in duplicate_tags:
            
            doc_list = []

            for doc in duplicate_tags[tag]:
                doc_list.append(" - {0}\n".format(doc))
            
            
            logging.warn("Tag '{0}' is defined in multiple files:\n{1}".format(tag, "".join(doc_list)))

            referenced_doc = [source_document for source_document in self.source_documents if tag in source_document.tags_used]

            ref_list = []

            for ref in referenced_doc:
                ref_list.append("\t - {0}\n".format(ref.path))

            logging.warn("\t'{0}' is used in documents:\n{1}".format(tag, "".join(ref_list)))





    
def main():
    options = optparse.OptionParser("%prog [options] asciidoc_dir sourcecode_dir")

    options.add_option("-l", "--lang", dest="language", default="swift")
    options.add_option("-n", "--dry-run", action="store_true", help="Don't actually modify any files")
    options.add_option("--clean", action="store_true", help="Remove snippets from files")
    options.add_option("--suffix", default="", help="Append this to the file name of written files (default=none)")

    (opts, args) = options.parse_args()

    if len(args) != 2:
        options.print_usage()
        sys.exit(1)
    
    opts.source_dir = args[0]
    opts.code_dir = args[1]

    logging.getLogger().setLevel(logging.INFO)

    processor = Processor(opts.source_dir, opts.code_dir,source_extensions=["txt","asciidoc"], tagged_extensions=SOURCE_FILE_EXTENSIONS, language=opts.language, clean=opts.clean)

    logging.debug("Found %i source files:", len(processor.source_documents))
    for doc in processor.source_documents:
        logging.debug(" - %s", doc.path)
    
    logging.debug("Found %i code files:", len(processor.tagged_documents))
    for doc in processor.tagged_documents:
        logging.debug(" - %s", doc.path)

    processor.find_multiply_defined_tags()
    
    processor.process(dry_run=opts.dry_run, suffix=opts.suffix)

if __name__ == '__main__':
    main()
