import unittest
from processor import Processor
from source_document import SourceDocument
from tagged_document import TaggedDocument
from test_tagged_document import create_test_repo

import os

class ProcessorTests(unittest.TestCase):

    def test_processing_files(self):

        new_repo = create_test_repo()

        processor = Processor("tests", new_repo.working_dir, tagged_extensions=["txt"], language="swift")

        # for this test, we only care about the sample
        processor.source_documents = filter(lambda x: x.path.endswith("sample.txt"), processor.source_documents)

        self.assertTrue(processor.tagged_documents)

        self.assertTrue(len(processor.source_documents) == 1)

        processor.process(suffix=".processed")

        reference_text = open("tests/sample-expanded.txt", "r").read()

        processed_text = open("tests/sample.txt.processed").read()

        self.assertEqual(reference_text, processed_text)

    def tearDown(self):
        # remove the processed file, if it exists

        path = "tests/sample.txt.processed"

        if os.path.isfile(path):
            os.remove(path)




