"""
Report Generator Module
Main interface for generating various types of reports
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os

from .excel_reports import ExcelReportGenerator
from .txt_reports import TxtReportGenerator
from ..products import ProductManager, InventoryManager
from ..database import ReportConfig

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Main report generator that coordinates different report types"""
    
    def __init__(self, product_manager: ProductManager, output_dir: str = 'output'):
        self.product_manager = product_manager
        self.inventory_manager = InventoryManager(product_manager)
        self.output_dir = output_dir
        self.excel_generator = ExcelReportGenerator(output_dir)
        self.txt_generator = TxtReportGenerator(output_dir)
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_products_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate products report in specified format"""
        try:
            # Get products data
            products = self.product_manager.get_all_products(force_local=True)
            
            # Prepare data for report
            report_data = []
            for product in products:
                product_data = {
                    'Código': product.codigo,
                    'Descrição': product.descricao,
                    'Categoria': product.categoria or 'Sem Categoria',
                    'Marca': product.marca or 'Sem Marca',
                    'Preço de Venda': f'R$ {product.preco_venda:.2f}',
                    'Estoque Atual': product.estoque_atual,
                    'Unidade': product.unidade or 'UN',
                    'Peso (kg)': f'{product.peso:.3f}' if product.peso else 'N/A',
                    'Valor em Estoque': f'R$ {(product.preco_venda * product.estoque_atual):.2f}'
                }
                
                # Apply filters if specified
                if self._apply_filters(product_data, config.filtros):
                    report_data.append(product_data)
            
            # Generate report based on type
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_products_report(report_data, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_products_report(report_data, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating products report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_inventory_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate inventory/stock report"""
        try:
            stock_report = self.inventory_manager.get_stock_report()
            
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_inventory_report(stock_report, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_inventory_report(stock_report, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating inventory report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_low_stock_report(self, config: ReportConfig, threshold: int = 5) -> Dict[str, Any]:
        """Generate low stock alert report"""
        try:
            low_stock_alerts = self.inventory_manager.get_low_stock_alert(threshold)
            
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_low_stock_report(low_stock_alerts, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_low_stock_report(low_stock_alerts, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating low stock report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_price_list(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate price list report"""
        try:
            products = self.product_manager.get_all_products(force_local=True)
            
            # Sort by category then by description
            products.sort(key=lambda p: (p.categoria or 'ZZZ', p.descricao))
            
            price_data = []
            for product in products:
                price_data.append({
                    'Código': product.codigo,
                    'Descrição': product.descricao,
                    'Categoria': product.categoria or 'Sem Categoria',
                    'Preço de Venda': f'R$ {product.preco_venda:.2f}',
                    'Unidade': product.unidade or 'UN'
                })
            
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_price_list(price_data, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_price_list(price_data, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating price list: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_category_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate report grouped by categories"""
        try:
            products = self.product_manager.get_all_products(force_local=True)
            
            # Group by category
            categories = {}
            for product in products:
                category = product.categoria or 'Sem Categoria'
                if category not in categories:
                    categories[category] = {
                        'produtos': [],
                        'total_items': 0,
                        'valor_total': 0,
                        'estoque_total': 0
                    }
                
                categories[category]['produtos'].append(product)
                categories[category]['total_items'] += 1
                categories[category]['valor_total'] += float(product.preco_venda * product.estoque_atual)
                categories[category]['estoque_total'] += product.estoque_atual
            
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_category_report(categories, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_category_report(categories, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating category report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_reorder_report(self, config: ReportConfig) -> Dict[str, Any]:
        """Generate reorder suggestions report"""
        try:
            reorder_suggestions = self.inventory_manager.calculate_reorder_suggestions()
            
            if config.tipo.lower() == 'excel':
                return self.excel_generator.generate_reorder_report(reorder_suggestions, config)
            elif config.tipo.lower() == 'txt':
                return self.txt_generator.generate_reorder_report(reorder_suggestions, config)
            else:
                raise ValueError(f"Unsupported report type: {config.tipo}")
                
        except Exception as e:
            logger.error(f"Error generating reorder report: {e}")
            return {'success': False, 'error': str(e)}
    
    def _apply_filters(self, product_data: Dict[str, Any], filtros: Optional[Dict[str, Any]]) -> bool:
        """Apply filters to product data"""
        if not filtros:
            return True
        
        try:
            # Category filter
            if 'categoria' in filtros and filtros['categoria']:
                if product_data['Categoria'] != filtros['categoria']:
                    return False
            
            # Price range filter
            if 'preco_min' in filtros and filtros['preco_min']:
                price_str = product_data['Preço de Venda'].replace('R$ ', '').replace(',', '.')
                price = float(price_str)
                if price < filtros['preco_min']:
                    return False
            
            if 'preco_max' in filtros and filtros['preco_max']:
                price_str = product_data['Preço de Venda'].replace('R$ ', '').replace(',', '.')
                price = float(price_str)
                if price > filtros['preco_max']:
                    return False
            
            # Stock filter
            if 'estoque_min' in filtros and filtros['estoque_min'] is not None:
                if product_data['Estoque Atual'] < filtros['estoque_min']:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return True
    
    def get_available_reports(self) -> List[Dict[str, Any]]:
        """Get list of available report types"""
        return [
            {
                'id': 'products',
                'name': 'Relatório de Produtos',
                'description': 'Lista completa de produtos com preços e estoque',
                'formats': ['excel', 'txt']
            },
            {
                'id': 'inventory',
                'name': 'Relatório de Estoque',
                'description': 'Análise detalhada do estoque atual',
                'formats': ['excel', 'txt']
            },
            {
                'id': 'low_stock',
                'name': 'Produtos em Falta',
                'description': 'Produtos com estoque baixo ou zerado',
                'formats': ['excel', 'txt']
            },
            {
                'id': 'price_list',
                'name': 'Lista de Preços',
                'description': 'Lista de preços para clientes',
                'formats': ['excel', 'txt']
            },
            {
                'id': 'categories',
                'name': 'Relatório por Categoria',
                'description': 'Produtos agrupados por categoria',
                'formats': ['excel', 'txt']
            },
            {
                'id': 'reorder',
                'name': 'Sugestões de Reposição',
                'description': 'Sugestões de compra para reposição de estoque',
                'formats': ['excel', 'txt']
            }
        ]