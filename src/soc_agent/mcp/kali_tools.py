"""Kali Linux MCP Server integration."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

from ..config import SETTINGS

logger = logging.getLogger(__name__)


class KaliMCPServer:
    """Integration with Kali Linux MCP Server."""
    
    def __init__(self):
        self.base_url = getattr(SETTINGS, 'kali_mcp_url', 'http://localhost:5000')
        self.timeout = getattr(SETTINGS, 'mcp_timeout', 30)
        self.session = None
    
    async def execute_command(
        self, 
        command: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a command on the Kali MCP server."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Build command based on type
            cmd = self._build_command(command, parameters or {})
            
            # Execute via MCP server
            async with self.session.post(
                f"{self.base_url}/run",
                json={"cmd": cmd},
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "command": cmd,
                        "output": result.get("output", ""),
                        "server": "kali"
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "command": cmd,
                        "server": "kali"
                    }
                    
        except Exception as e:
            logger.error(f"Kali MCP command execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "server": "kali"
            }
    
    def _build_command(self, command: str, parameters: Dict[str, Any]) -> str:
        """Build the actual command to execute."""
        if command == "nmap_scan":
            return self._build_nmap_command(parameters)
        elif command == "test_exploit":
            return self._build_exploit_command(parameters)
        elif command == "web_scan":
            return self._build_web_scan_command(parameters)
        elif command == "brute_force":
            return self._build_brute_force_command(parameters)
        else:
            return command
    
    def _build_nmap_command(self, parameters: Dict[str, Any]) -> str:
        """Build nmap command."""
        target = parameters.get("target", "localhost")
        scan_type = parameters.get("scan_type", "basic")
        
        if scan_type == "basic":
            return f"nmap -sS -O {target}"
        elif scan_type == "aggressive":
            return f"nmap -A -sS -sV -O {target}"
        elif scan_type == "stealth":
            return f"nmap -sS -f -T2 {target}"
        elif scan_type == "udp":
            return f"nmap -sU {target}"
        elif scan_type == "vulnerability":
            return f"nmap --script vuln {target}"
        else:
            return f"nmap {target}"
    
    def _build_exploit_command(self, parameters: Dict[str, Any]) -> str:
        """Build exploit testing command."""
        target = parameters.get("target", "localhost")
        vulnerability = parameters.get("vulnerability", "unknown")
        exploit_type = parameters.get("exploit_type", "basic")
        
        if exploit_type == "metasploit":
            return f"msfconsole -q -x 'use {vulnerability}; set RHOSTS {target}; run'"
        elif exploit_type == "custom":
            return f"python3 /opt/exploits/{vulnerability}.py {target}"
        else:
            return f"echo 'Exploit test for {vulnerability} on {target}'"
    
    def _build_web_scan_command(self, parameters: Dict[str, Any]) -> str:
        """Build web scanning command."""
        target = parameters.get("target", "localhost")
        scan_type = parameters.get("scan_type", "basic")
        
        if scan_type == "nikto":
            return f"nikto -h {target}"
        elif scan_type == "gobuster":
            return f"gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt"
        elif scan_type == "wpscan":
            return f"wpscan --url {target}"
        else:
            return f"curl -I {target}"
    
    def _build_brute_force_command(self, parameters: Dict[str, Any]) -> str:
        """Build brute force command."""
        target = parameters.get("target", "localhost")
        service = parameters.get("service", "ssh")
        username = parameters.get("username", "admin")
        wordlist = parameters.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        
        if service == "ssh":
            return f"hydra -l {username} -P {wordlist} ssh://{target}"
        elif service == "ftp":
            return f"hydra -l {username} -P {wordlist} ftp://{target}"
        elif service == "http":
            return f"hydra -l {username} -P {wordlist} http-get://{target}/login"
        else:
            return f"echo 'Brute force test for {service} on {target}'"
    
    async def nmap_scan(
        self, 
        target: str, 
        scan_type: str = "basic",
        ports: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform nmap scan."""
        parameters = {
            "target": target,
            "scan_type": scan_type,
            "ports": ports
        }
        return await self.execute_command("nmap_scan", parameters)
    
    async def test_exploit(
        self, 
        target: str, 
        vulnerability: str, 
        exploit_type: str = "basic"
    ) -> Dict[str, Any]:
        """Test an exploit."""
        parameters = {
            "target": target,
            "vulnerability": vulnerability,
            "exploit_type": exploit_type
        }
        return await self.execute_command("test_exploit", parameters)
    
    async def web_scan(
        self, 
        target: str, 
        scan_type: str = "nikto"
    ) -> Dict[str, Any]:
        """Perform web scan."""
        parameters = {
            "target": target,
            "scan_type": scan_type
        }
        return await self.execute_command("web_scan", parameters)
    
    async def brute_force(
        self, 
        target: str, 
        service: str = "ssh",
        username: str = "admin"
    ) -> Dict[str, Any]:
        """Perform brute force attack."""
        parameters = {
            "target": target,
            "service": service,
            "username": username
        }
        return await self.execute_command("brute_force", parameters)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(
                f"{self.base_url}/status",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return {"status": "online", "response_time": "< 1s"}
                else:
                    return {"status": "error", "code": response.status}
                    
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    def get_available_commands(self) -> List[str]:
        """Get available commands."""
        return [
            "nmap_scan",
            "test_exploit", 
            "web_scan",
            "brute_force"
        ]
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        return {
            "name": "Kali Linux MCP Server",
            "version": "1.0.0",
            "tools": [
                "nmap", "metasploit", "hydra", "nikto", 
                "gobuster", "wpscan", "sqlmap"
            ],
            "scan_types": [
                "port_scan", "vulnerability_scan", "web_scan",
                "brute_force", "exploit_test"
            ],
            "supported_protocols": ["tcp", "udp", "http", "https", "ssh", "ftp"],
            "max_targets": 1000,
            "concurrent_scans": 10
        }
    
    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None
