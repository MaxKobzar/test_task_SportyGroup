"""
Screenplay Pattern: Actor, Task and Question.
The Actor represents a user who performs Tasks and asks Questions using its Abilities.
"""

import logging
from typing import Protocol, TypeVar, cast

import allure

logger = logging.getLogger(__name__)

TAbility = TypeVar("TAbility")
TAnswer = TypeVar("TAnswer", covariant=True)


class Task(Protocol):
    """Something the actor does."""

    def perform_as(self, actor: "Actor") -> None: ...


class Question(Protocol[TAnswer]):
    """Something the actor finds out about the system state."""

    def answered_by(self, actor: "Actor") -> TAnswer: ...


class Actor:
    """An Actor interacts with the application through its abilities."""

    def __init__(self, name: str):
        self.name = name
        self._abilities: dict[type, object] = {}

    @classmethod
    def named(cls, name: str) -> "Actor":
        """Create a named Actor."""
        return cls(name=name)

    def can(self, ability: object) -> "Actor":
        """Grant an ability (one per type)."""
        self._abilities[type(ability)] = ability
        logger.info("Actor '%s' gained ability %s", self.name, type(ability).__name__)
        return self

    def ability_to(self, ability_cls: type[TAbility]) -> TAbility:
        """Return the ability of the given type."""
        try:
            return cast(TAbility, self._abilities[ability_cls])
        except KeyError:
            raise LookupError(
                f"Actor '{self.name}' does not have the ability {ability_cls.__name__}"
            ) from None

    def attempts_to(self, *tasks: Task) -> None:
        """Perform tasks in order, each as an Allure step."""
        for task in tasks:
            task_name = type(task).__name__
            with allure.step(f"{self.name} attempts to: {task_name}"):
                logger.info("%s performs %s", self.name, task_name)
                task.perform_as(self)

    def asks_for(self, question: Question[TAnswer]) -> TAnswer:
        """Answer a question about the current state of the application."""
        question_name = type(question).__name__
        with allure.step(f"{self.name} asks: {question_name}"):
            logger.info("%s asks %s", self.name, question_name)
            return question.answered_by(self)
