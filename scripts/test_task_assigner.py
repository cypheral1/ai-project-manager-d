#!/usr/bin/env python3
"""
Tests for the task auto-assignment engine.
Covers keyword categorization, round-robin distribution, suggestion, and Java payload generation.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from task_assigner import (
    categorize_task,
    categorize_tasks_batch,
    distribute_tasks_round_robin,
    auto_assign_tasks,
    suggest_allocation,
    generate_java_payload,
)


class TestTaskCategorization(unittest.TestCase):
    """Test keyword-based task categorization."""

    def test_frontend_keywords(self):
        self.assertEqual(categorize_task("Build the login page UI"), "frontend")
        self.assertEqual(categorize_task("Create responsive navigation component"), "frontend")

    def test_backend_keywords(self):
        self.assertEqual(categorize_task("Set up REST API endpoints"), "backend")
        self.assertEqual(categorize_task("Implement database migration"), "backend")

    def test_testing_keywords(self):
        self.assertEqual(categorize_task("Write unit tests for auth"), "testing")
        self.assertEqual(categorize_task("QA regression testing"), "testing")

    def test_devops_keywords(self):
        self.assertEqual(categorize_task("Deploy to AWS with Docker"), "devops")

    def test_general_fallback(self):
        self.assertEqual(categorize_task("Do something random"), "general")

    def test_batch_categorization(self):
        tasks = [
            "Build login page",
            "Create API endpoint",
            "Write unit tests",
        ]
        result = categorize_tasks_batch(tasks)
        self.assertIn("frontend", result)
        self.assertIn("backend", result)
        self.assertIn("testing", result)


class TestRoundRobin(unittest.TestCase):
    """Test workload balancing distribution."""

    def test_even_distribution(self):
        result = distribute_tasks_round_robin(6, ["Alice", "Bob", "Charlie"])
        self.assertEqual(result, {"Alice": 2, "Bob": 2, "Charlie": 2})

    def test_uneven_distribution(self):
        result = distribute_tasks_round_robin(7, ["Alice", "Bob"])
        self.assertEqual(result, {"Alice": 4, "Bob": 3})

    def test_single_person(self):
        result = distribute_tasks_round_robin(5, ["Alice"])
        self.assertEqual(result, {"Alice": 5})

    def test_empty_people(self):
        result = distribute_tasks_round_robin(5, [])
        self.assertEqual(result, {})


class TestAutoAssign(unittest.TestCase):
    """Test the full auto-assignment pipeline."""

    def test_basic_assignment(self):
        allocations = {
            "frontend": {"count": 6, "people": ["John", "Sarah"]},
            "backend": {"count": 4, "people": ["Mike"]}
        }
        result = auto_assign_tasks(10, allocations)

        self.assertEqual(result["frontend"]["assignments"]["John"], 3)
        self.assertEqual(result["frontend"]["assignments"]["Sarah"], 3)
        self.assertEqual(result["backend"]["assignments"]["Mike"], 4)

    def test_no_people(self):
        allocations = {"frontend": {"count": 5, "people": []}}
        result = auto_assign_tasks(5, allocations)
        self.assertEqual(result["frontend"]["assignments"], {})


class TestSuggestAllocation(unittest.TestCase):
    """Test allocation suggestion."""

    def test_default_teams(self):
        result = suggest_allocation(12)
        self.assertEqual(result["frontend"]["count"], 4)
        self.assertEqual(result["backend"]["count"], 4)
        self.assertEqual(result["testing"]["count"], 4)

    def test_custom_teams(self):
        result = suggest_allocation(10, ["a", "b"])
        self.assertEqual(result["a"]["count"], 5)
        self.assertEqual(result["b"]["count"], 5)


class TestJavaPayload(unittest.TestCase):
    """Test structured JSON generation for Java backend."""

    def test_payload_structure(self):
        allocations = {
            "frontend": {"count": 5, "people": ["John"], "assignments": {"John": 5}}
        }
        payload = generate_java_payload("Project X", 5, allocations)

        self.assertEqual(payload["action"], "CREATE")
        self.assertEqual(payload["project"]["name"], "Project X")
        self.assertEqual(payload["project"]["totalTasks"], 5)
        self.assertEqual(len(payload["project"]["teams"]), 1)
        self.assertEqual(payload["project"]["teams"][0]["teamName"], "frontend")
        self.assertEqual(payload["project"]["teams"][0]["members"][0]["name"], "John")
        self.assertEqual(payload["project"]["teams"][0]["members"][0]["assignedTasks"], 5)

    def test_custom_action(self):
        payload = generate_java_payload("P", 0, {}, action="DELETE")
        self.assertEqual(payload["action"], "DELETE")


if __name__ == "__main__":
    unittest.main()
