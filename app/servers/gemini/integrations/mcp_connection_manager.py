"""
MCP Connection Manager for application-level connection management
Handles persistent MCP connections to avoid task context issues
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPConnectionManager:
    """Manages persistent MCP connections at application level"""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None
        self._lock = asyncio.Lock()
        self._initialized = False
        self._stdio_context = None
        self._session_context = None
        
    async def initialize(self) -> None:
        """Initialize the MCP connection at application startup"""
        if self._initialized:
            logger.warning("MCP connection already initialized")
            return
            
        try:
            logger.info("Initializing MCP connection...")
            
            # Server parameters for MCP
            server_params = StdioServerParameters(
                command="python",
                args=["run_mcp.py"],
            )
            
            # Create the stdio client connection
            # Store the context manager for proper cleanup
            self._stdio_context = stdio_client(server_params)
            self.read_stream, self.write_stream = await self._stdio_context.__aenter__()
            
            # Create the client session
            self._session_context = ClientSession(self.read_stream, self.write_stream)
            self.session = await self._session_context.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            self._initialized = True
            logger.info("MCP connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP connection: {str(e)}", exc_info=True)
            raise
    
    async def shutdown(self) -> None:
        """Clean shutdown of MCP connection"""
        if not self._initialized:
            return
            
        try:
            logger.info("Shutting down MCP connection...")
            
            # Clean up session
            if self._session_context and self.session:
                await self._session_context.__aexit__(None, None, None)
                
            # Clean up stdio connection
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)
                
            self._initialized = False
            self.session = None
            self.read_stream = None
            self.write_stream = None
            
            logger.info("MCP connection shut down successfully")
            
        except Exception as e:
            logger.error(f"Error during MCP shutdown: {str(e)}", exc_info=True)
    
    @asynccontextmanager
    async def get_session(self):
        """Get the MCP session with thread-safe access"""
        if not self._initialized:
            raise RuntimeError("MCP connection not initialized. Call initialize() first.")
            
        async with self._lock:
            yield self.session
    
    def is_initialized(self) -> bool:
        """Check if MCP connection is initialized"""
        return self._initialized


class MCPConnectionPool:
    """
    Manages a pool of MCP connections for handling concurrent requests
    This is an alternative approach if single connection becomes a bottleneck
    """
    
    def __init__(self, pool_size: int = 3):
        self.pool_size = pool_size
        self.connections = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
        self._connections_data = []
        
    async def initialize(self) -> None:
        """Initialize the connection pool"""
        if self._initialized:
            return
            
        logger.info(f"Initializing MCP connection pool with {self.pool_size} connections...")
        
        for i in range(self.pool_size):
            try:
                conn_data = await self._create_connection(i)
                self._connections_data.append(conn_data)
                await self.connections.put(conn_data['session'])
            except Exception as e:
                logger.error(f"Failed to create connection {i}: {str(e)}")
                # Clean up any created connections
                await self.shutdown()
                raise
                
        self._initialized = True
        logger.info("MCP connection pool initialized successfully")
        
    async def _create_connection(self, index: int) -> Dict[str, Any]:
        """Create a single MCP connection"""
        server_params = StdioServerParameters(
            command="python",
            args=["run_mcp.py"],
        )
        
        # Create the connection with proper context management
        stdio_ctx = stdio_client(server_params)
        read, write = await stdio_ctx.__aenter__()
        
        session_ctx = ClientSession(read, write)
        session = await session_ctx.__aenter__()
        await session.initialize()
        
        return {
            'index': index,
            'session': session,
            'stdio_ctx': stdio_ctx,
            'session_ctx': session_ctx,
            'read': read,
            'write': write
        }
    
    async def shutdown(self) -> None:
        """Shutdown all connections in the pool"""
        logger.info("Shutting down MCP connection pool...")
        
        for conn_data in self._connections_data:
            try:
                # Clean up session
                if 'session_ctx' in conn_data:
                    await conn_data['session_ctx'].__aexit__(None, None, None)
                    
                # Clean up stdio
                if 'stdio_ctx' in conn_data:
                    await conn_data['stdio_ctx'].__aexit__(None, None, None)
                    
            except Exception as e:
                logger.error(f"Error shutting down connection {conn_data.get('index', '?')}: {str(e)}")
                
        self._connections_data.clear()
        self._initialized = False
        
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self._initialized:
            raise RuntimeError("MCP connection pool not initialized")
            
        # Get connection from pool (blocks if none available)
        session = await self.connections.get()
        try:
            yield session
        finally:
            # Return connection to pool
            await self.connections.put(session)


# Global singleton instance
_mcp_manager: Optional[MCPConnectionManager] = None


def get_mcp_manager() -> MCPConnectionManager:
    """Get the global MCP connection manager"""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPConnectionManager()
    return _mcp_manager