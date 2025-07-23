"""
Local SQLite Database Module
Handles local caching and offline mode functionality
"""
import sqlite3
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class LocalDatabase:
    """Manages local SQLite database for caching and offline mode"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join('dados', 'produtos_sic.db')
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Products table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    codigo TEXT PRIMARY KEY,
                    descricao TEXT NOT NULL,
                    preco_venda REAL NOT NULL,
                    estoque_atual INTEGER DEFAULT 0,
                    categoria TEXT,
                    marca TEXT,
                    unidade TEXT,
                    peso REAL,
                    data_atualizacao TIMESTAMP,
                    sincronizado INTEGER DEFAULT 1,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Sync status table
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY,
                    ultima_sincronizacao TIMESTAMP,
                    total_produtos INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'offline'
                )
                ''')
                
                # Sales/movements table for offline tracking
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS movimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL, -- 'venda', 'entrada', 'saida'
                    produto_codigo TEXT NOT NULL,
                    quantidade INTEGER NOT NULL,
                    preco REAL,
                    data_movimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sincronizado INTEGER DEFAULT 0,
                    dados_extras TEXT, -- JSON for additional data
                    FOREIGN KEY (produto_codigo) REFERENCES produtos (codigo)
                )
                ''')
                
                # Initialize sync status if empty
                cursor.execute('SELECT COUNT(*) FROM sync_status')
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                    INSERT INTO sync_status (ultima_sincronizacao, status) 
                    VALUES (?, 'offline')
                    ''', (datetime.now(),))
                
                conn.commit()
                logger.info("Local database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products from local database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM produtos 
                ORDER BY descricao
                ''')
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return []
    
    def get_product_by_code(self, codigo: str) -> Optional[Dict[str, Any]]:
        """Get specific product by code"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM produtos WHERE codigo = ?', (codigo,))
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting product {codigo}: {e}")
            return None
    
    def insert_or_update_product(self, produto: Dict[str, Any]) -> bool:
        """Insert or update product in local database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if product exists
                cursor.execute('SELECT codigo FROM produtos WHERE codigo = ?', (produto['codigo'],))
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Update existing product
                    cursor.execute('''
                    UPDATE produtos SET
                        descricao = ?,
                        preco_venda = ?,
                        estoque_atual = ?,
                        categoria = ?,
                        marca = ?,
                        unidade = ?,
                        peso = ?,
                        data_atualizacao = ?,
                        sincronizado = 1,
                        atualizado_em = CURRENT_TIMESTAMP
                    WHERE codigo = ?
                    ''', (
                        produto.get('descricao', ''),
                        produto.get('preco_venda', 0),
                        produto.get('estoque_atual', 0),
                        produto.get('categoria', ''),
                        produto.get('marca', ''),
                        produto.get('unidade', ''),
                        produto.get('peso', 0),
                        produto.get('data_atualizacao'),
                        produto['codigo']
                    ))
                else:
                    # Insert new product
                    cursor.execute('''
                    INSERT INTO produtos (
                        codigo, descricao, preco_venda, estoque_atual,
                        categoria, marca, unidade, peso, data_atualizacao,
                        sincronizado
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (
                        produto['codigo'],
                        produto.get('descricao', ''),
                        produto.get('preco_venda', 0),
                        produto.get('estoque_atual', 0),
                        produto.get('categoria', ''),
                        produto.get('marca', ''),
                        produto.get('unidade', ''),
                        produto.get('peso', 0),
                        produto.get('data_atualizacao')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error inserting/updating product: {e}")
            return False
    
    def sync_products_from_sic(self, produtos_sic: List[Dict[str, Any]]) -> int:
        """Sync products from SIC to local database"""
        try:
            count = 0
            for produto in produtos_sic:
                if self.insert_or_update_product(produto):
                    count += 1
            
            # Update sync status
            self.update_sync_status(len(produtos_sic), 'online')
            
            logger.info(f"Synced {count} products from SIC")
            return count
            
        except Exception as e:
            logger.error(f"Error syncing products: {e}")
            return 0
    
    def update_sync_status(self, total_produtos: int, status: str):
        """Update synchronization status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                UPDATE sync_status SET
                    ultima_sincronizacao = ?,
                    total_produtos = ?,
                    status = ?
                WHERE id = 1
                ''', (datetime.now(), total_produtos, status))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM sync_status WHERE id = 1')
                row = cursor.fetchone()
                
                return dict(row) if row else {
                    'ultima_sincronizacao': None,
                    'total_produtos': 0,
                    'status': 'offline'
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {'status': 'error'}
    
    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """Search products by description or code"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                search_pattern = f"%{search_term}%"
                cursor.execute('''
                SELECT * FROM produtos 
                WHERE descricao LIKE ? OR codigo LIKE ?
                ORDER BY descricao
                LIMIT 100
                ''', (search_pattern, search_pattern))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def record_movement(self, tipo: str, produto_codigo: str, quantidade: int, 
                       preco: float = None, dados_extras: Dict = None) -> bool:
        """Record product movement for offline tracking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO movimentos (
                    tipo, produto_codigo, quantidade, preco, dados_extras
                ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    tipo,
                    produto_codigo,
                    quantidade,
                    preco,
                    json.dumps(dados_extras) if dados_extras else None
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error recording movement: {e}")
            return False
    
    def get_pending_movements(self) -> List[Dict[str, Any]]:
        """Get movements not yet synchronized"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM movimentos 
                WHERE sincronizado = 0
                ORDER BY data_movimento
                ''')
                
                movements = []
                for row in cursor.fetchall():
                    movement = dict(row)
                    if movement['dados_extras']:
                        movement['dados_extras'] = json.loads(movement['dados_extras'])
                    movements.append(movement)
                
                return movements
                
        except Exception as e:
            logger.error(f"Error getting pending movements: {e}")
            return []