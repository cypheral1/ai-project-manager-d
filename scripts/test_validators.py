#!/usr/bin/env python3
"""
Tests for the input validation module.
Covers project creation, allocation checks, duplicate detection, and update validation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from validators import (
    validate_project_creation,
    validate_allocations,
    validate_project_update,
    check_duplicate_project,
)


class TestProjectCreationValidation(unittest.TestCase):
    """Test project creation inputs."""

    def test_valid_creation(self):
        valid, error = validate_project_creation("Project A", 10)
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_empty_name(self):
        valid, error = validate_project_creation("", 10)
        self.assertFalse(valid)
        self.assertIn("empty", error.lower())

    def test_name_too_long(self):
        valid, error = validate_project_creation("A" * 101, 10)
        self.assertFalse(valid)
        self.assertIn("100", error)

    def test_negative_tasks(self):
        valid, error = validate_project_creation("Project A", -5)
        self.assertFalse(valid)

    def test_tasks_too_many(self):
        valid, error = validate_project_creation("Project A", 1001)
        self.assertFalse(valid)
        self.assertIn("1000", error)

    def test_none_tasks(self):
        valid, error = validate_project_creation("Project A", None)
        self.assertFalse(valid)
        self.assertIn("specified", error.lower())

    def test_with_valid_allocations(self):
        allocs = {"frontend": {"count": 5, "people": ["John"]},
                  "backend": {"count": 5, "people": ["Mike"]}}
        valid, error = validate_project_creation("Project A", 10, allocs)
        self.assertTrue(valid)

    def test_with_mismatched_allocations(self):
        allocs = {"frontend": {"count": 3, "people": []},
                  "backend": {"count": 3, "people": []}}
        valid, error = validate_project_creation("Project A", 10, allocs)
        self.assertFalse(valid)
        self.assertIn("mismatch", error.lower())


class TestAllocationValidation(unittest.TestCase):
    """Test allocation validation."""

    def test_valid_allocations(self):
        allocs = {"frontend": {"count": 5, "people": ["A", "B"]}}
        valid, error = validate_allocations(allocs, 5)
        self.assertTrue(valid)

    def test_zero_count(self):
        allocs = {"frontend": {"count": 0, "people": []}}
        valid, error = validate_allocations(allocs, 0)
        self.assertFalse(valid)
        self.assertIn("zero", error.lower())

    def test_empty_team_name(self):
        allocs = {"": {"count": 5, "people": []}}
        valid, error = validate_allocations(allocs, 5)
        self.assertFalse(valid)

    def test_integer_format(self):
        allocs = {"frontend": 5}
        valid, error = validate_allocations(allocs, 5)
        self.assertTrue(valid)


class TestProjectUpdateValidation(unittest.TestCase):
    """Test update field validation."""

    def test_valid_status(self):
        valid, error = validate_project_update(status="In Progress")
        self.assertTrue(valid)

    def test_invalid_status(self):
        valid, error = validate_project_update(status="Flying")
        self.assertFalse(valid)

    def test_valid_completion(self):
        valid, error = validate_project_update(completion=75)
        self.assertTrue(valid)

    def test_invalid_completion_range(self):
        valid, error = validate_project_update(completion=150)
        self.assertFalse(valid)

    def test_negative_delayed(self):
        valid, error = validate_project_update(delayed_tasks=-1)
        self.assertFalse(valid)


class TestDuplicateCheck(unittest.TestCase):
    """Test duplicate project detection."""

    def test_no_duplicate(self):
        class MockDB:
            def get_project(self, name):
                return None
        self.assertFalse(check_duplicate_project(MockDB(), "New Project"))

    def test_found_duplicate(self):
        class MockDB:
            def get_project(self, name):
                return {"name": name}
        self.assertTrue(check_duplicate_project(MockDB(), "Existing"))


if __name__ == "__main__":
    unittest.main()
