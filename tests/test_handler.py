import os
import pytest
from intelli_sort.main import MyEventHandler

# A sample categories dictionary for our tests.
# We define it here so our tests are independent of the config.yaml file.
TEST_CATEGORIES = {
    'Documents': ['.txt'],
    'Images': ['.jpg']
}

def test_process_file_moves_known_file_type(tmp_path):
    """
    Tests if a known file type (.txt) is correctly moved to the Documents folder.
    This follows the Arrange-Act-Assert pattern.
    """
    # 1. ARRANGE: Set up the test environment.
    # tmp_path is our temporary directory provided by pytest.
    source_dir = tmp_path
    test_file_path = source_dir / "test_document.txt"
    test_file_path.touch() # .touch() creates an empty file.

    dest_dir = source_dir / "Documents"

    # Create an instance of our handler.
    handler = MyEventHandler(str(source_dir), TEST_CATEGORIES)

    # 2. ACT: Call the method we want to test.
    handler.process_file(str(test_file_path))

    # 3. ASSERT: Check if the outcome is what we expected.
    # Assert that the destination file exists.
    assert os.path.exists(dest_dir / "test_document.txt")
    # Assert that the original file no longer exists.
    assert not os.path.exists(test_file_path)

def test_process_file_skips_uncategorized_file_type(tmp_path):
    """
    Tests if an unknown file type (.xyz) is correctly skipped and not moved.
    """
    # 1. ARRANGE
    source_dir = tmp_path
    test_file_path = source_dir / "unknown_file.xyz"
    test_file_path.touch()

    handler = MyEventHandler(str(source_dir), TEST_CATEGORIES)

    # 2. ACT
    handler.process_file(str(test_file_path))

    # 3. ASSERT
    # Assert that the original file STILL exists (it wasn't moved).
    assert os.path.exists(test_file_path)
    # Assert that no new category folders were created.
    assert not os.path.exists(source_dir / "XYZ_Files")