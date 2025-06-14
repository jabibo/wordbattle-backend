from enum import Enum
from typing import Dict, Any, Optional, Type
from .base import (
    CloudStorageProvider,
    CloudDatabaseProvider,
    CloudDeploymentProvider,
    CloudSecretProvider
)
from .aws.providers import (
    AWSS3Provider,
    AWSRDSProvider,
    AWSECSProvider,
    AWSSecretsProvider
)
from .gcp.providers import (
    GCPStorageProvider,
    GCPCloudSQLProvider,
    GCPCloudRunProvider,
    GCPSecretsProvider
)

class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"

class CloudProviderFactory:
    def __init__(self, provider: CloudProvider, config: Dict[str, Any]):
        self.provider = provider
        self.config = config
        
        # Provider mappings
        self._storage_providers: Dict[CloudProvider, Type[CloudStorageProvider]] = {
            CloudProvider.AWS: AWSS3Provider,
            CloudProvider.GCP: GCPStorageProvider
        }
        
        self._database_providers: Dict[CloudProvider, Type[CloudDatabaseProvider]] = {
            CloudProvider.AWS: AWSRDSProvider,
            CloudProvider.GCP: GCPCloudSQLProvider
        }
        
        self._deployment_providers: Dict[CloudProvider, Type[CloudDeploymentProvider]] = {
            CloudProvider.AWS: AWSECSProvider,
            CloudProvider.GCP: GCPCloudRunProvider
        }
        
        self._secret_providers: Dict[CloudProvider, Type[CloudSecretProvider]] = {
            CloudProvider.AWS: AWSSecretsProvider,
            CloudProvider.GCP: GCPSecretsProvider
        }
    
    def get_storage_provider(self) -> Optional[CloudStorageProvider]:
        provider_class = self._storage_providers.get(self.provider)
        if provider_class:
            if self.provider == CloudProvider.AWS:
                return provider_class(bucket_name=self.config['bucket_name'])
            else:  # GCP
                return provider_class(bucket_name=self.config['bucket_name'])
        return None
    
    def get_database_provider(self) -> Optional[CloudDatabaseProvider]:
        provider_class = self._database_providers.get(self.provider)
        if provider_class:
            if self.provider == CloudProvider.AWS:
                return provider_class(region=self.config['region'])
            else:  # GCP
                return provider_class(
                    project=self.config['project_id'],
                    region=self.config['region']
                )
        return None
    
    def get_deployment_provider(self) -> Optional[CloudDeploymentProvider]:
        provider_class = self._deployment_providers.get(self.provider)
        if provider_class:
            if self.provider == CloudProvider.AWS:
                return provider_class(cluster=self.config['cluster_name'])
            else:  # GCP
                return provider_class(
                    project=self.config['project_id'],
                    region=self.config['region']
                )
        return None
    
    def get_secret_provider(self) -> Optional[CloudSecretProvider]:
        provider_class = self._secret_providers.get(self.provider)
        if provider_class:
            if self.provider == CloudProvider.AWS:
                return provider_class()
            else:  # GCP
                return provider_class(project=self.config['project_id'])
        return None 