#!/usr/bin/env python

import re
import itertools

SNIP_PREFIX="// snip:"
TAG_PREFIX="// tag:"

class SourceDocument(object):
    """A document, containing snippets that refer to tagged code."""
    
    def __init__ (self, path):
        self.path = path
        
        with open(path, "r") as source_file:
            self.contents = source_file.read()

        

    @property 
    def cleaned_contents(self):
        """Returns a version of 'text' that has no expanded snippets."""
        snip_with_code = re.compile("(//.*snip:.*\n)(\[.*\]\n)*----\n(.*\n)*?----\n")
        cleaned = re.sub(snip_with_code, r'\1', self.contents)
        return cleaned

    def render(self, tagged_documents):

        """Returns a version of itself after expanding snippets with code found in 'tagged_documents'"""
        assert isinstance(tagged_documents, list)

        source_lines = self.cleaned_contents.split("\n")

        output_lines = []

        current_ref = "HEAD"

        for line in source_lines:
            output_lines.append(line)

            # change which tag we're looking at if we hit an instruction to do so
            if line.startswith(TAG_PREFIX):
                current_ref = line[len(TAG_PREFIX):].strip()

            # expand snippets as we encounter them
            if line.startswith(SNIP_PREFIX):
                output_lines.append("----")

                query_text = line[len(SNIP_PREFIX):]

                documents_at_current_tag = filter(None, [document[current_ref] for document in tagged_documents])

                rendered_content = [document.query(query_text).split("\n") for document in documents_at_current_tag]

                rendered_content = filter(None, rendered_content)

                # we have a list of list of lines; we want to flatten this to a plain list of lines
                rendered_lines = itertools.chain.from_iterable(rendered_content)

                output_lines += rendered_lines

                output_lines.append("----")
        
        # render the output
        output = "\n".join(output_lines)

        return output



                




