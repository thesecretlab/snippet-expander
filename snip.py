#!/usr/bin/env python

import argparse
import sys
import os
from pprint import pprint
import re

import logging

MAX_LINE_WIDTH=80

FILE_EXTENSIONS = [
    "swift",
    "strings",
    "cs",
    "txt"    
]

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
    
    line_num = 0
    
    for line in file:
        
        # If this line contains "//-", "/*-" or "-*/", it's a comment
        # that should not be rendered.
        if "/*-" in line or "-*/" in line or "//-" in line:
            pass
        
        # If we entered a tag, add it to the list
        elif begin_re.search(line):
            tag = begin_re.search(line).group(1)
            
            if tag in current_tags:
                logging.warn("{0}:{1}: \"{2}\" was entered twice without exiting it".format(path, line_num, tag))
                
            current_tags.append(tag)
            
            
        # If we left a tag, remove it
        elif end_re.search(line):
            tag = end_re.search(line).group(1)
            
            if  tag not in current_tags:
                logging.warn("{0}:{1}: \"{2}\" was exited, but had not yet been entered".format(path, line_num, tag))
                
            current_tags.remove(tag)
            
          
        # If it's neither, add it to the list of tagged lines 
        else:
            tagged_lines.append((line, copy(current_tags), (path, line_num)))
            
        line_num += 1
    
    # TODO: Error if we left a file with an unclosed tag
    
    return tagged_lines

def parse_snippet_command(command):
    """Returns the tuple (tags_to_include, tags_to_exclude, tags_to_highlight)"""
    
    # Split the command into usable tokens
    import re
    tokens = re.split('\/\/|:|,| |\n', command)
    tokens = filter(None, tokens)
    
    if tokens[0] != "snip":
        logging.fatal("Somehow managed to parse First token must be 'snip'")
    
    # The current mode of our parser
    INCLUDE_TAGS=0
    EXCLUDE_TAGS=1
    HIGHLIGHT_TAGS=2    
    ISOLATE_TAGS=3
    mode = INCLUDE_TAGS
    
    # The useful output of this function
    tags_to_include = []
    tags_to_exclude = []
    tags_to_highlight = []
    tags_to_isolate = []
    
    # Interpret the list of tokens
    for token in tokens[1:]:
        
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
                tags_to_include.append(token)
            elif mode == EXCLUDE_TAGS:
                tags_to_exclude.append(token)
            elif mode == HIGHLIGHT_TAGS:
                tags_to_highlight.append(token)
            elif mode == ISOLATE_TAGS:
                tags_to_isolate.append(token)
                if len(tags_to_isolate) > 1:
                    logging.warn("Command {0}: 'isolating' should only have one tag in its list".format(command))
                
    return (tags_to_include,tags_to_exclude,tags_to_highlight,tags_to_isolate)
   
def render_snippet(tags, include, exclude, highlight, isolate):
    """Searches 'tags', and returns a string comprised of all lines that match any tags in 'include' and do not match any in 'exclude'"""
    
    # TODO: Implement highlighting support
    from StringIO import StringIO
    
    has_content = False
    highlighted_lines = []
    
    snippet_contents = StringIO()
    
    for candidate_line in tags:
        
        line = candidate_line[0]
        
        is_highlighted = set(candidate_line[1]).intersection(highlight)
        
        # If its LAST tag is the same as any of the isolating tags, include it
        if set(candidate_line[1][-1:]).intersection(isolate):
            snippet_contents.write(line)
            highlighted_lines.append(is_highlighted)
            has_content = True
        # Otherwise, if it has tags that we want, and none of the tags we don't, include it
        elif set(candidate_line[1]).intersection(include) and not set(candidate_line[1]).intersection(exclude):
            snippet_contents.write(line)
            highlighted_lines.append(is_highlighted)
            has_content = True
            
    if has_content == False:
        return (None, [])
        
    rendered_snippet = snippet_contents.getvalue()
    
    import textwrap
    rendered_snippet = textwrap.dedent(rendered_snippet)
    
    # list of (highlighted,contents) tuples
    contents = []
    
    from string import split
    
    for line_num, line_text in enumerate(split(rendered_snippet, "\n")):
        if line_num < len(highlighted_lines) and highlighted_lines[line_num]:
            contents.append((True, line_text))
        else:
            contents.append((False, line_text))

    
    # remove multiple blank lines
    final_contents = []
    last_line_was_blank = True # doing this means removing initial blank lines
    empty_line = re.compile("^\s*$") # the line contains only whitespace
    for line in contents:
        this_line_blank = empty_line.match(line[1])
        if last_line_was_blank and this_line_blank:
            continue
        last_line_was_blank = this_line_blank
        final_contents.append(line)
    
    rendered_snippet = StringIO()
    
    warnings = []
    
    for (line_num, line) in enumerate(final_contents):
        if line[0] == True:
            rendered_snippet.write("> {0}\n".format(line[1]))
        else:
            rendered_snippet.write("  {0}\n".format(line[1]))
        
        if (len(line[1]) > MAX_LINE_WIDTH):
            warnings.append((line_num, "exceeds max line length ({0})".format(len(line[1]))))
        
    return (rendered_snippet.getvalue(), warnings)
        

def render_file(file_path, tags, language):
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
            snippet_content, warnings = render_snippet(tags, snippet_command[0], snippet_command[1], snippet_command[2], snippet_command[3])
            
            for warning in warnings:
                warn_line_num = warning[0] + file_contents.getvalue().count("\n") + 3
                logging.warn("{0}:{1} {2}".format(file_path, warn_line_num, warning[1]))
            
            if snippet_content:
                file_contents.write("[source,{0}]\n".format(language))
                file_contents.write("----\n")
                file_contents.write(snippet_content)
                file_contents.write("----\n")
                
            
    
    
    return file_contents.getvalue()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Renders snippets in AsciiDoc files.')
    
    parser.add_argument('--only-clean', dest='only_clean', action='store_const',
                       const=True, default=False,
                       help='remove snippets from source documents only')
    parser.add_argument('--lang', dest="language", type=str, default="javascript",
                       help='the language to use for syntax highlighting')
    parser.add_argument('--asciidoc-directory', type=str, default=".",
                       help='the directory containing asciidoc files to process (default = current directory)')
    parser.add_argument('source_directory', type=str,
                       help='the directory to search for code snippets')
    
    args = parser.parse_args()
    
    tags = []
    
    # Pull in the tags, unless we're only cleaning
    if args.only_clean == False:
        
        swift_files = []
        
        for extension in FILE_EXTENSIONS:
            swift_files.extend(build_file_list(args.source_directory, extension))
        
        for file in swift_files:
            new_tags = tag_source_file(file)
            # TODO: Warn if a tag was detected in multiple files
            tags += new_tags
    
    # Process every asciidoc file we found
    asciidoc_files = build_file_list(args.asciidoc_directory, "asciidoc")
    
    for file in asciidoc_files:
        new_contents = render_file(file, tags, args.language)
        new_file = open(file, "w")
        new_file.write(new_contents)
