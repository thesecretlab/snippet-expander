#!/usr/bin/env python


import git
from gooey import Gooey, GooeyParser
from tagged_document import TaggedDocument, TagQuery
from source_document import SourceDocument
import logging
from argparse import ArgumentParser
import sys
import os

from source_document import WORKSPACE_REF

SOURCE_FILE_EXTENSIONS = [
    "swift",
    "txt",
    "cs",
    "py"
]

class Processor(object):
    
    def __init__(self, source_path, tagged_path, source_extensions=["txt"], tagged_extensions=["swift"], language=None, clean=False, expand_images=False, show_query=False, as_inline_list_items=False):
        assert isinstance(source_path, str)
        assert isinstance(tagged_path, str)
        

        self.repo = git.Repo(tagged_path)

        self.tagged_documents = TaggedDocument.find(self.repo, tagged_extensions)
        self.source_documents = SourceDocument.find(source_path, source_extensions)
        self.clean = clean

        self.language = language

        self.expand_images = expand_images

        self.show_query = show_query

        self.as_inline_list_items = as_inline_list_items
    
    def get_file_contents(self, name):

        for root, dirs, files in os.walk(self.repo.working_dir):
            
            for file in files:                
                if file == name:
                    path = os.path.join(root, file)
                    return open(path).read()
        
        logging.error("Failed to find %s", name)
    
    def process(self, dry_run=False, suffix=""):

        file_getter = lambda name: self.get_file_contents(name)

        for doc in self.source_documents:
            assert isinstance(doc, SourceDocument)
            rendered_source, dirty = doc.render(
                self.tagged_documents, 
                language=self.language, 
                clean=self.clean, 
                file_getter=file_getter,
                show_query=self.show_query,
                as_inline_list_items=self.as_inline_list_items
                )

            if dirty:
                if dry_run:
                    logging.info("Would write %s", doc.path)
                else:
                    with open(doc.path + suffix, "w") as output_file:
                        output_file.write(rendered_source)
                    logging.info("Writing %s", doc.path)
    
    def extract_snippets(self, extract_dir):
        if os.path.isdir(extract_dir) == False:
            logging.error("%s is not a directory.", extract_dir)
            return

        use_file_prefix = len(self.source_documents) > 1
        
        for doc in self.source_documents:

            for (count, snippet) in enumerate(doc.snippets):

                assert isinstance(snippet, TagQuery)

                filename = "{}-{}".format(count, snippet.as_filename)

                if use_file_prefix:
                    filename = "{}_{}".format(doc.filename, filename)

                dest_path = os.path.join(extract_dir,filename)

                output = doc.render_snippet(snippet, self.tagged_documents)

                with open(dest_path, "w") as f:
                    f.write(output)


    def find_overlong_lines(self, limit):
        import itertools
        all_long_lines = itertools.chain(*[doc[WORKSPACE_REF].lines_over_limit(limit) for doc in self.tagged_documents])

        for line in all_long_lines:
            logging.info("Line too long: %s:%i (%i > %i)", line.source_name, line.line_number, len(line.text), limit)


    
    def find_multiply_defined_tags(self):

        from itertools import combinations
        from collections import defaultdict

        duplicate_tags = defaultdict(set)

        docs_at_head = filter(lambda d: d[WORKSPACE_REF], self.tagged_documents)

        tag_groups = {doc.path: doc[WORKSPACE_REF].tags for doc in self.tagged_documents}

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


@Gooey(
    program_name="Snippet Processor",
    tabbed_groups=True
)
def main():
    options = GooeyParser()

    options.add_argument("source_dir", help="Path to the directory containing your book's source text.", widget="DirChooser")
    options.add_argument("code_dir", help="Path to the git repo containing source code.", widget="DirChooser")

    
    options.add_argument("-l", "--lang", dest="language", help="Indicate that the source code is in this language when syntax highlighting", default="swift")
    options.add_argument("-n", "--dry-run", action="store_true", help="Don't actually modify any files")
    options.add_argument("--clean", action="store_true", help="Remove snippets from files, instead of adding their contents to files")
    options.add_argument("--length", default=75, help="The maximum length permitted for snippet lines. Lines longer than this will be warned about.")

    advanced_options = options.add_argument_group("Advanced Options")

    
    advanced_options.add_argument("--suffix", default="", help="Append this to the file name of written files (default=none)")
    advanced_options.add_argument("-x", "--extract-snippets", dest="extract_dir", default=None, help="Render each snippet to a file, and store it in this directory.", widget="DirChooser")
    advanced_options.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    advanced_options.add_argument("-q", "--show_query", action="store_true", help="Include the query in rendered snippets.")
    advanced_options.add_argument("--as_inline_list_items", action="store_true", help="Add a + after the snippet tag, to make the snippets format properly when being used as inline blocks in list items")
    #options.add_argument("-i", "--expand-images", action="store_true", help="Expand img: shortcuts (CURRENTLY BROKEN!)")

    
    
    opts = options.parse_args()
    
    logging.getLogger().setLevel(logging.INFO)

    if opts.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    processor = Processor(
        opts.source_dir, 
        opts.code_dir,
        source_extensions=["txt","asciidoc"],
        tagged_extensions=SOURCE_FILE_EXTENSIONS, 
        language=opts.language, 
        clean=opts.clean, 
        show_query=opts.show_query,
        as_inline_list_items=opts.as_inline_list_items)

    logging.debug("Found %i source files:", len(processor.source_documents))
    for doc in processor.source_documents:
        logging.debug(" - %s", doc.path)
    
    logging.debug("Found %i code files:", len(processor.tagged_documents))
    for doc in processor.tagged_documents:
        logging.debug(" - %s", doc.path)

    processor.find_multiply_defined_tags()

    processor.find_overlong_lines(opts.length)
    
    processor.process(dry_run=opts.dry_run, suffix=opts.suffix)

    if opts.extract_dir:
        processor.extract_snippets(opts.extract_dir)

    
if __name__ == '__main__':
    main()
