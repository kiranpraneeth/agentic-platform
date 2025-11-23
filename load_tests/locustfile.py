"""Locust load testing for Agentic Platform API."""

import random
from locust import HttpUser, task, between, events


class AgenticPlatformUser(HttpUser):
    """Simulated user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    host = "http://localhost:8000"

    def on_start(self):
        """Run once when user starts - login and get token."""
        # Login to get access token
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpass123",
            },
        )

        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.access_token = None
            self.headers = {}

    @task(10)
    def list_agents(self):
        """List agents (common operation)."""
        self.client.get("/api/v1/agents", headers=self.headers)

    @task(5)
    def get_agent(self):
        """Get a specific agent."""
        # You would need to have a known agent ID for this
        # For now, we'll just test the endpoint structure
        response = self.client.get("/api/v1/agents", headers=self.headers)
        if response.status_code == 200:
            agents = response.json().get("agents", [])
            if agents:
                agent_id = agents[0]["id"]
                self.client.get(f"/api/v1/agents/{agent_id}", headers=self.headers)

    @task(3)
    def create_agent(self):
        """Create a new agent."""
        agent_data = {
            "name": f"Load Test Agent {random.randint(1, 10000)}",
            "description": "Agent created during load testing",
            "system_prompt": "You are a helpful assistant for load testing.",
            "model_provider": "anthropic",
            "model_name": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        self.client.post("/api/v1/agents", json=agent_data, headers=self.headers)

    @task(8)
    def list_workflows(self):
        """List workflows."""
        self.client.get("/api/v1/workflows/workflows", headers=self.headers)

    @task(2)
    def list_mcp_servers(self):
        """List MCP servers."""
        self.client.get("/api/v1/mcp/servers", headers=self.headers)

    @task(5)
    def list_collections(self):
        """List RAG collections."""
        self.client.get("/api/v1/rag/collections", headers=self.headers)

    @task(1)
    def health_check(self):
        """Health check endpoint."""
        self.client.get("/health")

    @task(1)
    def readiness_check(self):
        """Readiness check endpoint."""
        self.client.get("/health/ready")


class ReadOnlyUser(HttpUser):
    """User that only performs read operations."""

    wait_time = between(0.5, 2)
    host = "http://localhost:8000"

    def on_start(self):
        """Login on start."""
        response = self.client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpass123",
            },
        )

        if response.status_code == 200:
            self.access_token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.access_token}"}
        else:
            self.access_token = None
            self.headers = {}

    @task(20)
    def list_agents(self):
        """List agents."""
        self.client.get("/api/v1/agents", headers=self.headers)

    @task(10)
    def list_workflows(self):
        """List workflows."""
        self.client.get("/api/v1/workflows/workflows", headers=self.headers)

    @task(5)
    def list_collections(self):
        """List collections."""
        self.client.get("/api/v1/rag/collections", headers=self.headers)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Run when test starts."""
    print("=" * 60)
    print("Starting load test for Agentic Platform")
    print(f"Host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Run when test stops."""
    print("=" * 60)
    print("Load test completed")
    print("=" * 60)
