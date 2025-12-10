"""Connector Registry - Loads and manages connector configurations from YAML."""

import logging
from pathlib import Path
from typing import Optional

import yaml

from .models import ConnectorConfig

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Registry that loads connector configurations from YAML files."""

    def __init__(self, config_dir: Path | str | None = None):
        """Initialize the registry.

        Args:
            config_dir: Directory containing connector YAML files.
                       Defaults to ./connectors/ relative to this file.
        """
        if config_dir is None:
            # Default to connectors/ directory next to registry module
            self._config_dir = Path(__file__).parent.parent / "connectors_config"
        else:
            self._config_dir = Path(config_dir)

        self._connectors: dict[str, ConnectorConfig] = {}
        self._loaded = False

    @property
    def config_dir(self) -> Path:
        """Get the configuration directory path."""
        return self._config_dir

    def load(self, force: bool = False) -> None:
        """Load all connector configurations from YAML files.

        Args:
            force: If True, reload even if already loaded.
        """
        if self._loaded and not force:
            return

        self._connectors.clear()

        if not self._config_dir.exists():
            logger.warning(f"Config directory does not exist: {self._config_dir}")
            self._config_dir.mkdir(parents=True, exist_ok=True)
            self._loaded = True
            return

        # Load all .yaml and .yml files
        for yaml_file in self._config_dir.glob("*.yaml"):
            self._load_file(yaml_file)
        for yaml_file in self._config_dir.glob("*.yml"):
            self._load_file(yaml_file)

        logger.info(f"Loaded {len(self._connectors)} connectors from {self._config_dir}")
        self._loaded = True

    def _load_file(self, yaml_file: Path) -> None:
        """Load a single YAML configuration file."""
        try:
            with open(yaml_file, "r") as f:
                data = yaml.safe_load(f)

            if data is None:
                logger.warning(f"Empty YAML file: {yaml_file}")
                return

            config = ConnectorConfig(**data)
            self._connectors[config.id] = config
            logger.debug(f"Loaded connector: {config.id} from {yaml_file.name}")

        except yaml.YAMLError as e:
            logger.error(f"YAML parse error in {yaml_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load {yaml_file}: {e}")

    def get(self, connector_id: str) -> Optional[ConnectorConfig]:
        """Get a connector configuration by ID.

        Args:
            connector_id: The unique connector identifier.

        Returns:
            ConnectorConfig if found, None otherwise.
        """
        self.load()
        return self._connectors.get(connector_id)

    def list_all(self) -> list[ConnectorConfig]:
        """Get all connector configurations.

        Returns:
            List of all registered connectors.
        """
        self.load()
        return list(self._connectors.values())

    def list_published(self) -> list[ConnectorConfig]:
        """Get only published connectors (for customer library view).

        Returns:
            List of published connectors.
        """
        self.load()
        return [c for c in self._connectors.values() if c.status == "published"]

    def save(self, config: ConnectorConfig) -> None:
        """Save a connector configuration to YAML.

        Args:
            config: The connector configuration to save.
        """
        self._config_dir.mkdir(parents=True, exist_ok=True)

        yaml_file = self._config_dir / f"{config.id}.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(
                config.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

        self._connectors[config.id] = config
        logger.info(f"Saved connector: {config.id} to {yaml_file}")

    def delete(self, connector_id: str) -> bool:
        """Delete a connector configuration.

        Args:
            connector_id: The connector ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        self.load()

        if connector_id not in self._connectors:
            return False

        yaml_file = self._config_dir / f"{connector_id}.yaml"
        if yaml_file.exists():
            yaml_file.unlink()

        del self._connectors[connector_id]
        logger.info(f"Deleted connector: {connector_id}")
        return True


# Global registry instance
_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry instance."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry
