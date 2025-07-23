"""
Configuration Manager Module
Handles system configuration and settings
"""
import os
import yaml
import json
import configparser
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages system configuration from multiple sources"""
    
    def __init__(self, config_dir: str = 'config'):
        self.config_dir = config_dir
        self.fallback_config_dir = 'dados'
        self.config_cache = {}
        
        # Ensure config directory exists
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        
        # Create default configurations
        self.create_default_configs()
    
    def create_default_configs(self):
        """Create default configuration files"""
        configs = {
            'app_config.yaml': self._get_default_app_config(),
            'database.yaml': self._get_default_database_config(),
            'ui_config.yaml': self._get_default_ui_config()
        }
        
        for config_name, content in configs.items():
            config_path = os.path.join(self.config_dir, config_name)
            if not os.path.exists(config_path):
                self._save_yaml_config(config_path, content)
                logger.info(f"Created default config: {config_name}")
    
    def _get_default_app_config(self) -> Dict[str, Any]:
        """Default application configuration"""
        return {
            'app': {
                'name': 'Sistema PDV - Madeireira Maria Luiza',
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'business': {
                'nome_empresa': 'MADEIREIRA MARIA LUIZA',
                'endereco': 'Av. Dr. Cládio Gueiros Leite, 6311',
                'cidade': 'Pau Amarelo - PE',
                'telefone': '(81) 3011-5515',
                'cnpj': '48.905.025/001-61',
                'email': 'contato@madeireiramariluiza.com.br'
            },
            'frete': {
                'valor_por_kg': 3.50,
                'frete_minimo': 15.00,
                'calculo_automatico': True
            },
            'sync': {
                'auto_sync_enabled': True,
                'sync_interval_minutes': 5,
                'max_retry_attempts': 3,
                'timeout_seconds': 30
            },
            'reports': {
                'output_directory': 'output',
                'default_format': 'excel',
                'include_timestamp': True,
                'auto_open': False
            },
            'receipts': {
                'auto_number': True,
                'print_copies': 2,
                'default_template': 'standard'
            }
        }
    
    def _get_default_database_config(self) -> Dict[str, Any]:
        """Default database configuration"""
        return {
            'sic': {
                'servidor': 'localhost\\SQLEXPRESS',
                'banco': 'SIC',
                'usuario': 'sa',
                'senha': '',
                'porta': 1433,
                'timeout': 30,
                'driver': 'ODBC Driver 17 for SQL Server'
            },
            'local': {
                'database_path': 'dados/produtos_sic.db',
                'backup_enabled': True,
                'backup_interval_hours': 24,
                'max_backups': 7
            },
            'tables': {
                'produtos': 'PRODUTOS',
                'estoque': 'ESTOQUE',
                'categorias': 'CATEGORIAS',
                'marcas': 'MARCAS',
                'clientes': 'CLIENTES'
            }
        }
    
    def _get_default_ui_config(self) -> Dict[str, Any]:
        """Default UI configuration"""
        return {
            'window': {
                'width': 1200,
                'height': 800,
                'resizable': True,
                'center_on_screen': True
            },
            'theme': {
                'primary_color': '#2c3e50',
                'secondary_color': '#3498db',
                'background_color': '#ecf0f1',
                'text_color': '#2c3e50',
                'font_family': 'Arial',
                'font_size': 11
            },
            'grid': {
                'rows_per_page': 50,
                'auto_refresh': True,
                'refresh_interval': 30
            },
            'notifications': {
                'show_sync_status': True,
                'show_low_stock_alerts': True,
                'auto_hide_delay': 5000
            }
        }
    
    def get_config(self, config_name: str, section: str = None) -> Union[Dict[str, Any], Any]:
        """Get configuration data"""
        try:
            # Check cache first
            cache_key = f"{config_name}:{section}" if section else config_name
            if cache_key in self.config_cache:
                return self.config_cache[cache_key]
            
            # Try YAML config first
            yaml_path = os.path.join(self.config_dir, f"{config_name}.yaml")
            if os.path.exists(yaml_path):
                config_data = self._load_yaml_config(yaml_path)
                
                if section:
                    result = config_data.get(section, {})
                else:
                    result = config_data
                
                self.config_cache[cache_key] = result
                return result
            
            # Fallback to INI config (for backward compatibility)
            ini_path = os.path.join(self.fallback_config_dir, f"{config_name}.ini")
            if os.path.exists(ini_path):
                config_data = self._load_ini_config(ini_path)
                
                if section:
                    result = config_data.get(section, {})
                else:
                    result = config_data
                
                self.config_cache[cache_key] = result
                return result
            
            # Return empty dict if no config found
            logger.warning(f"Configuration not found: {config_name}")
            return {} if section else {}
            
        except Exception as e:
            logger.error(f"Error loading config {config_name}: {e}")
            return {} if section else {}
    
    def set_config(self, config_name: str, section: str, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
            
            # Load existing config or create new
            if os.path.exists(config_path):
                config_data = self._load_yaml_config(config_path)
            else:
                config_data = {}
            
            # Set the value
            if section not in config_data:
                config_data[section] = {}
            
            config_data[section][key] = value
            
            # Save the config
            self._save_yaml_config(config_path, config_data)
            
            # Clear cache
            cache_key = f"{config_name}:{section}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            logger.info(f"Updated config {config_name}.{section}.{key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting config {config_name}.{section}.{key}: {e}")
            return False
    
    def update_config_section(self, config_name: str, section: str, data: Dict[str, Any]) -> bool:
        """Update entire configuration section"""
        try:
            config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
            
            # Load existing config or create new
            if os.path.exists(config_path):
                config_data = self._load_yaml_config(config_path)
            else:
                config_data = {}
            
            # Update the section
            config_data[section] = data
            
            # Save the config
            self._save_yaml_config(config_path, config_data)
            
            # Clear cache
            cache_key = f"{config_name}:{section}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            
            logger.info(f"Updated config section {config_name}.{section}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config section {config_name}.{section}: {e}")
            return False
    
    def _load_yaml_config(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _save_yaml_config(self, file_path: str, data: Dict[str, Any]):
        """Save YAML configuration file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    def _load_ini_config(self, file_path: str) -> Dict[str, Dict[str, str]]:
        """Load INI configuration file (for backward compatibility)"""
        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')
        
        result = {}
        for section in config.sections():
            result[section] = dict(config[section])
        
        return result
    
    def clear_cache(self):
        """Clear configuration cache"""
        self.config_cache.clear()
        logger.info("Configuration cache cleared")
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get application information"""
        return self.get_config('app_config', 'app')
    
    def get_business_info(self) -> Dict[str, Any]:
        """Get business information"""
        return self.get_config('app_config', 'business')
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get_config('database')
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.get_config('ui_config')
    
    def export_config(self, output_path: str) -> bool:
        """Export all configurations to a single file"""
        try:
            all_configs = {}
            
            # Get all config files
            for file in os.listdir(self.config_dir):
                if file.endswith('.yaml'):
                    config_name = file[:-5]  # Remove .yaml extension
                    all_configs[config_name] = self.get_config(config_name)
            
            # Save to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(all_configs, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"Exported all configurations to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configurations: {e}")
            return False
    
    def import_config(self, input_path: str) -> bool:
        """Import configurations from a file"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                all_configs = yaml.safe_load(f)
            
            # Save each configuration
            for config_name, config_data in all_configs.items():
                config_path = os.path.join(self.config_dir, f"{config_name}.yaml")
                self._save_yaml_config(config_path, config_data)
            
            # Clear cache
            self.clear_cache()
            
            logger.info(f"Imported configurations from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configurations: {e}")
            return False