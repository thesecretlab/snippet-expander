#!/usr/bin/env python

import re
import itertools
import os
import logging

SNIP_PREFIX="// snip:"
TAG_PREFIX="// tag:"

class SourceDocument(object):
    """A document, containing snippets that refer to tagged code."""
    
    def __init__ (self, path):
        self.path = path
        
        with open(path, "r") as source_file:
            self.contents = source_file.read()

    @staticmethod
    def find(base_path, extensions):
        assert isinstance(base_path, str)
        assert isinstance(extensions, list)

        documents = []

        starting_dir = base_path

        for (path, dirs, files) in os.walk(starting_dir):
            
            for filename in files:
                for extension in extensions:
                    if filename.endswith("."+extension):
                        file_path = path+os.path.sep+filename

                        if ".git" in file_path:
                            continue

                        
                        documents.append(SourceDocument(file_path))
        
        return documents  

    @property 
    def cleaned_contents(self):
        """Returns a version of 'text' that has no expanded snippets."""
        snip_with_code = re.compile("(//.*snip:.*\n)(\[.*\]\n)*----\n(.*\n)*?----\n")
        cleaned = re.sub(snip_with_code, r'\1', self.contents)
        return cleaned

    def render(self, tagged_documents, language=None):

        """Returns a version of itself after expanding snippets with code found in 'tagged_documents'"""
        assert isinstance(tagged_documents, list)
        assert isinstance(language, str) or language is None

        # start with a version of ourself that has no expanded snippets
        source_lines = self.cleaned_contents.split("\n")

        # the list of lines we're working with
        output_lines = []

        # default to working with files at HEAD
        current_ref = "HEAD"

        for line in source_lines:
            output_lines.append(line)

            # change which tag we're looking at if we hit an instruction to do so
            if line.startswith(TAG_PREFIX):
                current_ref = line[len(TAG_PREFIX)+1:].strip()

            # expand snippets as we encounter them
            if line.startswith(SNIP_PREFIX):

                # figure out what tags we're supposed to be using here
                query_text = line[len(SNIP_PREFIX)+1:]

                # get the list of documents that actually exist at this point
                documents_at_current_tag = filter(None, [document[current_ref] for document in tagged_documents])

                # get the tagged lines that apply from these documents
                rendered_content = [document.query(query_text) for document in documents_at_current_tag]

                # any document that produced no lines will have returned None; remove those
                rendered_content = filter(None, rendered_content)

                rendered_content = [content.split("\n") for content in rendered_content]

                
                # we now have a list of list of lines; we want to flatten this to a plain list of lines
                rendered_lines = list(itertools.chain.from_iterable(rendered_content))

                if not rendered_lines:
                    logging.warn("%s: No code found for query '%s'", self.path, query_text)
                else:
                    # time to produce our output!

                    # add the language tag if one was specified
                    if language:
                        output_lines.append("[source,{}]".format(language))

                    # and output the snippet
                    output_lines.append("----")
                    output_lines += rendered_lines
                    output_lines.append("----")
        
        # render the output into a string; we're done!
        output = "\n".join(output_lines)

        return output



                




