"""Agent registry for managing multiple agents."""

from typing import Dict, List, Optional
from loguru import logger

from digital_humain.core.agent import BaseAgent, AgentConfig, AgentRole


class AgentRegistry:
    """
    Registry for managing multiple agents.
    
    Provides agent lookup, registration, and lifecycle management.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, BaseAgent] = {}
        self._configs: Dict[str, AgentConfig] = {}
        logger.info("Initialized AgentRegistry")
    
    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance to register
        """
        agent_name = agent.config.name
        
        if agent_name in self._agents:
            logger.warning(f"Agent {agent_name} already registered, replacing")
        
        self._agents[agent_name] = agent
        self._configs[agent_name] = agent.config
        
        logger.info(f"Registered agent: {agent_name} ({agent.config.role.value})")
    
    def unregister(self, agent_name: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_name: Name of agent to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if agent_name in self._agents:
            del self._agents[agent_name]
            del self._configs[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
            return True
        
        logger.warning(f"Agent not found: {agent_name}")
        return False
    
    def get(self, agent_name: str) -> Optional[BaseAgent]:
        """
        Get an agent by name.
        
        Args:
            agent_name: Name of agent to retrieve
            
        Returns:
            Agent instance or None if not found
        """
        return self._agents.get(agent_name)
    
    def get_by_role(self, role: AgentRole) -> List[BaseAgent]:
        """
        Get all agents with a specific role.
        
        Args:
            role: Agent role to filter by
            
        Returns:
            List of matching agents
        """
        return [
            agent for agent in self._agents.values()
            if agent.config.role == role
        ]
    
    def list_agents(self) -> List[str]:
        """
        List all registered agent names.
        
        Returns:
            List of agent names
        """
        return list(self._agents.keys())
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict]:
        """
        Get information about an agent.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            Dictionary with agent information
        """
        if agent_name not in self._agents:
            return None
        
        config = self._configs[agent_name]
        agent = self._agents[agent_name]
        
        return {
            "name": config.name,
            "role": config.role.value,
            "model": config.model,
            "tools": config.tools,
            "max_iterations": config.max_iterations,
            "has_state": agent.state is not None
        }
    
    def list_agents_info(self) -> List[Dict]:
        """
        List information about all registered agents.
        
        Returns:
            List of agent information dictionaries
        """
        return [
            self.get_agent_info(name)
            for name in self._agents.keys()
        ]
    
    def clear(self) -> None:
        """Clear all registered agents."""
        count = len(self._agents)
        self._agents.clear()
        self._configs.clear()
        logger.info(f"Cleared {count} agents from registry")
