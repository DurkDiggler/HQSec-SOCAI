"""MCP Server Registry for managing multiple MCP servers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .kali_tools import KaliMCPServer
from .vulnerability_scanner import VulnerabilityMCPServer

logger = logging.getLogger(__name__)


class MCPServerRegistry:
    """Registry for managing multiple MCP servers."""
    
    def __init__(self):
        self.servers = {
            "kali": KaliMCPServer(),
            "vulnerability": VulnerabilityMCPServer()
        }
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def execute_command(
        self, 
        server_name: str, 
        command: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a command on a specific MCP server."""
        try:
            if server_name not in self.servers:
                raise ValueError(f"Unknown server: {server_name}")
            
            server = self.servers[server_name]
            return await server.execute_command(command, parameters or {})
            
        except Exception as e:
            logger.error(f"Command execution failed on {server_name}: {e}")
            return {"error": str(e), "success": False}
    
    async def scan_target(self, target: str, scan_type: str = "basic") -> Dict[str, Any]:
        """Perform a scan on a target using appropriate MCP server."""
        try:
            if scan_type in ["nmap", "port_scan", "service_scan"]:
                return await self.execute_command("kali", "nmap_scan", {"target": target, "scan_type": scan_type})
            elif scan_type in ["vulnerability", "vuln_scan"]:
                return await self.execute_command("vulnerability", "vuln_scan", {"target": target})
            else:
                # Default to basic nmap scan
                return await self.execute_command("kali", "nmap_scan", {"target": target, "scan_type": "basic"})
                
        except Exception as e:
            logger.error(f"Target scan failed: {e}")
            return {"error": str(e), "success": False}
    
    async def test_exploit(
        self, 
        target: str, 
        vulnerability: str, 
        exploit_type: str = "basic"
    ) -> Dict[str, Any]:
        """Test an exploit against a target."""
        try:
            return await self.execute_command(
                "kali", 
                "test_exploit", 
                {
                    "target": target,
                    "vulnerability": vulnerability,
                    "exploit_type": exploit_type
                }
            )
            
        except Exception as e:
            logger.error(f"Exploit test failed: {e}")
            return {"error": str(e), "success": False}
    
    async def analyze_with_ai(self, alert_id: int) -> Dict[str, Any]:
        """Analyze an alert using AI and MCP tools."""
        try:
            # This would integrate with your existing alert system
            # For now, return a placeholder
            return {
                "alert_id": alert_id,
                "ai_analysis": "AI analysis placeholder",
                "mcp_tools_used": ["nmap", "vulnerability_scanner"],
                "recommendations": ["Run additional scans", "Check for vulnerabilities"],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"AI analysis with MCP tools failed: {e}")
            return {"error": str(e), "success": False}
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers."""
        status = {}
        
        for name, server in self.servers.items():
            try:
                server_status = await server.get_status()
                status[name] = {
                    "status": "online",
                    "details": server_status
                }
            except Exception as e:
                status[name] = {
                    "status": "offline",
                    "error": str(e)
                }
        
        return status
    
    async def run_offensive_test_suite(
        self, 
        target: str, 
        test_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run a complete offensive test suite."""
        results = []
        
        for scenario in test_scenarios:
            try:
                test_type = scenario.get("type", "basic")
                parameters = scenario.get("parameters", {})
                
                if test_type == "port_scan":
                    result = await self.scan_target(target, "nmap")
                elif test_type == "vulnerability_scan":
                    result = await self.scan_target(target, "vulnerability")
                elif test_type == "exploit_test":
                    result = await self.test_exploit(
                        target, 
                        parameters.get("vulnerability", "unknown"),
                        parameters.get("exploit_type", "basic")
                    )
                else:
                    result = {"error": f"Unknown test type: {test_type}", "success": False}
                
                results.append({
                    "scenario": scenario,
                    "result": result,
                    "success": result.get("success", False)
                })
                
            except Exception as e:
                results.append({
                    "scenario": scenario,
                    "result": {"error": str(e), "success": False},
                    "success": False
                })
        
        # Calculate overall success rate
        successful_tests = len([r for r in results if r["success"]])
        success_rate = (successful_tests / len(results)) * 100 if results else 0
        
        return {
            "target": target,
            "total_tests": len(results),
            "successful_tests": successful_tests,
            "success_rate": round(success_rate, 2),
            "results": results,
            "overall_status": "PASS" if success_rate >= 80 else "FAIL"
        }
    
    def get_available_commands(self) -> Dict[str, List[str]]:
        """Get available commands for each MCP server."""
        commands = {}
        
        for name, server in self.servers.items():
            commands[name] = server.get_available_commands()
        
        return commands
    
    def get_server_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Get capabilities of each MCP server."""
        capabilities = {}
        
        for name, server in self.servers.items():
            capabilities[name] = server.get_capabilities()
        
        return capabilities
