# Snippet Expander

We needed a way to expand snippets when we wrote books so we made this!

Snippet Expander lets you refer to code from one file (e.g. asciidoc source of a book, say) by including tags referring to parts of another file (e.g. your example source code).

Note that highlighting is currently broken.

## Usage

Include snippet(s) in your text file:

// snip: <snippet name>, [<snippet name>...]

Include snippet(s) but exclude some snippets:

// snip: <snippet name>, [<snippet name>...] except <snippet name>, [<snippet name>...]

Include snippet(s) and highlight some snippets:

// snip: <snippet name>, [<snippet name>...] highlighting <snippet name>, [<snippet name>...]

"except" and "highlighting" can be combined.

Multiple snippets can have the same name; they will be combined at build time in the order that they appear in the file.

## Ideas

Some of thiese might already be done:

* Run this as a pre-commit hook so that it's always up to date
* This will embed the code straight into the asciidoc; consider a "snip clean" command to remove them?
* Big huge errors if a snippet is not found
* Define a default language for syntax highlighting in atlas.json
* Work out how to reference source files (maybe don't? do a search for unique tags instead? might be worth adding in a command like "search for tags relative to this folder now" to avoid having to make EVERY tag globally unique)
* De-indent final snippet content so that no lines have extraneous leading whitespace
* Alert when lines go over a certain width, to catch typesetting issues
* Take de-indentation into account
* Collapse multiple blank lines to a single blank line

## License

The MIT License (MIT)

Copyright (c) 2015 Secret Lab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

