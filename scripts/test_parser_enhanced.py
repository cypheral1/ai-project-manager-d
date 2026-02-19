#!/usr/bin/env python3
"""
Tests for the enhanced regex parser – verifies all 6 intents,
team+people extraction, allocation validation, and status updates.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parser import parse_command


class TestParserIntents(unittest.TestCase):
    """Test intent detection across all 6 types."""

    def test_get_status(self):
        for msg in ["What is the status of Project A?", "How is Project B doing?",
                     "Tell me about Project C", "progress of Project D"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "GET_STATUS", f"Failed for: {msg}")

    def test_create_project(self):
        for msg in ["Create Project Alpha with 10 tasks", "Set up Project Beta",
                     "Build Project Gamma", "New project Delta"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "CREATE_PROJECT", f"Failed for: {msg}")

    def test_list_projects(self):
        for msg in ["List all projects", "Show all projects", "Which projects exist?"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "LIST_PROJECTS", f"Failed for: {msg}")

    def test_update_task(self):
        for msg in ["Update Project A to 50% completion",
                     "Mark Project B as completed", "Set completion of Project C to 80%"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "UPDATE_TASK", f"Failed for: {msg}")

    def test_delete_project(self):
        for msg in ["Delete Project A", "Remove Project B", "Drop Project C"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "DELETE_PROJECT", f"Failed for: {msg}")

    def test_help(self):
        for msg in ["Help", "What can you do?", "Show me commands"]:
            result = parse_command(msg)
            self.assertEqual(result["intent"], "HELP", f"Failed for: {msg}")

    def test_unknown(self):
        result = parse_command("The weather is nice today")
        self.assertEqual(result["intent"], "UNKNOWN")


class TestParserExtraction(unittest.TestCase):
    """Test entity extraction from user input."""

    def test_project_name(self):
        result = parse_command("Create Project Alpha with 10 tasks")
        self.assertIn("Alpha", result["project_name"])

    def test_total_tasks(self):
        result = parse_command("Create Project X with 16 tasks")
        self.assertEqual(result["total_tasks"], 16)

    def test_allocations_with_people(self):
        msg = "Create Project X with 12 tasks, 7 to frontend (John, Sarah), 5 to backend (Mike)"
        result = parse_command(msg)
        self.assertEqual(result["total_tasks"], 12)
        self.assertIn("frontend", result["allocations"])
        self.assertIn("backend", result["allocations"])
        self.assertEqual(result["allocations"]["frontend"]["count"], 7)
        self.assertIn("John", result["allocations"]["frontend"]["people"])
        self.assertIn("Sarah", result["allocations"]["frontend"]["people"])
        self.assertEqual(result["allocations"]["backend"]["count"], 5)
        self.assertIn("Mike", result["allocations"]["backend"]["people"])

    def test_allocations_without_people(self):
        msg = "Create Project Y with 10 tasks, 5 to frontend, 5 to backend"
        result = parse_command(msg)
        self.assertEqual(result["allocations"]["frontend"]["count"], 5)
        self.assertEqual(result["allocations"]["frontend"]["people"], [])

    def test_multiple_teams(self):
        msg = "Create Project Z with 16 tasks, 7 to frontend (John, Sarah), 5 to backend (Mike, Tom), 4 to testing (Lisa)"
        result = parse_command(msg)
        self.assertEqual(len(result["allocations"]), 3)
        self.assertIn("testing", result["allocations"])
        self.assertEqual(result["allocations"]["testing"]["count"], 4)
        self.assertIn("Lisa", result["allocations"]["testing"]["people"])


class TestParserValidation(unittest.TestCase):
    """Test allocation sum validation."""

    def test_valid_sum(self):
        msg = "Create Project X with 10 tasks, 5 to frontend, 5 to backend"
        result = parse_command(msg)
        self.assertIsNone(result["validation_error"])

    def test_invalid_sum(self):
        msg = "Create Project X with 10 tasks, 3 to frontend, 3 to backend"
        result = parse_command(msg)
        self.assertIsNotNone(result["validation_error"])
        self.assertIn("mismatch", result["validation_error"].lower())

    def test_auto_calculate_total(self):
        msg = "Create Project X, 5 to frontend, 5 to backend"
        result = parse_command(msg)
        self.assertEqual(result["total_tasks"], 10)


class TestParserStatusUpdate(unittest.TestCase):
    """Test status update field extraction."""

    def test_completion_extraction(self):
        msg = "Update Project A to 75% completion"
        result = parse_command(msg)
        self.assertEqual(result["intent"], "UPDATE_TASK")
        self.assertEqual(result["update_fields"]["completion"], 75)

    def test_status_extraction(self):
        msg = "Mark Project B as completed"
        result = parse_command(msg)
        self.assertEqual(result["intent"], "UPDATE_TASK")
        self.assertEqual(result["update_fields"]["status"], "Completed")


if __name__ == "__main__":
    unittest.main()
