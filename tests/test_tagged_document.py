import unittest
import shutil
import os
import git

from tagged_document import TaggedDocument

dir_path = os.getcwd()

REPO_DIR = os.path.join(dir_path, ".test_repo")

def create_test_repo():
    # This setup creates a git repo in REPO_DIR that contains
    # a single file that changes across multiple versions.

    if not os.path.isdir(REPO_DIR):
        # the folder doesn't exist - create it
        os.mkdir(REPO_DIR)
    else:
        # the folder does exist, but is not empty; remove it
        # and replace it with an empty one
        shutil.rmtree(REPO_DIR)
        os.mkdir(REPO_DIR)

    # Initialise the empty repo
    repo = git.Repo.init(REPO_DIR)

    # We're going to create three versions of this file; each version has
    # different content, so we'll pull that from these source files
    versions =["sourceA-v1.txt",  "sourceA-v2.txt",  "sourceA-v3.txt"]
    
    # We'll also add in place a version that exists in the working copy, but has not yet been committed.
    uncommitted_version = "sourceA-v4.txt"

    # Finally, we'll also add a file that is present in the working copy,
    # but has never been committed to the repo (i.e. no versions of it
    # exist at all in the history.)
    uncommitted_file = "sourceB.txt"

    # Get the index so we can stage and commit each version
    index = repo.index

    # Create a fake user to commit with
    committer = git.Actor("Test Committer", "test@example.com")

    # Do a shortcut
    join = os.path.join 

    # Add and commit the multiple versions of the file
    for version in versions:
        shutil.copy(join("tests",version), join(REPO_DIR,"sourceA.txt"))
        index.add(["sourceA.txt"])
        index.commit("Updated sourceA.txt using {}".format(version), author=committer)
        repo.create_tag(version)
    
    # Copy in the last version on top, as an uncommitted version in the
    # working copy
    shutil.copy(join("tests",uncommitted_version), join(REPO_DIR,"sourceA.txt"))

    # Copy in the uncommitted file
    shutil.copy(join("tests",uncommitted_file), join(REPO_DIR,"sourceB.txt"))

    
    return repo

class SourceDocumentTests(unittest.TestCase):

    def setUp(self):
        # create a repo with test data
        self.repo = create_test_repo()
    
    def tearDown(self): 
        # remove the reference to the repo
        self.repo = None
  

    def test_repo(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        # HEAD should be at the most recent version
        main_version = document["HEAD"].data

        most_recent_version = open("tests/sourceA-v3.txt").read()

        self.assertEqual(most_recent_version, main_version)
    
    def test_tag_access(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        tags = ["sourceA-v1.txt", "sourceA-v2.txt", "sourceA-v3.txt"]

        # the repo contains a tag for each version, and each tag is named
        # with the original source file (eg "-v1.txt" etc).

        # check that each tag in the repo matches its corresponding source
        # file
        for tag in tags:
            tagged_version = document[tag].data

            reference_version = open("tests/" + tag, "r").read()

            self.assertEqual(tagged_version, reference_version)

    def test_line_tagging(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        self.assertEqual(2, len(document["HEAD"].lines))
    
    def test_including_queries(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        tagged_text = document["HEAD"].query("sourceA")

        reference_text = "This is version 3 of source A.\nThis line is tagged with both 'sourceA' and 'sourceA-1'."

        self.assertEqual(tagged_text, reference_text)
    
    def test_isolating_queries(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        tagged_text = document["HEAD"].query("isolating sourceA")

        reference_text = "This is version 3 of source A."

        self.assertEqual(tagged_text, reference_text)
    
    def test_excluding_queries(self):
        document = TaggedDocument(self.repo, "sourceA.txt")

        tagged_text = document["HEAD"].query("sourceA except sourceA-1")

        reference_text = "This is version 3 of source A."

        self.assertEqual(tagged_text, reference_text)
        