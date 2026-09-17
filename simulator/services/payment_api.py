import random


class PaymentAPI:
    """
    Simulated production payment service.

    The service can operate in three states:
        healthy
        degraded
        failing

    Each state affects request latency and probability of failure.
    """

    STATES = {
        "healthy": {
            "latency_min": 80,
            "latency_max": 200,
            "error_rate": 0.01,
        },
        "degraded": {
            "latency_min": 400,
            "latency_max": 900,
            "error_rate": 0.20,
        },
        "failing": {
            "latency_min": 1000,
            "latency_max": 3000,
            "error_rate": 0.80,
        },
    }

    def __init__(self, state="healthy"):
        self.state = state

    def set_state(self, state):
        """Change the simulated production state."""

        if state not in self.STATES:
            raise ValueError(
                f"Invalid state: {state}. "
                f"Choose from: {list(self.STATES)}"
            )

        self.state = state

    def process_payment(self):
        """
        Simulate one payment request.

        Returns the result of the request, including:
        - current service state
        - success/failure
        - simulated latency
        """

        config = self.STATES[self.state]

        latency = round(
            random.uniform(
                config["latency_min"],
                config["latency_max"],
            ),
            2,
        )

        success = random.random() >= config["error_rate"]

        return {
            "service": "payment-api",
            "state": self.state,
            "success": success,
            "latency_ms": latency,
        }
