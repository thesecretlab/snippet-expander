#!/usr/bin/env python

import re
import itertools
import os
import logging
from fuzzywuzzy import process

SNIP_PREFIX="// snip:"
SNIP_FILE_PREFIX="// snip-file:"
TAG_PREFIX="// tag:"

# The virtual "ref" that represents the current state of the files on disk,
# and may not necessarily be stored in the index or in a commit. Uses a
# space because these are very uncommon in tags or branch names, and not
# seen in commit hashes.
WORKSPACE_REF = "Working Copy"

class SourceDocument(object):
    """A document, containing snippets that refer to tagged code."""
    
    def __init__ (self, path):
        self.path = path
        
        with open(path, "r") as source_file:
            self.contents = source_file.read()

    @property
    def filename(self):
        return os.path.splitext(os.path.basename)[0]
        

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
        snip_with_code = re.compile("(//.*snip(\-file)*:.*\n)(\[.*\]\n)*----\n(.*\n)*?----\n")
        cleaned = re.sub(snip_with_code, r'\1', self.contents)
        return cleaned
    
    @property
    def snippets(self):
        """Returns the list of snippets in this document, as a TagQuery."""

        queries = []

        from tagged_document import TagQuery

        # start with a version of ourself that has no expanded snippets
        source_lines = self.cleaned_contents.split("\n")

        # the list of lines we're working with
        output_lines = []

        # default to working with files at the current state on disk; this
        # can change to specific refs when a // tag: instruction is
        # encountered in the document
        current_ref = WORKSPACE_REF

        for line in source_lines:
            output_lines.append(line)

            # change which tag we're looking at if we hit an instruction to
            # do so
            if line.startswith(TAG_PREFIX):
                current_ref = line[len(TAG_PREFIX)+1:].strip()

            # is this a snippet?
            if line.startswith(SNIP_PREFIX):

                # figure out what tags we're supposed to be using here
                query_text = line[len(SNIP_PREFIX)+1:]

                # build the tag query from this
                query = TagQuery(query_text, ref=current_ref)

                queries.append(query)

        return queries

    @property
    def tags_used(self):
        """Returns the set of all tags referred to in this document."""
        return set([query.all_referenced_tags for query in self.snippets])

    def render_snippet(self, query, tagged_documents):

        from tagged_document import TagQuery

        assert isinstance(query, TagQuery)

        # get the list of documents that actually exist at this point
        documents_at_current_tag = filter(None, [document[query.ref] for document in tagged_documents])

        # get the tagged lines that apply from these documents
        rendered_content = [document.query(query.query_string) for document in documents_at_current_tag]

        # any document that produced no lines will have returned None;
        # remove those
        rendered_content = filter(None, rendered_content)

        rendered_content = [content.split("\n") for content in rendered_content]

        # we now have a list of list of lines; we want to flatten this to a
        # plain list of lines
        rendered_lines = list(itertools.chain.from_iterable(rendered_content))

        rendered_lines = "\n".join(rendered_lines)

        # finally, identify and remove any chain of 2 or more empty lines,
        # replacing it with a single empty line
        empty_lines = re.compile(r"(\s*?\n){2,}")

        rendered_lines = re.sub(empty_lines, "\n\n", rendered_lines)

        return rendered_lines

        

    def render(self, tagged_documents, language=None, clean=False, show_query=True, file_getter=None):

        """Returns a tuple of (string,bool): a version of itself after expanding snippets with code found in 'tagged_documents', and True if any snippets were rendered"""
        assert isinstance(tagged_documents, list)
        assert isinstance(language, str) or language is None

        if clean:
            return self.cleaned_contents, True
        
        # start with a version of ourself that has no expanded snippets
        source_lines = self.cleaned_contents.split("\n")

        # the list of lines we're working with
        output_lines = []

        # default to working with files at HEAD
        current_ref = WORKSPACE_REF

        # true if this file rendered any snippets
        dirty = False 

        all_tags_at_current_tag = list({tag for doc in tagged_documents for tag in doc[current_ref].tags})

        snippet_count = 0

        for line in source_lines:
            output_lines.append(line)

            # change which tag we're looking at if we hit an instruction to do so
            if line.startswith(TAG_PREFIX):
                current_ref = line[len(TAG_PREFIX)+1:].strip()

                all_valid_docs_at_current_ref = [doc for doc in tagged_documents if doc[current_ref]]

                all_tags_at_current_tag = list({tag for doc in all_valid_docs_at_current_ref for tag in doc[current_ref].tags})

            # expand file snippets as we encounter them
            if line.startswith(SNIP_FILE_PREFIX):
                if not file_getter:
                    logging.warn("snip-file command used, but no file getter was provided")
                    continue

                dirty = True
                filename = line[len(SNIP_FILE_PREFIX)+1:].strip()

                file_contents = file_getter(filename)

                output_lines.append("----")
                output_lines.append(file_contents)
                output_lines.append("----")

            # expand snippets as we encounter them
            if line.startswith(SNIP_PREFIX):

                dirty = True

                # figure out what tags we're supposed to be using here
                query_text = line[len(SNIP_PREFIX)+1:]

                # get the list of documents that actually exist at this
                # point
                documents_at_current_tag = filter(None, [document[current_ref] for document in tagged_documents])

                # get the tagged lines that apply from these documents
                rendered_content = [document.query(query_text) for document in documents_at_current_tag]

                # any document that produced no lines will have returned
                # None; remove those
                rendered_content = filter(None, rendered_content)

                rendered_content = [content.split("\n") for content in rendered_content]

                # we now have a list of list of lines; we want to flatten
                # this to a plain list of lines
                rendered_lines = list(itertools.chain.from_iterable(rendered_content))

                if show_query:
                    from tagged_document import TagQuery
                    query_obj = TagQuery(query_text)
                    description = "// Snippet: {}-{}\n".format(snippet_count, query_obj.as_filename)
                    rendered_lines = [description] + rendered_lines

                if not rendered_lines:
                    # if we got no lines, we log a warning and also render
                    # out that warning in the final output (so that a
                    # proofreader can spot it)

                    # try and find some potential tags that could fit
                    from tagged_document import TagQuery

                    query = TagQuery(query_text)

                    bests = [result[0] for result in process.extractBests(query.include[0], all_tags_at_current_tag, score_cutoff=80)]
                    
                    import textwrap
                    warning = "No code found for query '{}' at ref '{}'. Possible replacement tags include: {}".format(query_text, current_ref, ", ".join(bests))
                    warning = textwrap.fill(warning, 80)
                    logging.warn("%s: %s", self.path, warning)
                    exclamations = "!" * 8
                    rendered_lines = [exclamations, warning, exclamations]
                
                # time to produce our output!

                # add the language tag if one was specified
                if language:
                    output_lines.append("[source,{}]".format(language))

                # and output the snippet
                output_lines.append("----")
                output_lines += rendered_lines
                output_lines.append("----")

                snippet_count += 1
        
        # render the output into a string
        output = "\n".join(output_lines)

        # finally, identify and remove any chain of 2 or more empty lines,
        # replacing it with a single empty line
        empty_lines = re.compile(r"(\s*?\n){2,}")

        output = re.sub(empty_lines, "\n\n", output)

        
        return output, dirty



                




