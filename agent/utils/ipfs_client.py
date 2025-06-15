"""IPFS Client for content storage"""
import logging
import json
import aiohttp
from typing import Dict, Any, Optional
import hashlib

from config.settings import settings

logger = logging.getLogger(__name__)

class IPFSClient:
    """Client for interacting with IPFS"""
    
    def __init__(self):
        self.pinata_jwt = settings.PINATA_JWT
        self.pinata_gateway = settings.PINATA_GATEWAY
        self.ipfs_api_url = settings.IPFS_API_URL
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def upload_json(self, data: Dict[str, Any]) -> str:
        """
        Upload JSON data to IPFS
        
        Args:
            data: Dictionary to upload
            
        Returns:
            IPFS hash (CID)
        """
        try:
            if self.pinata_jwt:
                return await self._upload_to_pinata(data)
            else:
                return await self._upload_to_local_ipfs(data)
                
        except Exception as e:
            logger.error(f"IPFS upload failed: {str(e)}")
            raise
    
    async def upload_file(self, file_path: str, content_type: str) -> str:
        """
        Upload a file to IPFS
        
        Args:
            file_path: Path to the file
            content_type: MIME type of the file
            
        Returns:
            IPFS hash (CID)
        """
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            if self.pinata_jwt:
                return await self._upload_file_to_pinata(file_data, content_type)
            else:
                return await self._upload_file_to_local_ipfs(file_data)
                
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise
    
    async def get_json(self, ipfs_hash: str) -> Dict[str, Any]:
        """
        Retrieve JSON data from IPFS
        
        Args:
            ipfs_hash: IPFS hash (CID)
            
        Returns:
            Retrieved data as dictionary
        """
        try:
            if self.pinata_gateway:
                url = f"{self.pinata_gateway}/ipfs/{ipfs_hash}"
            else:
                url = f"https://ipfs.io/ipfs/{ipfs_hash}"
            
            async with self.session.get(url) as response:
                data = await response.json()
                return data
                
        except Exception as e:
            logger.error(f"IPFS retrieval failed: {str(e)}")
            raise
    
    def calculate_hash(self, data: Dict[str, Any]) -> str:
        """
        Calculate hash of data for verification
        
        Args:
            data: Data to hash
            
        Returns:
            Hex hash string
        """
        json_str = json.dumps(data, sort_keys=True)
        return "0x" + hashlib.sha256(json_str.encode()).hexdigest()
    
    async def _upload_to_pinata(self, data: Dict[str, Any]) -> str:
        """Upload JSON to Pinata"""
        headers = {
            "Authorization": f"Bearer {self.pinata_jwt}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "pinataContent": data,
            "pinataMetadata": {
                "name": f"idolly-{data.get('content_id', 'unknown')}"
            }
        }
        
        async with self.session.post(
            "https://api.pinata.cloud/pinning/pinJSONToIPFS",
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            return result["IpfsHash"]
    
    async def _upload_to_local_ipfs(self, data: Dict[str, Any]) -> str:
        """Upload JSON to local IPFS node"""
        # For PoC, simulate IPFS upload
        # In production, use proper IPFS client
        json_str = json.dumps(data)
        
        # Simulate CID generation
        import base58
        hash_bytes = hashlib.sha256(json_str.encode()).digest()
        # Add multihash prefix for SHA-256
        multihash = b'\x12\x20' + hash_bytes
        cid = base58.b58encode(multihash).decode()
        
        logger.info(f"Simulated IPFS upload: {cid}")
        return cid
    
    async def _upload_file_to_pinata(self, file_data: bytes, content_type: str) -> str:
        """Upload file to Pinata"""
        headers = {
            "Authorization": f"Bearer {self.pinata_jwt}"
        }
        
        # Create form data
        form_data = aiohttp.FormData()
        form_data.add_field(
            'file',
            file_data,
            filename='file',
            content_type=content_type
        )
        
        async with self.session.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            headers=headers,
            data=form_data
        ) as response:
            result = await response.json()
            return result["IpfsHash"]
    
    async def _upload_file_to_local_ipfs(self, file_data: bytes) -> str:
        """Upload file to local IPFS node"""
        # For PoC, simulate file upload
        import base58
        hash_bytes = hashlib.sha256(file_data).digest()
        multihash = b'\x12\x20' + hash_bytes
        cid = base58.b58encode(multihash).decode()
        
        logger.info(f"Simulated file upload: {cid}")
        return cid