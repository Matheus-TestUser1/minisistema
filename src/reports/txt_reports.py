"""
Text Reports Generator Module  
Generates formatted text reports for printing or simple viewing
"""
import logging
from typing import Dict, Any, List
from datetime import datetime
import os

from ..database import ReportConfig

logger = logging.getLogger(__name__)

class TxtReportGenerator:
    """Generates formatted text reports"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.line_width = 80
    
    def _center_text(self, text: str) -> str:
        """Center text within line width"""
        return text.center(self.line_width)
    
    def _create_header(self, title: str) -> str:
        """Create report header"""
        header = []
        header.append("=" * self.line_width)
        header.append(self._center_text("🌲 MADEIREIRA MARIA LUIZA"))
        header.append(self._center_text(title))
        header.append(self._center_text(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"))
        header.append("=" * self.line_width)
        header.append("")
        return "\n".join(header)
    
    def _create_section_header(self, title: str) -> str:
        """Create section header"""
        return f"\n{title}\n{'-' * len(title)}\n"
    
    def _format_table_row(self, columns: List[str], widths: List[int]) -> str:
        """Format a table row with specified column widths"""
        row = ""
        for i, (col, width) in enumerate(zip(columns, widths)):
            if i > 0:
                row += " | "
            row += str(col)[:width].ljust(width)
        return row
    
    def _create_table_separator(self, widths: List[int]) -> str:
        """Create table separator line"""
        separator = ""
        for i, width in enumerate(widths):
            if i > 0:
                separator += "-+-"
            separator += "-" * width
        return separator
    
    def generate_products_report(self, data: List[Dict[str, Any]], config: ReportConfig) -> Dict[str, Any]:
        """Generate products text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "RELATÓRIO DE PRODUTOS"))
            
            if not data:
                lines.append("Nenhum produto encontrado.")
                content = "\n".join(lines)
                filename = self._save_report(content, "produtos_vazio")
                return {'success': True, 'filename': filename, 'message': 'Relatório gerado (vazio)'}
            
            # Table headers and widths
            headers = ["CÓDIGO", "DESCRIÇÃO", "CATEGORIA", "PREÇO", "ESTOQUE"]
            widths = [10, 30, 15, 12, 8]
            
            lines.append(self._format_table_row(headers, widths))
            lines.append(self._create_table_separator(widths))
            
            # Data rows
            for product in data:
                row = [
                    product.get('Código', '')[:10],
                    product.get('Descrição', '')[:30],
                    product.get('Categoria', '')[:15],
                    product.get('Preço de Venda', '')[:12],
                    str(product.get('Estoque Atual', ''))[:8]
                ]
                lines.append(self._format_table_row(row, widths))
            
            lines.append("")
            lines.append(f"Total de produtos: {len(data)}")
            
            content = "\n".join(lines)
            filename = self._save_report(content, "produtos")
            
            return {'success': True, 'filename': filename, 'total_records': len(data)}
            
        except Exception as e:
            logger.error(f"Error generating text products report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_inventory_report(self, stock_data: Dict[str, Any], config: ReportConfig) -> Dict[str, Any]:
        """Generate inventory text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "RELATÓRIO DE ESTOQUE"))
            
            # Summary section
            lines.append(self._create_section_header("RESUMO GERAL"))
            lines.append(f"Total de Produtos: {stock_data.get('total_products', 0)}")
            lines.append(f"Valor Total em Estoque: R$ {stock_data.get('total_stock_value', 0):.2f}")
            lines.append(f"Produtos em Falta: {stock_data.get('out_of_stock_count', 0)}")
            lines.append(f"Produtos com Estoque Baixo: {stock_data.get('low_stock_count', 0)}")
            
            # Categories section
            if stock_data.get('categories'):
                lines.append(self._create_section_header("RESUMO POR CATEGORIA"))
                
                headers = ["CATEGORIA", "QTD", "VALOR TOTAL", "ESTOQUE"]
                widths = [20, 8, 15, 10]
                
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for categoria, data in stock_data['categories'].items():
                    row = [
                        categoria[:20],
                        str(data['count']),
                        f"R$ {data['total_value']:.2f}",
                        str(data['total_stock'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            # Top products by value
            if stock_data.get('products'):
                lines.append(self._create_section_header("PRODUTOS COM MAIOR VALOR EM ESTOQUE"))
                
                # Sort by stock value and take top 20
                products = sorted(stock_data['products'], 
                                key=lambda x: x['valor_estoque'], reverse=True)[:20]
                
                headers = ["CÓDIGO", "DESCRIÇÃO", "ESTOQUE", "VALOR"]
                widths = [10, 35, 8, 12]
                
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for product in products:
                    row = [
                        product['codigo'][:10],
                        product['descricao'][:35],
                        str(product['estoque_atual']),
                        f"R$ {product['valor_estoque']:.2f}"
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            content = "\n".join(lines)
            filename = self._save_report(content, "estoque")
            
            return {'success': True, 'filename': filename}
            
        except Exception as e:
            logger.error(f"Error generating text inventory report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_low_stock_report(self, alerts: List[Dict[str, Any]], config: ReportConfig) -> Dict[str, Any]:
        """Generate low stock text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "PRODUTOS EM FALTA"))
            
            if not alerts:
                lines.append("Nenhum produto com estoque baixo encontrado.")
                content = "\n".join(lines)
                filename = self._save_report(content, "estoque_baixo_vazio")
                return {'success': True, 'filename': filename, 'message': 'Nenhum produto em falta'}
            
            # Group by urgency
            critical = [a for a in alerts if a['urgency'] == 'CRITICAL']
            high = [a for a in alerts if a['urgency'] == 'HIGH']
            medium = [a for a in alerts if a['urgency'] == 'MEDIUM']
            
            headers = ["CÓDIGO", "DESCRIÇÃO", "CATEGORIA", "ESTOQUE"]
            widths = [10, 35, 15, 8]
            
            # Critical items
            if critical:
                lines.append(self._create_section_header("🔴 CRÍTICO - PRODUTOS EM FALTA"))
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for alert in critical:
                    row = [
                        alert['codigo'][:10],
                        alert['descricao'][:35],
                        (alert['categoria'] or 'Sem Categoria')[:15],
                        str(alert['estoque_atual'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            # High priority items
            if high:
                lines.append(self._create_section_header("🟡 ALTO - ESTOQUE MUITO BAIXO"))
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for alert in high:
                    row = [
                        alert['codigo'][:10],
                        alert['descricao'][:35],
                        (alert['categoria'] or 'Sem Categoria')[:15],
                        str(alert['estoque_atual'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            # Medium priority items
            if medium:
                lines.append(self._create_section_header("🟢 MÉDIO - ESTOQUE BAIXO"))
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for alert in medium:
                    row = [
                        alert['codigo'][:10],
                        alert['descricao'][:35],
                        (alert['categoria'] or 'Sem Categoria')[:15],
                        str(alert['estoque_atual'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            lines.append("")
            lines.append(f"Total de alertas: {len(alerts)}")
            lines.append(f"Críticos: {len(critical)} | Altos: {len(high)} | Médios: {len(medium)}")
            
            content = "\n".join(lines)
            filename = self._save_report(content, "estoque_baixo")
            
            return {'success': True, 'filename': filename, 'total_alerts': len(alerts)}
            
        except Exception as e:
            logger.error(f"Error generating text low stock report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_price_list(self, price_data: List[Dict[str, Any]], config: ReportConfig) -> Dict[str, Any]:
        """Generate price list text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "LISTA DE PREÇOS"))
            
            current_category = None
            
            for item in price_data:
                if item['Categoria'] != current_category:
                    current_category = item['Categoria']
                    lines.append(self._create_section_header(f"CATEGORIA: {current_category}"))
                
                # Format price line
                price_line = f"{item['Código'].ljust(12)} {item['Descrição'][:45].ljust(45)} {item['Preço de Venda'].rjust(12)}"
                lines.append(price_line)
            
            lines.append("")
            lines.append(f"Total de itens: {len(price_data)}")
            
            content = "\n".join(lines)
            filename = self._save_report(content, "lista_precos")
            
            return {'success': True, 'filename': filename, 'total_items': len(price_data)}
            
        except Exception as e:
            logger.error(f"Error generating text price list: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_category_report(self, categories: Dict[str, Dict], config: ReportConfig) -> Dict[str, Any]:
        """Generate category-based text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "RELATÓRIO POR CATEGORIA"))
            
            for categoria, data in categories.items():
                lines.append(self._create_section_header(f"CATEGORIA: {categoria}"))
                lines.append(f"Total de Produtos: {data['total_items']}")
                lines.append(f"Valor Total: R$ {data['valor_total']:.2f}")
                lines.append(f"Estoque Total: {data['estoque_total']} unidades")
                lines.append("")
                
                # Top products in category
                products = sorted(data['produtos'], 
                                key=lambda p: p.preco_venda * p.estoque_atual, reverse=True)[:10]
                
                if products:
                    lines.append("Principais produtos:")
                    headers = ["CÓDIGO", "DESCRIÇÃO", "PREÇO", "ESTOQUE"]
                    widths = [10, 30, 12, 8]
                    
                    lines.append(self._format_table_row(headers, widths))
                    lines.append(self._create_table_separator(widths))
                    
                    for product in products:
                        row = [
                            product.codigo[:10],
                            product.descricao[:30],
                            f"R$ {product.preco_venda:.2f}",
                            str(product.estoque_atual)
                        ]
                        lines.append(self._format_table_row(row, widths))
                
                lines.append("")
            
            content = "\n".join(lines)
            filename = self._save_report(content, "categorias")
            
            return {'success': True, 'filename': filename, 'categories_count': len(categories)}
            
        except Exception as e:
            logger.error(f"Error generating text category report: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_reorder_report(self, suggestions: List[Dict[str, Any]], config: ReportConfig) -> Dict[str, Any]:
        """Generate reorder suggestions text report"""
        try:
            lines = []
            lines.append(self._create_header(config.titulo or "SUGESTÕES DE REPOSIÇÃO"))
            
            if not suggestions:
                lines.append("Nenhuma sugestão de reposição no momento.")
                content = "\n".join(lines)
                filename = self._save_report(content, "reposicao_vazio")
                return {'success': True, 'filename': filename}
            
            # Group by priority
            high_priority = [s for s in suggestions if s['priority'] == 'HIGH']
            medium_priority = [s for s in suggestions if s['priority'] == 'MEDIUM']
            
            headers = ["CÓDIGO", "DESCRIÇÃO", "ATUAL", "SUGERIDO"]
            widths = [10, 30, 8, 10]
            
            # High priority
            if high_priority:
                lines.append(self._create_section_header("🔴 ALTA PRIORIDADE"))
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for suggestion in high_priority:
                    row = [
                        suggestion['codigo'][:10],
                        suggestion['descricao'][:30],
                        str(suggestion['estoque_atual']),
                        str(suggestion['quantidade_sugerida'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            # Medium priority
            if medium_priority:
                lines.append(self._create_section_header("🟡 MÉDIA PRIORIDADE"))
                lines.append(self._format_table_row(headers, widths))
                lines.append(self._create_table_separator(widths))
                
                for suggestion in medium_priority:
                    row = [
                        suggestion['codigo'][:10],
                        suggestion['descricao'][:30],
                        str(suggestion['estoque_atual']),
                        str(suggestion['quantidade_sugerida'])
                    ]
                    lines.append(self._format_table_row(row, widths))
            
            lines.append("")
            lines.append(f"Total de sugestões: {len(suggestions)}")
            lines.append(f"Alta prioridade: {len(high_priority)} | Média prioridade: {len(medium_priority)}")
            
            content = "\n".join(lines)
            filename = self._save_report(content, "reposicao")
            
            return {'success': True, 'filename': filename, 'suggestions_count': len(suggestions)}
            
        except Exception as e:
            logger.error(f"Error generating text reorder report: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_report(self, content: str, prefix: str) -> str:
        """Save report content to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Text report saved: {filepath}")
        return filename