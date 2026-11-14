"""
Screenplay Pattern: Actor implementation.
The Actor represents a user performing business tasks and asking questions about the system state.
"""
from typing import Any, Dict, List, Type, TypeVar
import allure

from framework.core.logger import get_logger

TAbility = TypeVar("TAbility")
logger = get_logger("ScreenplayActor")


class Actor:
    """An Actor interacts with the application using assigned abilities."""

    def __init__(self, name: str):
        self.name = name
        self._abilities: Dict[Type, Any] = {}

    @classmethod
    def named(cls, name: str) -> "Actor":
        """Factory method to instantiate a named Actor."""
        return cls(name=name)

    def can(self, ability: Any) -> "Actor":
        """Assign an ability to the Actor."""
        ability_type = type(ability)
        self._abilities[ability_type] = ability
        logger.info(f"Actor '{self.name}' gained ability: {ability_type.__name__}")
        return self

    def ability_to(self, ability_cls: Type[TAbility]) -> TAbility:
        """Retrieve an ability possessed by the Actor."""
        if ability_cls not in self._abilities:
            raise KeyError(f"Actor '{self.name}' does not possess ability '{ability_cls.__name__}'")
        return self._abilities[ability_cls]

    def attempts_to(self, *tasks) -> None:
        """Perform a sequence of Tasks or Actions in order."""
        for task in tasks:
            task_name = task.__class__.__name__
            with allure.step(f"{self.name} attempts to: {task_name}"):
                logger.info(f"{self.name} is performing task: {task_name}")
                task.perform_as(self)

    def asks_for(self, question: Any) -> Any:
        """Ask a question about the current state of the application."""
        question_name = question.__class__.__name__
        with allure.step(f"{self.name} asks: {question_name}"):
            logger.info(f"{self.name} asks question: {question_name}")
            return question.answered_by(self)
