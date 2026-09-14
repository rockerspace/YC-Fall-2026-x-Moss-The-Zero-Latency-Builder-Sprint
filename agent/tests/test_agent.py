import pytest
import asyncio
from agent import MossContextEngine, SCENARIOS

@pytest.mark.asyncio
async def test_moss_context_retrieval():
    """Test the Moss Context Engine retrieves valid context from SQLite."""
    engine = MossContextEngine(api_key="test-key")
    
    # We are using CURRENT_SCENARIO from agent.py, which defaults to 'healthcare'
    # Let's ensure it doesn't return 'CRITICAL' error string
    context = await engine.retrieve_context(user_id="test_user", query="help")
    
    assert "User ID: test_user" in context
    assert "CRITICAL" not in context
    assert len(context) > 20

def test_personas_loaded():
    """Ensure personas are loaded correctly from JSON."""
    assert isinstance(SCENARIOS, dict)
    assert "healthcare" in SCENARIOS
    assert "role" in SCENARIOS["healthcare"]
