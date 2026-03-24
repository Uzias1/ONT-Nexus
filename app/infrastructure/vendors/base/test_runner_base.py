from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.dto.execution_test_request import ExecutionTestRequest


class TestRunnerBase(ABC):
    """
    Base común para runners de pruebas por vendor.
    """

    @abstractmethod
    def run(self, request: ExecutionTestRequest) -> None:
        raise NotImplementedError