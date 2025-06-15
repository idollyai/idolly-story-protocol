"""Story Protocol Client Wrapper for Python SDK"""
import os
from typing import Dict, List, Optional, Any
from web3 import Web3
from story_protocol_python_sdk import StoryClient
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class StoryProtocolClient:
    """Wrapper for Story Protocol Python SDK Client"""
    
    def __init__(self, private_key: Optional[str] = None):
        """Initialize Story Protocol client with configuration"""
        self.private_key = private_key or settings.WALLET_PRIVATE_KEY
        self.rpc_url = settings.RPC_PROVIDER_URL
        self.chain_id = settings.CHAIN_ID
        
        # Initialize Story Protocol client
        self.client = StoryClient(
            account=self.private_key,
            transport=Web3.HTTPProvider(self.rpc_url),
            chain_id=self.chain_id
        )
        
        # Contract addresses
        self.spg_nft_contract = settings.SPG_NFT_CONTRACT
        self.pil_license_template = settings.PIL_LICENSE_TEMPLATE
        self.royalty_policy_lap = settings.ROYALTY_POLICY_LAP
        self.wip_token = settings.WIP_TOKEN_ADDRESS
        
        logger.info(f"Story Protocol client initialized for chain: {self.chain_id}")
    
    async def register_idol_ip(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register an Idol as an IP Asset on Story Protocol
        
        Args:
            metadata: Dictionary containing idol metadata
                - name: Idol name
                - description: Idol description
                - personality: Idol personality traits
                - image_uri: IPFS URI for idol image
                - attributes: Additional attributes
        
        Returns:
            Dictionary containing:
                - ip_id: The registered IP Asset ID
                - token_id: The minted NFT token ID
                - tx_hash: Transaction hash
        """
        try:
            # Prepare IP metadata
            ip_metadata = {
                "ip_metadata_uri": metadata.get("metadata_uri"),
                "ip_metadata_hash": Web3.to_hex(Web3.keccak(text=metadata.get("metadata_uri", ""))),
                "nft_metadata_uri": metadata.get("nft_metadata_uri"),
                "nft_metadata_hash": Web3.to_hex(Web3.keccak(text=metadata.get("nft_metadata_uri", "")))
            }
            
            # Mint and register IP Asset
            response = self.client.IPAsset.mint_and_register_ip_asset_with_pil_terms(
                spg_nft_contract=self.spg_nft_contract,
                terms=[self._get_default_license_terms()],
                allow_duplicates=False,
                ip_metadata=ip_metadata,
                tx_options={"wait_for_transaction": True}
            )
            
            logger.info(f"Idol IP registered: {response['ip_id']}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to register idol IP: {str(e)}")
            raise
    
    async def create_derivative_content(
        self, 
        parent_ip_id: str, 
        content_metadata: Dict[str, Any],
        license_token_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create derivative content from a parent IP
        
        Args:
            parent_ip_id: The parent IP Asset ID
            content_metadata: Metadata for the derivative content
            license_token_ids: Optional license token IDs if using license tokens
        
        Returns:
            Dictionary containing derivative IP information
        """
        try:
            if license_token_ids:
                # Register derivative using license tokens
                response = self.client.IPAsset.register_derivative_with_license_tokens(
                    child_ip_id=content_metadata["child_ip_id"],
                    license_token_ids=license_token_ids,
                    max_rts=100_000_000,  # Default max royalty tokens
                    tx_options={"wait_for_transaction": True}
                )
            else:
                # Register derivative directly with parent's license terms
                response = self.client.IPAsset.register_derivative(
                    child_ip_id=content_metadata["child_ip_id"],
                    parent_ip_ids=[parent_ip_id],
                    license_terms_ids=content_metadata.get("license_terms_ids", ["1"]),
                    max_minting_fee=0,
                    max_rts=100_000_000,
                    max_revenue_share=100,
                    tx_options={"wait_for_transaction": True}
                )
            
            logger.info(f"Derivative content created: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create derivative content: {str(e)}")
            raise
    
    async def mint_license_tokens(
        self, 
        ip_id: str, 
        amount: int = 1,
        receiver: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mint license tokens for an IP Asset
        
        Args:
            ip_id: The IP Asset ID to mint licenses for
            amount: Number of license tokens to mint
            receiver: Optional receiver address (defaults to caller)
        
        Returns:
            Dictionary containing license token information
        """
        try:
            response = self.client.License.mint_license_tokens(
                licensor_ip_id=ip_id,
                license_template=self.pil_license_template,
                license_terms_id="1",  # Default terms ID
                amount=amount,
                receiver=receiver,
                max_minting_fee=0,
                max_revenue_share=100,
                tx_options={"wait_for_transaction": True}
            )
            
            logger.info(f"Minted {amount} license tokens for IP: {ip_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to mint license tokens: {str(e)}")
            raise
    
    async def claim_royalties(self, ip_id: str, child_ip_ids: List[str]) -> Dict[str, Any]:
        """
        Claim accumulated royalties for an IP Asset
        
        Args:
            ip_id: The ancestor IP ID claiming royalties
            child_ip_ids: List of child IP IDs to claim from
        
        Returns:
            Dictionary containing claimed token amounts
        """
        try:
            response = self.client.Royalty.claim_all_revenue(
                ancestor_ip_id=ip_id,
                claimer=ip_id,  # IP Account claims for itself
                currency_tokens=[self.wip_token],
                child_ip_ids=child_ip_ids,
                royalty_policies=[self.royalty_policy_lap],
                claim_options={
                    "auto_transfer_all_claimed_tokens_from_ip": True,
                    "auto_unwrap_ip_tokens": True
                },
                tx_options={"wait_for_transaction": True}
            )
            
            logger.info(f"Claimed royalties for IP: {ip_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to claim royalties: {str(e)}")
            raise
    
    def _get_default_license_terms(self) -> Dict[str, Any]:
        """Get default commercial remix license terms"""
        return {
            "terms": {
                "transferable": True,
                "royalty_policy": self.royalty_policy_lap,
                "default_minting_fee": 0,
                "expiration": 0,
                "commercial_use": True,
                "commercial_attribution": True,
                "commercializer_checker": "0x0000000000000000000000000000000000000000",
                "commercializer_checker_data": "0x0000000000000000000000000000000000000000",
                "commercial_rev_share": 10,  # 10% revenue share
                "commercial_rev_ceiling": 0,
                "derivatives_allowed": True,
                "derivatives_attribution": True,
                "derivatives_approval": False,
                "derivatives_reciprocal": True,
                "derivative_rev_ceiling": 0,
                "currency": self.wip_token,
                "uri": ""
            },
            "licensing_config": {
                "is_set": False,
                "minting_fee": 0,
                "licensing_hook": "0x0000000000000000000000000000000000000000",
                "hook_data": "0x0000000000000000000000000000000000000000",
                "commercial_rev_share": 0,
                "disabled": False,
                "expect_minimum_group_reward_share": 0,
                "expect_group_reward_pool": "0x0000000000000000000000000000000000000000"
            }
        }
    
    async def create_spg_nft_collection(
        self, 
        name: str, 
        symbol: str,
        is_public_minting: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new SPG NFT collection
        
        Args:
            name: Collection name
            symbol: Collection symbol
            is_public_minting: Whether public minting is allowed
        
        Returns:
            Dictionary containing the new collection contract address
        """
        try:
            response = self.client.NFTClient.create_nft_collection(
                name=name,
                symbol=symbol,
                is_public_minting=is_public_minting,
                mint_open=True,
                mint_fee_recipient="0x0000000000000000000000000000000000000000",
                contract_uri="",
                tx_options={"wait_for_transaction": True}
            )
            
            logger.info(f"Created SPG NFT collection: {response['nft_contract']}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create NFT collection: {str(e)}")
            raise