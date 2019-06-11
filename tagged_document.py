#!/usr/bin/env python

import git
import re
import copy
import logging
from six import StringIO
import textwrap
import os

from source_document import WORKSPACE_REF

class TaggedDocument(object):
    """A document containing tagged regions."""

    @staticmethod
    def find(repo, extensions):
        assert isinstance(repo, git.Repo)
        assert isinstance(extensions, list)

        documents = []

        starting_dir = repo.working_dir

        for (path, dirs, files) in os.walk(starting_dir):
            
            for filename in files:
                for extension in extensions:
                    if filename.endswith("."+extension):
                        file_path = path+os.path.sep+filename

                        if ".git" in path:
                            continue

                        if "old" in path:
                            continue

                        path_relative_to_repo = os.path.relpath(file_path, starting_dir)

                        # if this path happens to be in the repo, then we add it to the
                        # documents we're using
                        logging.debug("Adding %s", path_relative_to_repo)

                        documents.append(TaggedDocument(repo, path_relative_to_repo))                        
                        
                            

                        
        if len(documents) == 0:
            logging.warn("No tagged documents were found.")
        return documents
        
        

    def __init__(self, repo, path):
        assert isinstance(repo, git.Repo)
        assert isinstance(path, str)
        self.path = path.replace(os.sep, "/")
        self.versions = {} # maps git refs to TaggedDocumentVersion objects
        self.repo = repo

        # Add the current-on-disk version
        path_on_disk = os.path.join(repo.working_dir, path)
        with open(path_on_disk) as file_on_disk:
            data_on_disk = file_on_disk.read()
            self.versions[WORKSPACE_REF] = TaggedDocumentVersion(self.path, data_on_disk, WORKSPACE_REF)
        
    
    def __getitem__(self, revision):
        """Gets the version of this document at a specified revision (ie commit number, tag or other ref)"""

        assert isinstance(revision, str)
        
        try:
            version = self.versions[revision]
        except KeyError:
            # attempt to get the file at this path, at this version
            try:
                # get the data of the file at this ref; may raise KeyError
                data = self.repo.tree(revision)[self.path].data_stream.read()

                # create the version from this data
                version = TaggedDocumentVersion(self.path, data, revision)

                # cache it
                self.versions[revision] = version
            except KeyError:
                # there's no commit of this type in the repo at this name
                return None

        assert isinstance(version, TaggedDocumentVersion) 

        return self.versions[revision]

class TaggedDocumentVersion(object):
    """A specific version of a tagged document."""

    def __init__(self, path, data, version):
        self.path = path
        self.data = data.replace(b"\r", b"")
        self.version = version
        self.lines = []

        self.parse_lines(self.data)

        logging.debug("Loaded %s (%i lines)", self.path, len(self.lines))

    @property
    def tags(self):

        tags = set()

        for line in self.lines:

            assert isinstance(line, TaggedLine)

            tags = tags.union(set(line.tags))
        
        # return the set of all tags in this document
        return tags

    
    def query(self, query_string):
        """Given a query string, returns the lines of text that match the specified query."""

        assert isinstance(query_string, str)

        query = TagQuery(query_string)

        has_content = False

        snippet_contents = []

        for line in self.lines:

            assert isinstance(line, TaggedLine)

            # If its LAST tag is the same as any of the isolating tags, include it
            if set(line.tags[-1:]).intersection(query.isolate):
                snippet_contents.append (line.text)
                
                has_content = True
            # Otherwise, if it has tags that we want, and none of the tags we don't, include it
            elif set(line.tags).intersection(query.include) and not set(line.tags).intersection(query.exclude):
                snippet_contents.append(line.text)
                
                has_content = True
            else:
                # This line doesn't match the tags we're looking for. Move on to the next.
                pass
        
        if not has_content:
            return None

        rendered_snippet = "\n".join(snippet_contents)
        
        rendered_snippet = textwrap.dedent(rendered_snippet)

        return rendered_snippet



    def parse_lines(self, data):

        assert isinstance(data, str)

        begin_re = re.compile(r"\s*\/\/\s*BEGIN\s+([^\s]+)")
        end_re = re.compile(r"\s*\/\/\s*END\s+([^\s]+)")

        current_tags = []

        for (line_number, line_text) in enumerate(data.split("\n")):
            
            # If this line contains "//-", "/*-" or "-*/", it's a comment
            # that should not be included in rendered snippets.
            if "/*-" in line_text or "-*/" in line_text or "//-" in line_text:
                pass
            
            # If we entered a tag, add it to the list
            elif begin_re.search(line_text):
                tag = begin_re.search(line_text).group(1)
                
                if tag in current_tags:
                    logging.warn("{0}:{1}: \"{2}\" was entered twice without exiting it".format(self.path, line_number, tag))
                else:
                    current_tags.append(tag)
                
                
            # If we left a tag, remove it
            elif end_re.search(line_text):
                tag = end_re.search(line_text).group(1)
                
                if tag not in current_tags:
                    logging.warn("{0}:{1}: \"{2}\" was exited, but had not yet been entered".format(self.path, line_number, tag))
                else:
                    current_tags.remove(tag)
                
            
            # If it's neither, and we're inside any tagged region, 
            # add it to the list of tagged lines 
            elif current_tags:
                self.lines.append(TaggedLine(self.path, line_number, line_text, copy.copy(current_tags)))
    
    def lines_over_limit(self, limit):

        return [line for line in self.lines if len(line.text) > limit]

    
class TaggedLine(object):
    """A line in a document, with its associated tags."""
    def __init__(self, source_name, line_number, text, tags):

        assert isinstance(source_name, str)
        assert isinstance(line_number, int)
        assert isinstance(text, str)
        assert isinstance(tags, list)

        assert tags, "Expected a non-empty list of tags when creating a TaggedLine"

        self.source_name = source_name
        self.line_number = line_number
        self.text = text
        self.tags = tags

INCLUDE_TAGS = 0
EXCLUDE_TAGS = 1
HIGHLIGHT_TAGS = 2
ISOLATE_TAGS = 3

class TagQuery(object):
    """Represents a query for a specific set of tags."""
    def __init__(self, query_string, ref="HEAD"):

        assert isinstance(query_string, str)
        tokens = query_string.split(" ")

        mode = INCLUDE_TAGS
        
        # The context at which we 
        self.query_string = query_string 
        self.ref = ref 

        # The specific tags this query deals with
        self.include = []
        self.exclude = []
        self.highlight = []
        self.isolate = []
        
        
        # Interpret the list of tokens
        for token in tokens:
            
            # Change mode if we have to
            if token == "except":
                mode = EXCLUDE_TAGS
            elif token == "highlighting":
                mode = HIGHLIGHT_TAGS
            elif token == "isolating":
                mode = ISOLATE_TAGS
            
            # Otherwise, add it to the list of tokens
            else:
                if mode == INCLUDE_TAGS:
                    self.include.append(token)
                elif mode == EXCLUDE_TAGS:
                    self.exclude.append(token)
                elif mode == HIGHLIGHT_TAGS:
                    self.highlight.append(token)
                elif mode == ISOLATE_TAGS:
                    self.isolate.append(token)
        
        logging.debug("Query includes tags %s", self.include)
    
    @property
    def as_filename(self):
        if self.ref == "HEAD":
            return "{}.txt".format(self.query_string.replace(" ", "_"))
        else:
            return "{}_{}.txt".format(self.ref, self.query_string.replace(" ", "_"))

    @property
    def all_referenced_tags(self):
        return set(self.include) |  set(self.exclude) |  set(self.highlight) | set(self.isolate)
