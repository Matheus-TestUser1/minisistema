"""
Secure Configuration Manager Module
Handles secure storage and loading of configuration with proper authentication
"""
import os
import json
import configparser
import hashlib
import base64
from typing import Dict, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import simpledialog, messagebox
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


class SecureConfigManager:
    """Manages secure configuration storage and retrieval"""
    
    def __init__(self, config_dir: str = "dados"):
        self.config_dir = config_dir
        self.legacy_ini_file = os.path.join(config_dir, "config.ini")
        self.legacy_json_file = os.path.join(config_dir, "config.json")
        self.session_config = {}
        
    def request_password(self, title: str = "Autenticação Necessária") -> Optional[str]:
        """Request password from user with proper dialog"""
        if not HAS_GUI:
            return None
            
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        password = simpledialog.askstring(
            title,
            "Digite a senha do banco SIC:",
            show='*'
        )
        
        root.destroy()
        return password
    
    def validate_credentials(self, servidor: str, banco: str, usuario: str, senha: str) -> Tuple[bool, str]:
        """Validate SIC database credentials"""
        try:
            import pyodbc
            
            # Build connection string
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={servidor};"
                f"DATABASE={banco};"
                f"UID={usuario};"
                f"PWD={senha};"
                f"TIMEOUT=10;"
            )
            
            # Test connection
            conn = pyodbc.connect(conn_str)
            
            # Test with simple query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            return True, "Credenciais válidas"
            
        except pyodbc.Error as e:
            error_msg = str(e).lower()
            if "login failed" in error_msg:
                return False, "Usuário ou senha incorretos"
            elif "server not found" in error_msg:
                return False, "Servidor não encontrado"
            elif "database" in error_msg:
                return False, "Banco de dados não encontrado"
            else:
                return False, f"Erro de conexão: {e}"
        except Exception as e:
            return False, f"Erro geral: {e}"
    
    def load_legacy_config(self) -> Dict:
        """Load configuration from legacy files"""
        config = {}
        
        # Try INI file first
        if os.path.exists(self.legacy_ini_file):
            parser = configparser.ConfigParser()
            parser.read(self.legacy_ini_file, encoding='utf-8')
            
            if 'SIC' in parser:
                config = {
                    'servidor': parser['SIC'].get('servidor', ''),
                    'banco': parser['SIC'].get('banco', ''),
                    'usuario': parser['SIC'].get('usuario', ''),
                    'porta': parser['SIC'].get('porta', '1433'),
                    'timeout': parser['SIC'].get('timeout', '30')
                }
        
        # Try JSON file as fallback
        elif os.path.exists(self.legacy_json_file):
            with open(self.legacy_json_file, 'r', encoding='utf-8') as f:
                legacy_config = json.load(f)
                config = {
                    'servidor': legacy_config.get('servidor', ''),
                    'banco': legacy_config.get('database', ''),
                    'usuario': legacy_config.get('usuario', ''),
                    'porta': '1433',
                    'timeout': '30'
                }
        
        return config
    
    def get_sic_credentials(self, force_prompt: bool = False) -> Optional[Dict]:
        """Get SIC credentials with mandatory password prompt"""
        # Check if we have session credentials
        if not force_prompt and self.session_config.get('sic'):
            return self.session_config['sic']
        
        # Load basic config (without password)
        config = self.load_legacy_config()
        
        if not config.get('servidor') or not config.get('banco') or not config.get('usuario'):
            if HAS_GUI:
                messagebox.showerror(
                    "Configuração Incompleta",
                    "Configuração do SIC incompleta. Verifique os arquivos de configuração."
                )
            return None
        
        # Always request password
        senha = self.request_password("Autenticação SIC")
        if not senha:
            return None
        
        # Validate credentials
        is_valid, message = self.validate_credentials(
            config['servidor'], 
            config['banco'], 
            config['usuario'], 
            senha
        )
        
        if not is_valid:
            if HAS_GUI:
                messagebox.showerror("Erro de Autenticação", message)
            return None
        
        # Store in session (memory only)
        sic_config = {
            **config,
            'senha': senha
        }
        
        self.session_config['sic'] = sic_config
        return sic_config
    
    def clear_session(self):
        """Clear session credentials"""
        self.session_config.clear()
    
    def cleanup_legacy_credentials(self):
        """Remove hardcoded credentials from legacy files (optional)"""
        try:
            # Clean INI file
            if os.path.exists(self.legacy_ini_file):
                parser = configparser.ConfigParser()
                parser.read(self.legacy_ini_file, encoding='utf-8')
                
                if 'SIC' in parser and 'senha' in parser['SIC']:
                    parser['SIC']['senha'] = ''  # Clear password
                    with open(self.legacy_ini_file, 'w', encoding='utf-8') as f:
                        parser.write(f)
            
            # Clean JSON file
            if os.path.exists(self.legacy_json_file):
                with open(self.legacy_json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if 'senha' in data:
                    data['senha'] = ''  # Clear password
                    with open(self.legacy_json_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error cleaning legacy credentials: {e}")
            return False
    
    def has_valid_session(self) -> bool:
        """Check if we have a valid session"""
        return bool(self.session_config.get('sic'))
    
    def get_session_timeout(self) -> int:
        """Get session timeout in minutes (default: 30)"""
        return 30