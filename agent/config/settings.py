from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Story Protocol Configuration
    RPC_PROVIDER_URL: str = "https://aeneid.storyrpc.io"
    CHAIN_ID: str = "aeneid"
    WALLET_PRIVATE_KEY: str
    
    # Story Protocol Contracts (Aeneid Testnet)
    SPG_NFT_CONTRACT: str = "0xc32A8a0FF3beDDDa58393d022aF433e78739FAbc"  # Public SPG for testing
    PIL_LICENSE_TEMPLATE: str = "0x2E896b0b2Fdb7457499B56AAaA4AE55BCB4Cd316"
    ROYALTY_POLICY_LAP: str = "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E"
    WIP_TOKEN_ADDRESS: str = "0x1514000000000000000000000000000000000000"
    
    # IPFS Configuration
    IPFS_API_URL: str = "/ip4/127.0.0.1/tcp/5001"
    PINATA_JWT: Optional[str] = None
    PINATA_GATEWAY: Optional[str] = None
    
    # AI Services
    OPENAI_API_KEY: str
    IMAGE_SERVER_URL: str
    BLOCKCHAIN_SERVER_URL: str
    
    # Database
    DATABASE_URL: str
    REDIS_URL: str
    
    # Agent Configuration
    MAX_CONCURRENT_AGENTS: int = 100
    CONTENT_GENERATION_INTERVAL: int = 7200  # 2 hours
    LICENSE_MANAGEMENT_INTERVAL: int = 86400  # 24 hours
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()