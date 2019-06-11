import unittest
from source_document import SourceDocument
from test_tagged_document import create_test_repo
from tagged_document import TaggedDocument

class SourceDocumentTests(unittest.TestCase):
    """Unit tests for the Document class"""
    def test_cleaning(self):
        """Tests removing snippets"""

        input_path = "tests/sample-expanded.txt"
        reference_path = "tests/sample.txt"

        reference_text = open(reference_path, "r").read()

        document = SourceDocument(input_path)

        self.assertEqual(document.cleaned_contents, reference_text)

    def test_finding_documents(self):

        found_documents = SourceDocument.find("tests", ["txt"])

        self.assertTrue(len(found_documents) == 7)



    def test_processing(self):
        """Tests rendering a snippet using tagged documents."""
        repo = create_test_repo()

        tagged_documents = TaggedDocument.find(repo, ["txt"])

        self.assertTrue(tagged_documents)

        input_path = "tests/sample.txt"
        reference_path = "tests/sample-expanded.txt"
        reference_text = open(reference_path, "r").read()

        source = SourceDocument(input_path)

        rendered_output = source.render(tagged_documents, language="swift",show_query=False)

        self.assertEqual(rendered_output, (reference_text, True))



        

