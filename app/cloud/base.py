from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class CloudStorageProvider(ABC):
    @abstractmethod
    async def upload_file(self, file_path: str, destination: str) -> str:
        pass
    
    @abstractmethod
    async def download_file(self, file_path: str, destination: str) -> bool:
        pass

class CloudDatabaseProvider(ABC):
    @abstractmethod
    async def get_connection_string(self) -> str:
        pass
    
    @abstractmethod
    async def create_database_instance(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def delete_database_instance(self, instance_id: str) -> bool:
        pass

class CloudDeploymentProvider(ABC):
    @abstractmethod
    async def deploy_application(self, config: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def scale_application(self, replicas: int) -> bool:
        pass
    
    @abstractmethod
    async def get_application_url(self) -> str:
        pass

class CloudSecretProvider(ABC):
    @abstractmethod
    async def get_secret(self, secret_name: str) -> Optional[str]:
        pass
    
    @abstractmethod
    async def set_secret(self, secret_name: str, value: str) -> bool:
        pass 