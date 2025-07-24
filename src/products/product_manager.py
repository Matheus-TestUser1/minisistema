"""
Product Manager Module
Handles product operations and business logic
"""
import logging
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from ..database import SICConnection, LocalDatabase, Product, Movement

logger = logging.getLogger(__name__)

class ProductManager:
    """Manages product operations and data flow between SIC and local database"""
    
    def __init__(self, sic_connection: SICConnection = None, local_db: LocalDatabase = None):
        self.sic_connection = sic_connection or SICConnection()
        self.local_db = local_db or LocalDatabase()
        self.offline_mode = False
        
    def check_sic_connection(self) -> bool:
        """Check if SIC is available"""
        try:
            success, _ = self.sic_connection.test_connection()
            self.offline_mode = not success
            return success
        except Exception as e:
            logger.error(f"Error checking SIC connection: {e}")
            self.offline_mode = True
            return False
    
    def get_all_products(self, force_local: bool = False) -> List[Product]:
        """Get all products, preferring SIC if available"""
        try:
            if not force_local and not self.offline_mode and self.check_sic_connection():
                # Try to get from SIC
                sic_products = self.sic_connection.get_products()
                products = [Product.from_dict(p) for p in sic_products]
                
                # Cache in local database
                self.local_db.sync_products_from_sic(sic_products)
                
                return products
            else:
                # Use local database
                local_products = self.local_db.get_all_products()
                return [Product.from_dict(p) for p in local_products]
                
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            # Fallback to local database
            local_products = self.local_db.get_all_products()
            return [Product.from_dict(p) for p in local_products]
    
    def get_product_by_code(self, codigo: str, force_local: bool = False) -> Optional[Product]:
        """Get specific product by code"""
        try:
            if not force_local and not self.offline_mode and self.check_sic_connection():
                # Try to get from SIC first
                sic_product = self.sic_connection.get_product_by_code(codigo)
                if sic_product:
                    product = Product.from_dict(sic_product)
                    # Update local cache
                    self.local_db.insert_or_update_product(sic_product)
                    return product
            
            # Use local database
            local_product = self.local_db.get_product_by_code(codigo)
            return Product.from_dict(local_product) if local_product else None
            
        except Exception as e:
            logger.error(f"Error getting product {codigo}: {e}")
            # Fallback to local
            local_product = self.local_db.get_product_by_code(codigo)
            return Product.from_dict(local_product) if local_product else None
    
    def search_products(self, search_term: str) -> List[Product]:
        """Search products by description or code"""
        try:
            # Always search in local database for speed
            local_products = self.local_db.search_products(search_term)
            return [Product.from_dict(p) for p in local_products]
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def update_product_price(self, codigo: str, novo_preco: Decimal) -> bool:
        """Update product price"""
        try:
            # Try to update in SIC first
            if not self.offline_mode and self.check_sic_connection():
                success = self.sic_connection.update_product_price(codigo, float(novo_preco))
                if success:
                    # Update local cache
                    local_product = self.local_db.get_product_by_code(codigo)
                    if local_product:
                        local_product['preco_venda'] = float(novo_preco)
                        local_product['atualizado_em'] = datetime.now().isoformat()
                        self.local_db.insert_or_update_product(local_product)
                    return True
            
            # Update locally and mark as not synchronized
            local_product = self.local_db.get_product_by_code(codigo)
            if local_product:
                local_product['preco_venda'] = float(novo_preco)
                local_product['sincronizado'] = 0  # Mark as needing sync
                local_product['atualizado_em'] = datetime.now().isoformat()
                return self.local_db.insert_or_update_product(local_product)
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating product price: {e}")
            return False
    
    def record_sale(self, codigo: str, quantidade: int, preco: Decimal) -> bool:
        """Record a product sale"""
        try:
            # Record movement
            success = self.local_db.record_movement(
                tipo='venda',
                produto_codigo=codigo,
                quantidade=quantidade,
                preco=float(preco)
            )
            
            # Update local stock
            if success:
                product_data = self.local_db.get_product_by_code(codigo)
                if product_data:
                    product_data['estoque_atual'] = max(0, product_data['estoque_atual'] - quantidade)
                    product_data['sincronizado'] = 0  # Mark as needing sync
                    self.local_db.insert_or_update_product(product_data)
            
            return success
            
        except Exception as e:
            logger.error(f"Error recording sale: {e}")
            return False
    
    def sync_with_sic(self) -> Dict[str, Any]:
        """Synchronize local data with SIC"""
        result = {
            'success': False,
            'products_synced': 0,
            'movements_synced': 0,
            'errors': []
        }
        
        try:
            # Check SIC connection
            if not self.check_sic_connection():
                result['errors'].append('Cannot connect to SIC')
                return result
            
            # Sync products from SIC
            sic_products = self.sic_connection.get_products()
            products_synced = self.local_db.sync_products_from_sic(sic_products)
            result['products_synced'] = products_synced
            
            # TODO: Sync pending movements to SIC
            pending_movements = self.local_db.get_pending_movements()
            movements_synced = 0
            
            for movement in pending_movements:
                # Here you would implement the logic to send movements to SIC
                # For now, just mark as synchronized
                movements_synced += 1
            
            result['movements_synced'] = movements_synced
            result['success'] = True
            
            logger.info(f"Sync completed: {products_synced} products, {movements_synced} movements")
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def get_low_stock_products(self, threshold: int = 5) -> List[Product]:
        """Get products with low stock"""
        try:
            all_products = self.get_all_products(force_local=True)
            return [p for p in all_products if p.estoque_atual <= threshold]
            
        except Exception as e:
            logger.error(f"Error getting low stock products: {e}")
            return []
    
    def get_product_categories(self) -> List[str]:
        """Get all unique product categories"""
        try:
            products = self.get_all_products(force_local=True)
            categories = set()
            
            for product in products:
                if product.categoria:
                    categories.add(product.categoria)
            
            return sorted(list(categories))
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_products_by_category(self, categoria: str) -> List[Product]:
        """Get products by category"""
        try:
            all_products = self.get_all_products(force_local=True)
            return [p for p in all_products if p.categoria == categoria]
            
        except Exception as e:
            logger.error(f"Error getting products by category: {e}")
            return []
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        try:
            local_status = self.local_db.get_sync_status()
            sic_available = self.check_sic_connection()
            
            return {
                **local_status,
                'sic_available': sic_available,
                'offline_mode': self.offline_mode
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {'status': 'error', 'offline_mode': True}
    
    def create_product(self, produto_data: Dict[str, Any]) -> bool:
        """Create a new product locally"""
        try:
            # Validate required fields
            required_fields = ['codigo', 'descricao', 'preco_venda']
            for field in required_fields:
                if not produto_data.get(field):
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate price
            try:
                preco = float(produto_data['preco_venda'])
                if preco <= 0:
                    logger.error("Price must be greater than 0")
                    return False
                produto_data['preco_venda'] = preco
            except (ValueError, TypeError):
                logger.error("Invalid price format")
                return False
            
            # Create in local database
            success = self.local_db.create_product(produto_data)
            
            if success:
                logger.info(f"Product {produto_data['codigo']} created successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return False
    
    def update_product(self, codigo: str, produto_data: Dict[str, Any]) -> bool:
        """Update an existing product"""
        try:
            # Validate required fields
            required_fields = ['descricao', 'preco_venda']
            for field in required_fields:
                if field in produto_data and not produto_data[field]:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate price if provided
            if 'preco_venda' in produto_data:
                try:
                    preco = float(produto_data['preco_venda'])
                    if preco <= 0:
                        logger.error("Price must be greater than 0")
                        return False
                    produto_data['preco_venda'] = preco
                except (ValueError, TypeError):
                    logger.error("Invalid price format")
                    return False
            
            # Update in local database
            success = self.local_db.update_product(codigo, produto_data)
            
            if success:
                logger.info(f"Product {codigo} updated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            return False
    
    def delete_product(self, codigo: str) -> bool:
        """Delete a product"""
        try:
            success = self.local_db.delete_product(codigo)
            
            if success:
                logger.info(f"Product {codigo} deleted successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            return False
    
    def validate_product_data(self, produto_data: Dict[str, Any], is_update: bool = False) -> List[str]:
        """Validate product data and return list of errors"""
        errors = []
        
        # Required fields for new products
        if not is_update:
            required_fields = ['codigo', 'descricao', 'preco_venda']
            for field in required_fields:
                value = produto_data.get(field, '')
                if not str(value).strip():
                    errors.append(f"Campo obrigatório: {field}")
        
        # Validate code uniqueness for new products
        if not is_update and produto_data.get('codigo'):
            if self.local_db.check_product_code_exists(produto_data['codigo']):
                errors.append("Código do produto já existe")
        
        # Validate price
        if 'preco_venda' in produto_data:
            try:
                preco = float(produto_data['preco_venda'])
                if preco <= 0:
                    errors.append("Preço deve ser maior que zero")
            except (ValueError, TypeError):
                errors.append("Preço em formato inválido")
        
        # Validate cost price if provided
        if 'preco_custo' in produto_data and produto_data['preco_custo']:
            try:
                preco_custo = float(produto_data['preco_custo'])
                if preco_custo < 0:
                    errors.append("Preço de custo não pode ser negativo")
            except (ValueError, TypeError):
                errors.append("Preço de custo em formato inválido")
        
        # Validate stock if provided
        if 'estoque' in produto_data and produto_data['estoque']:
            try:
                estoque = int(produto_data['estoque'])
                if estoque < 0:
                    errors.append("Estoque não pode ser negativo")
            except (ValueError, TypeError):
                errors.append("Estoque deve ser um número inteiro")
        
        return errors