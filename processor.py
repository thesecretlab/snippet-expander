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

    logging.info("Found %i source files:", len(processor.source_documents))
    for doc in processor.source_documents:
        logging.info(" - %s", doc.path)
    
    logging.info("Found %i code files:", len(processor.tagged_documents))
    for doc in processor.tagged_documents:
        logging.info(" - %s", doc.path)
    
    processor.process(dry_run=opts.dry_run, suffix=opts.suffix)

if __name__ == '__main__':
    main()
