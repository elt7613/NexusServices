from tenacity import retry, stop_after_attempt, wait_exponential
import pybreaker
from pydantic_ai.usage import UsageLimits
import logging
from typing import Any, Dict, Optional
import asyncio
from functools import lru_cache

# Configure logging
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "retry_attempts": 20,
    "retry_multiplier": 1,
    "retry_max": 40,
    "circuit_fail_max": 20,
    "circuit_reset_timeout": 60
}

# Circuit breaker configuration
AGENT_BREAKER = pybreaker.CircuitBreaker(
    fail_max=DEFAULT_CONFIG["circuit_fail_max"], 
    reset_timeout=DEFAULT_CONFIG["circuit_reset_timeout"],
    name="agent_circuit",
    exclude=[KeyboardInterrupt, asyncio.CancelledError]
)

@lru_cache(maxsize=128)
def get_configured_retry(attempts: int = None, multiplier: int = None, max_wait: int = None):
    """
    Create a retry decorator with configurable parameters.
    
    Args:
        attempts: Maximum number of retry attempts
        multiplier: Base multiplier for exponential backoff
        max_wait: Maximum wait time between retries
        
    Returns:
        Configured retry decorator
    """
    attempts = attempts or DEFAULT_CONFIG["retry_attempts"]
    multiplier = multiplier or DEFAULT_CONFIG["retry_multiplier"]
    max_wait = max_wait or DEFAULT_CONFIG["retry_max"]
    
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=multiplier, max=max_wait),
        reraise=True,
        before_sleep=lambda retry_state: logger.info(
            f"Retrying agent execution: attempt {retry_state.attempt_number} after {retry_state.outcome.exception()}"
        )
    )

async def execute_agent_with_retries(
    agent,
    prompt: str,
    retry_config: Optional[Dict[str, int]] = None,
    usage_limits: Optional[UsageLimits] = None
) -> Any:
    """
    Execute an agent with retry capabilities.
    
    Args:
        agent: The agent to execute
        prompt: The prompt to send to the agent
        retry_config: Optional configuration for retries
        usage_limits: Optional usage limits
        
    Returns:
        The agent response
    
    Raises:
        Exception: Any exception raised by the agent after all retries are exhausted
    """
    retry_config = retry_config or {}
    retry_decorator = get_configured_retry(
        retry_config.get("attempts"),
        retry_config.get("multiplier"),
        retry_config.get("max_wait")
    )
    
    @retry_decorator
    async def _execute():
        try:
            logger.debug(f"Executing agent with prompt: {prompt[:50]}...")
            async with agent.run_mcp_servers():
                agent_response = await agent.run(
                    prompt, 
                    usage_limits=usage_limits or UsageLimits(request_limit=None)
                )
            return agent_response
        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}")
            raise
    
    return await _execute()

async def execute_agent_safely(
    agent,
    prompt: str,
    retry_config: Optional[Dict[str, int]] = None,
    circuit_config: Optional[Dict[str, int]] = None,
    usage_limits: Optional[UsageLimits] = None
) -> Any:
    """
    Execute an agent with both circuit breaker and retry capabilities.
    
    Args:
        agent: The agent to execute
        prompt: The prompt to send to the agent
        retry_config: Optional configuration for retries
        circuit_config: Optional configuration for the circuit breaker
        usage_limits: Optional usage limits
        
    Returns:
        The agent response
        
    Raises:
        pybreaker.CircuitBreakerError: When the circuit is open
        Exception: Any exception raised by the agent after all retries are exhausted
    """
    # Apply custom circuit breaker if configured
    if circuit_config:
        circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=circuit_config.get("fail_max", DEFAULT_CONFIG["circuit_fail_max"]),
            reset_timeout=circuit_config.get("reset_timeout", DEFAULT_CONFIG["circuit_reset_timeout"]),
            name="custom_agent_circuit",
            exclude=[KeyboardInterrupt, asyncio.CancelledError]
        )
    else:
        circuit_breaker = AGENT_BREAKER
        
    try:
        @circuit_breaker
        async def _execute_with_circuit_breaker():
            return await execute_agent_with_retries(agent, prompt, retry_config, usage_limits)
            
        return await _execute_with_circuit_breaker()
    except pybreaker.CircuitBreakerError:
        logger.critical("Agent circuit breaker open - too many failures")
        raise
    except Exception as e:
        logger.error(f"Agent execution failed after retries: {str(e)}")
        raise