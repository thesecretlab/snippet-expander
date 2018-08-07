# Snippet Expander

We needed a way to expand snippets when we wrote books so we made this!

Snippet Expander lets you refer to code from one file (e.g. asciidoc source of a book, say) by including tags referring to parts of another file (e.g. your example source code).

## Usage

Include snippet(s) in your text file:

    // snip: (snippet name), [(snippet name)...]

Include snippet(s) but exclude some snippets:

    // snip: (snippet name), [(snippet name)...] except (snippet name), [(snippet name)...]

Include snippet(s) and highlight some snippets:

    // snip: (snippet name), [(snippet name)...] highlighting (snippet name), [(snippet name)...]

"except" and "highlighting" can be combined.

Multiple snippets can have the same name; they will be combined at build time in the order that they appear in the file.

Include snippets, but none of their child snippets:

    // snip: isolating (snippet name)

> Please note: `highlighting` is currently broken in this version!

## Example

In your text file:
````
This is some text explaining some code, and here is the code:

// snip: code_example_1

This continues the explanation of the code above.
````

In your code example file:
````
// BEGIN code_example_1
var someVariable = "Yes"
// END code_example_1
````
After running Snippet Expander, the text file:

````
This is some text explaining some code, and here is the code:

// snip: code_example_1
[source,javascript]
----
var someVariable = "Yes"
----

This continues the explanation of the code above.
````
Execute with --help for options/instructions on running. Snippets can be nested and updated.

You can also use the `isolating` feature to show only the top level of a snippet. For example, say have the following code:

````
// BEGIN function_foo
func foo() {
	
	// BEGIN thing_one
	do_thing_one()
	// END thing_one	
	
	// BEGIN thing_two
	do_thing_two()
	// END thing_two
	
}
// END function_foo
````

And you have the following text:

````
// snip: isolating function_foo
````

This will be rendered as:

````
func foo() {
	
}
````

Note that you don't have to keep track of the tags you want to exclude - if you just want the top level of stuff, use `isolating`!

## Installing

1. Install Pipenv:

````bash
$ brew install pipenv
````

2. Clone the snippet processor:

````bash
$ git clone git@github.com:thesecretlab/snippet-expander.git
````

3. Enter the directory you just cloned:

````bash
$ cd snippet-expander
````

4. Set up your environment

````bash
$ pipenv install --two # ensures Python 2
````

5. Start a shell:

````bash
$ pipenv shell
````

6. You're now ready to use it.

## Usage

`processor.py` is the main script that does all the work. You invoke it like this:

````bash
$ ./processor.py <path to your asciidoc folder> <path to your source code folder>
````

The source code folder *must be a Git repository*, and the code you want to make appear in the AsciiDoc *must be committed to Git*. Otherwise, the script won't see it.

### Useful options:

* If you want to see what files would change without actually writing any changes, use the `--dry-run` option.
* The `--clean` option will remove any source code snippets from the AsciiDoc file. This is useful when you want to focus on your own written text. You can put them back in later by running without `--clean`.
* The `--lang` option allows you to indicate in your AsciiDoc files what language the source code snippets are. It defaults to `swift`; you can specify any language that your AsciiDoc processor is aware of. (For example, many AsciiDoc processing toolchains use [Pygments](http://pygments.org/).)

The full set of options is:

````
Usage: processor.py [options] asciidoc_dir sourcecode_dir

Options:
  -h, --help            show this help message and exit
  -l LANGUAGE, --lang=LANGUAGE
                        Indicate that the source code is in this language when
                        syntax highlighting
  -n, --dry-run         Don't actually modify any files
  --clean               Remove snippets from files
  --suffix=SUFFIX       Append this to the file name of written files
                        (default=none)
  -x EXTRACT_DIR, --extract-snippets=EXTRACT_DIR
                        Render each snippet to a file, and store it in this
                        directory.
  -v, --verbose         Verbose logging.
  -q, --show_query      Include the query in rendered snippets.
````