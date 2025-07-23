"""
Inventory Management Module
Handles stock control and inventory operations
"""
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from .product_manager import ProductManager
from ..database import Product, Movement

logger = logging.getLogger(__name__)

class InventoryManager:
    """Manages inventory operations and stock control"""
    
    def __init__(self, product_manager: ProductManager):
        self.product_manager = product_manager
    
    def get_stock_report(self) -> Dict[str, Any]:
        """Generate comprehensive stock report"""
        try:
            products = self.product_manager.get_all_products(force_local=True)
            
            report = {
                'timestamp': datetime.now().isoformat(),
                'total_products': len(products),
                'total_stock_value': Decimal('0'),
                'low_stock_count': 0,
                'out_of_stock_count': 0,
                'categories': {},
                'products': []
            }
            
            for product in products:
                stock_value = product.preco_venda * product.estoque_atual
                report['total_stock_value'] += stock_value
                
                if product.estoque_atual == 0:
                    report['out_of_stock_count'] += 1
                elif product.estoque_atual <= 5:  # Low stock threshold
                    report['low_stock_count'] += 1
                
                # Category breakdown
                category = product.categoria or 'Sem Categoria'
                if category not in report['categories']:
                    report['categories'][category] = {
                        'count': 0,
                        'total_value': Decimal('0'),
                        'total_stock': 0
                    }
                
                report['categories'][category]['count'] += 1
                report['categories'][category]['total_value'] += stock_value
                report['categories'][category]['total_stock'] += product.estoque_atual
                
                # Product details
                report['products'].append({
                    'codigo': product.codigo,
                    'descricao': product.descricao,
                    'estoque_atual': product.estoque_atual,
                    'preco_venda': float(product.preco_venda),
                    'valor_estoque': float(stock_value),
                    'categoria': product.categoria,
                    'status': self._get_stock_status(product.estoque_atual)
                })
            
            # Convert decimal values to float for JSON serialization
            report['total_stock_value'] = float(report['total_stock_value'])
            for category_data in report['categories'].values():
                category_data['total_value'] = float(category_data['total_value'])
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating stock report: {e}")
            return {'error': str(e)}
    
    def _get_stock_status(self, stock: int) -> str:
        """Get stock status description"""
        if stock == 0:
            return 'OUT_OF_STOCK'
        elif stock <= 5:
            return 'LOW_STOCK'
        elif stock <= 20:
            return 'NORMAL'
        else:
            return 'HIGH_STOCK'
    
    def get_low_stock_alert(self, threshold: int = 5) -> List[Dict[str, Any]]:
        """Get products that need restocking"""
        try:
            low_stock_products = self.product_manager.get_low_stock_products(threshold)
            
            alerts = []
            for product in low_stock_products:
                alerts.append({
                    'codigo': product.codigo,
                    'descricao': product.descricao,
                    'estoque_atual': product.estoque_atual,
                    'categoria': product.categoria,
                    'urgency': 'CRITICAL' if product.estoque_atual == 0 else 'HIGH' if product.estoque_atual <= 2 else 'MEDIUM'
                })
            
            return sorted(alerts, key=lambda x: x['estoque_atual'])
            
        except Exception as e:
            logger.error(f"Error getting low stock alerts: {e}")
            return []
    
    def record_stock_entry(self, codigo: str, quantidade: int, 
                          custo: Optional[Decimal] = None, observacao: str = '') -> bool:
        """Record stock entry (purchase/restock)"""
        try:
            # Record movement
            success = self.product_manager.local_db.record_movement(
                tipo='entrada',
                produto_codigo=codigo,
                quantidade=quantidade,
                preco=float(custo) if custo else None,
                dados_extras={'observacao': observacao}
            )
            
            if success:
                # Update local stock
                product_data = self.product_manager.local_db.get_product_by_code(codigo)
                if product_data:
                    product_data['estoque_atual'] += quantidade
                    product_data['sincronizado'] = 0  # Mark as needing sync
                    product_data['atualizado_em'] = datetime.now().isoformat()
                    self.product_manager.local_db.insert_or_update_product(product_data)
                    
                    logger.info(f"Stock entry recorded: {codigo} +{quantidade}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error recording stock entry: {e}")
            return False
    
    def record_stock_adjustment(self, codigo: str, nova_quantidade: int, 
                              motivo: str = 'Ajuste de estoque') -> bool:
        """Record stock adjustment (set exact quantity)"""
        try:
            product_data = self.product_manager.local_db.get_product_by_code(codigo)
            if not product_data:
                logger.error(f"Product {codigo} not found for stock adjustment")
                return False
            
            quantidade_atual = product_data['estoque_atual']
            diferenca = nova_quantidade - quantidade_atual
            
            if diferenca == 0:
                return True  # No change needed
            
            # Record movement
            tipo_movimento = 'entrada' if diferenca > 0 else 'saida'
            success = self.product_manager.local_db.record_movement(
                tipo=tipo_movimento,
                produto_codigo=codigo,
                quantidade=abs(diferenca),
                dados_extras={'motivo': motivo, 'ajuste': True}
            )
            
            if success:
                # Update stock
                product_data['estoque_atual'] = nova_quantidade
                product_data['sincronizado'] = 0
                product_data['atualizado_em'] = datetime.now().isoformat()
                self.product_manager.local_db.insert_or_update_product(product_data)
                
                logger.info(f"Stock adjusted: {codigo} {quantidade_atual} -> {nova_quantidade}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adjusting stock: {e}")
            return False
    
    def get_movement_history(self, codigo: str = None, days: int = 30) -> List[Dict[str, Any]]:
        """Get movement history for a product or all products"""
        try:
            # This would require extending the local database to support querying movements
            # For now, return pending movements
            movements = self.product_manager.local_db.get_pending_movements()
            
            # Filter by product if specified
            if codigo:
                movements = [m for m in movements if m.get('produto_codigo') == codigo]
            
            # Filter by date range
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_movements = []
            
            for movement in movements:
                try:
                    movement_date = datetime.fromisoformat(movement['data_movimento'])
                    if movement_date >= cutoff_date:
                        filtered_movements.append(movement)
                except:
                    continue
            
            return sorted(filtered_movements, key=lambda x: x['data_movimento'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting movement history: {e}")
            return []
    
    def calculate_reorder_suggestions(self) -> List[Dict[str, Any]]:
        """Calculate reorder suggestions based on stock levels and movement history"""
        try:
            products = self.product_manager.get_all_products(force_local=True)
            suggestions = []
            
            for product in products:
                if product.estoque_atual <= 10:  # Reorder threshold
                    # Simple reorder calculation
                    # In a real system, this would consider sales velocity, lead times, etc.
                    suggested_quantity = max(20, product.estoque_atual * 3)
                    
                    suggestions.append({
                        'codigo': product.codigo,
                        'descricao': product.descricao,
                        'estoque_atual': product.estoque_atual,
                        'quantidade_sugerida': suggested_quantity,
                        'categoria': product.categoria,
                        'priority': 'HIGH' if product.estoque_atual <= 5 else 'MEDIUM'
                    })
            
            return sorted(suggestions, key=lambda x: x['estoque_atual'])
            
        except Exception as e:
            logger.error(f"Error calculating reorder suggestions: {e}")
            return []
    
    def export_inventory_csv(self, filepath: str) -> bool:
        """Export inventory to CSV file"""
        try:
            import csv
            
            products = self.product_manager.get_all_products(force_local=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['codigo', 'descricao', 'categoria', 'estoque_atual', 
                             'preco_venda', 'valor_estoque', 'status']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for product in products:
                    stock_value = float(product.preco_venda * product.estoque_atual)
                    writer.writerow({
                        'codigo': product.codigo,
                        'descricao': product.descricao,
                        'categoria': product.categoria or '',
                        'estoque_atual': product.estoque_atual,
                        'preco_venda': float(product.preco_venda),
                        'valor_estoque': stock_value,
                        'status': self._get_stock_status(product.estoque_atual)
                    })
            
            logger.info(f"Inventory exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting inventory: {e}")
            return False