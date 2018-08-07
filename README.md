# Snippet Expander

We needed a way to expand snippets when we wrote books so we made this!

Snippet Expander lets you refer to code from one file (e.g. asciidoc source of a book, say) by including tags referring to parts of another file (e.g. your example source code).

Note that highlighting is currently broken. 

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

    $ brew install pipenv

2. Clone the snippet processor:

    $ git clone git@github.com:thesecretlab/snippet-expander.git

3. Enter the directory you just cloned:

	$ cd snippet-expander 

4. Set up your environment

	$ pipenv install

5. 
