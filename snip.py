#!/usr/bin/env python

import argparse
import sys
import os
from pprint import pprint
import re

MAX_LINE_WIDTH=80

def build_file_list(starting_dir, extension):
    """Returns an array of files."""
    found_files = []
    
    for (path, dirs, files) in os.walk(starting_dir):
        for filename in files:
            if filename.endswith("."+extension):
                found_files.append(path+os.path.sep+filename)
    
    return found_files
    
def tag_source_file(path):
    """Returns a list of tuples: (line_text, list_of_tags)"""

    file = open(path, "r")
    
    # The list of tagged lines
    tagged_lines = []
    
    # The list of tags that currently apply
    current_tags = []
    
    # Use this to store snapshots of current_tags
    from copy import copy
    
    # Regexes for detecting when tags start and end
    begin_re = re.compile(".*?\/\/ BEGIN (.*).*")
    end_re = re.compile(".*?\/\/ END (.*).*")
    
    for line in file:
        
        # If we entered a tag, add it to the list
        if begin_re.search(line):
            tag = begin_re.search(line).group(1)
            current_tags.append(tag)
            
        # If we left a tag, remove it
        elif end_re.search(line):
            tag = end_re.search(line).group(1)
            current_tags.remove(tag)
            # TODO: Error if we exited a tag that we did not enter
          
        # If it's neither, add it to the list of tagged lines 
        else:
            tagged_lines.append((line, copy(current_tags)))
    
    # TODO: Error if we left a file with an unclosed tag
    
    return tagged_lines
    

    
    

def parse_snippet_command(command):
    """Returns the tuple (tags_to_include, tags_to_exclude, tags_to_highlight)"""
    
    # Split the command into usable tokens
    import re
    tokens = re.split('\/\/|:|,| |\n', command)
    tokens = filter(None, tokens)
    
    if tokens[0] != "snip":
        raise ValueError("First token must be 'snip'")
    
    # The current mode of our parser
    INCLUDE_TAGS=0
    EXCLUDE_TAGS=1
    HIGHLIGHT_TAGS=2    
    mode = INCLUDE_TAGS
    
    # The useful output of this function
    tags_to_include = []
    tags_to_exclude = []
    tags_to_highlight = []
    
    # Interpret the list of tokens
    for token in tokens[1:]:
        
        # Change mode if we have to
        if token == "except":
            mode = EXCLUDE_TAGS
        elif token == "highlighting":
            mode = HIGHLIGHT_TAGS
        
        # Otherwise, add it to the list of tokens
        else:
            if mode == INCLUDE_TAGS:
                tags_to_include.append(token)
            elif mode == EXCLUDE_TAGS:
                tags_to_exclude.append(token)
            elif mode == HIGHLIGHT_TAGS:
                tags_to_highlight.append(token)
                
    return (tags_to_include,tags_to_exclude,tags_to_highlight)
   
def render_snippet(tags, include, exclude, highlight):
    """Searches 'tags', and returns a string comprised of all lines that match any tags in 'include' and do not match any in 'exclude'"""
    
    # TODO: Implement highlighting support
    from StringIO import StringIO
    
    has_content = False
    snippet_contents = StringIO()
    
    for candidate_line in tags:
        # If it has tags that we want, and none of the tags we don't, include it
        if set(candidate_line[1]).intersection(include) and not set(candidate_line[1]).intersection(exclude):
            snippet_contents.write(candidate_line[0])
            has_content = True
            
    if has_content == False:
        return None
        
    rendered_snippet = snippet_contents.getvalue()
    
    import textwrap
    rendered_snippet = textwrap.dedent(rendered_snippet)
    
    
    
    # wrapper = textwrap.TextWrapper()
    # wrapper.width = MAX_LINE_WIDTH
    # replace_whitespace = False
    #
    # rendered_snippet = wrapper.fill(rendered_snippet)
    
    # TODO: Remove multiple blank lines
    # TODO: Warn when de-indented lines exceed a line width
    
    return rendered_snippet
        

def render_file(file_path, tags):
    """Returns the text of the file, with snippets rendered."""
    
    # First, clean the file of any already-rendered snippets
    file = open(file_path, 'r')
    file_contents = file.read()
    snip_with_code = re.compile("(//.*snip:.*\n)(\[.*\]\n)*----\n(.*\n)*?----\n")
    cleaned_contents = re.sub(snip_with_code, r'\1', file_contents)
    
    # Now render snippets in this cleaned content
    from StringIO import StringIO    
    cleaned_contents = StringIO(cleaned_contents)
    file_contents = StringIO()
    
    for line in cleaned_contents:
        
        # Write back the line
        file_contents.write(line)
        
        # Expand snippet commands if we find them
        if line.startswith("// snip:"):
            
            snippet_command = parse_snippet_command(line)
            snippet_content = render_snippet(tags, snippet_command[0], snippet_command[1], snippet_command[2])
            
            if snippet_content:            
                file_contents.write("[source,javascript]\n")
                file_contents.write("----\n")
                file_contents.write(snippet_content)
                file_contents.write("----\n")
    
    
    return file_contents.getvalue()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Renders snippets in AsciiDoc files.')
    
    parser.add_argument('--only-clean', dest='only_clean', action='store_const',
                       const=True, default=False,
                       help='remove snippets from source documents only')
    parser.add_argument('--asciidoc-directory', type=str, default=".",
                       help='the directory containing asciidoc files to process (default = current directory)')
    parser.add_argument('source_directory', type=str,
                       help='the directory to search for code snippets')
    
    args = parser.parse_args()
    
    tags = []
    
    # Pull in the tags, unless we're only cleaning
    if args.only_clean == False:
        swift_files = build_file_list(args.source_directory, "swift")
        
        for file in swift_files:
            new_tags = tag_source_file(file)
            # TODO: Warn if a tag was detected in multiple files
            tags += new_tags
    
    # Process every asciidoc file we found
    asciidoc_files = build_file_list(args.asciidoc_directory, "asciidoc")
    
    for file in asciidoc_files:
        new_contents = render_file(file, tags)
        new_file = open(file, "w")
        new_file.write(new_contents)
