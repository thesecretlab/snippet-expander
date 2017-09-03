#!/usr/bin/env python


import git
from tagged_document import TaggedDocument
from source_document import SourceDocument
import logging
import optparse
import sys

class Processor(object):
    
    def __init__(self, source_path, tagged_path, source_extensions=["txt"], tagged_extensions=["swift"], language=None):
        assert isinstance(source_path, str)
        assert isinstance(tagged_path, str)
        

        self.repo = git.Repo(tagged_path)

        self.tagged_documents = TaggedDocument.find(self.repo, tagged_extensions)
        self.source_documents = SourceDocument.find(source_path, source_extensions)

        self.language = language
    
    def process(self, dry_run=False, suffix=""):

        for doc in self.source_documents:
            assert isinstance(doc, SourceDocument)

            rendered_source = doc.render(self.tagged_documents, language=self.language)

            if dry_run:
                logging.info("Would write %s", doc.path)
            else:
                with open(doc.path + suffix, "w") as output_file:
                    output_file.write(rendered_source)
                logging.info("%s", doc.path)



    
def main():
    options = optparse.OptionParser("%prog [options] asciidoc_dir sourcecode_dir")

    options.add_option("-l", "--lang", dest="language", default="swift")

    (opts, args) = options.parse_args()

    if len(args) != 2:
        options.print_usage()
        sys.exit(1)
    
    opts.source_dir = args[0]
    opts.code_dir = args[1]

    processor = Processor(opts.source_dir, opts.code_dir,source_extensions=["txt","asciidoc"], tagged_extensions=["swift","txt"])

    processor.process()

if __name__ == '__main__':
    main()
