"""
Screenplay Ability: CallAPI.
Enables an Actor to execute REST API requests through BettingApiClient.
"""

from framework.api.client import BettingApiClient


class CallAPI:
    """Ability to communicate directly with backend APIs."""

    def __init__(self, client: BettingApiClient):
        self.client = client

    @classmethod
    def with_client(cls, client: BettingApiClient) -> "CallAPI":
        """Create the ability around an API client."""
        return cls(client=client)
