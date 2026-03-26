# Author: Antonio Corona
# Date: 2026-03-26
"""
Tests for AI Service

Covers the service-layer orchestration logic for the Sprint 3 Chunk A AI Chat Tool.

Responsibilities:
    - Verify stateless command processing behavior
    - Verify base prompt construction behavior
    - Verify correct handling of tool-calling responses
    - Verify structured success/error results returned to routes

Notes:
    - External OpenAI calls should be mocked in these tests.
    - Tests should focus on service logic, not live API behavior.
"""