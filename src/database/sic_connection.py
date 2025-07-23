"""
SIC Database Connection Module
Handles SQL Server connection to SIC system with connection pooling and error handling
"""
import pyodbc
import configparser
import os
import logging
from typing import Optional, Dict, Any, List
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SICConnection:
    """Manages connection to SIC SQL Server database"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join('config', 'database.yaml')
        self.fallback_config_path = os.path.join('dados', 'config.ini')
        self.connection_string = None
        self._connection = None
        self.is_connected = False
        self.connection_pool = []
        self.max_pool_size = 5
        
    def load_config(self) -> Dict[str, str]:
        """Load SIC database configuration"""
        # Try new YAML config first
        if os.path.exists(self.config_path):
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('sic', {})
        
        # Fallback to existing ini config
        if os.path.exists(self.fallback_config_path):
            config = configparser.ConfigParser()
            config.read(self.fallback_config_path, encoding='utf-8')
            return {
                'servidor': config['SIC']['servidor'],
                'banco': config['SIC']['banco'],
                'usuario': config['SIC']['usuario'],
                'senha': config['SIC']['senha'],
                'porta': config['SIC'].get('porta', '1433'),
                'timeout': config['SIC'].get('timeout', '30')
            }
        
        raise FileNotFoundError("No database configuration found")
    
    def build_connection_string(self) -> str:
        """Build SQL Server connection string"""
        try:
            config = self.load_config()
            
            # Handle different authentication methods
            if config.get('senha'):
                # SQL Server Authentication
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={config['servidor']};"
                    f"DATABASE={config['banco']};"
                    f"UID={config['usuario']};"
                    f"PWD={config['senha']};"
                    f"TIMEOUT={config.get('timeout', 30)};"
                )
            else:
                # Windows Authentication
                conn_str = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={config['servidor']};"
                    f"DATABASE={config['banco']};"
                    f"Trusted_Connection=yes;"
                    f"TIMEOUT={config.get('timeout', 30)};"
                )
            
            self.connection_string = conn_str
            return conn_str
            
        except Exception as e:
            logger.error(f"Error building connection string: {e}")
            raise
    
    def test_connection(self) -> tuple[bool, str]:
        """Test connection to SIC database"""
        try:
            conn_str = self.build_connection_string()
            conn = pyodbc.connect(conn_str, timeout=10)
            
            # Test with a simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.is_connected = True
            return True, "Connection successful"
            
        except pyodbc.Error as e:
            self.is_connected = False
            return False, f"Database error: {e}"
        except Exception as e:
            self.is_connected = False
            return False, f"Connection error: {e}"
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            if not self.connection_string:
                self.build_connection_string()
            
            conn = pyodbc.connect(self.connection_string)
            yield conn
            
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch all rows and convert to dict
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_command(self, command: str, params: tuple = None) -> int:
        """Execute INSERT/UPDATE/DELETE command"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(command, params)
                else:
                    cursor.execute(command)
                
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise
    
    def get_products(self) -> List[Dict[str, Any]]:
        """Get all products from SIC"""
        query = """
        SELECT 
            CODIGO,
            DESCRICAO,
            PRECO_VENDA,
            ESTOQUE_ATUAL,
            CATEGORIA,
            MARCA,
            UNIDADE,
            PESO,
            DATA_ATUALIZACAO
        FROM PRODUTOS 
        WHERE ATIVO = 1
        ORDER BY DESCRICAO
        """
        return self.execute_query(query)
    
    def get_product_by_code(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Get specific product by code"""
        query = """
        SELECT 
            CODIGO,
            DESCRICAO,
            PRECO_VENDA,
            ESTOQUE_ATUAL,
            CATEGORIA,
            MARCA,
            UNIDADE,
            PESO,
            DATA_ATUALIZACAO
        FROM PRODUTOS 
        WHERE CODIGO = ? AND ATIVO = 1
        """
        results = self.execute_query(query, (codigo,))
        return results[0] if results else None
    
    def update_product_price(self, codigo: str, novo_preco: float) -> bool:
        """Update product price in SIC"""
        try:
            command = "UPDATE PRODUTOS SET PRECO_VENDA = ? WHERE CODIGO = ?"
            rows_affected = self.execute_command(command, (novo_preco, codigo))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Error updating product price: {e}")
            return False