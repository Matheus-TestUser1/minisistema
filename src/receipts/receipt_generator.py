"""
Receipt Generator Module
Generates professional receipts/talões for customers and store
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import os

try:
    from .templates import ReceiptTemplateManager
except ImportError:
    # Fallback if relative import fails
    from src.receipts.templates import ReceiptTemplateManager
from ..database import Receipt, ReceiptItem, Product

logger = logging.getLogger(__name__)

class ReceiptGenerator:
    """Generates receipts/talões with professional formatting"""
    
    def __init__(self, template_manager: ReceiptTemplateManager = None, output_dir: str = 'output'):
        self.template_manager = template_manager or ReceiptTemplateManager()
        self.output_dir = output_dir
        self.frete_config = {
            'valor_por_kg': Decimal('3.50'),
            'frete_minimo': Decimal('15.00')
        }
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def create_receipt(self, cliente_nome: str, items: List[Dict[str, Any]], 
                      observacoes: str = '', tipo: str = 'cliente') -> Dict[str, Any]:
        """Create a new receipt with items"""
        try:
            # Convert items to ReceiptItem objects
            receipt_items = []
            subtotal = Decimal('0')
            
            for item_data in items:
                item = ReceiptItem(
                    produto_codigo=item_data['codigo'],
                    descricao=item_data['descricao'],
                    quantidade=item_data['quantidade'],
                    preco_unitario=Decimal(str(item_data['preco_unitario'])),
                    subtotal=Decimal(str(item_data['quantidade'])) * Decimal(str(item_data['preco_unitario'])),
                    peso=Decimal(str(item_data.get('peso', 0))) if item_data.get('peso') else None
                )
                receipt_items.append(item)
                subtotal += item.subtotal
            
            # Calculate freight
            frete = self._calculate_freight(receipt_items)
            total = subtotal + frete
            
            # Generate receipt number
            numero = self._generate_receipt_number()
            
            # Create receipt object
            receipt = Receipt(
                numero=numero,
                cliente_nome=cliente_nome,
                items=receipt_items,
                subtotal=subtotal,
                frete=frete,
                total=total,
                observacoes=observacoes
            )
            
            return {
                'success': True,
                'receipt': receipt,
                'numero': numero,
                'total': float(total)
            }
            
        except Exception as e:
            logger.error(f"Error creating receipt: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_receipt_html(self, receipt: Receipt, tipo: str = 'cliente') -> Dict[str, Any]:
        """Generate HTML receipt for viewing/printing"""
        try:
            template_name = f'talao_{tipo}.html'
            
            # Prepare data for template
            template_data = {
                'receipt': receipt,
                'empresa': {
                    'nome': 'MADEIREIRA MARIA LUIZA',
                    'endereco': 'Av. Dr. Cládio Gueiros Leite, 6311',
                    'cidade': 'Pau Amarelo - PE',
                    'telefone': '(81) 3011-5515',
                    'cnpj': '48.905.025/001-61'
                },
                'data_emissao': receipt.data_emissao.strftime('%d/%m/%Y %H:%M'),
                'tipo': tipo.upper(),
                'is_cliente': tipo == 'cliente',
                'is_loja': tipo == 'loja'
            }
            
            # Generate HTML content
            html_content = self.template_manager.render_template(template_name, template_data)
            
            # Save to file
            filename = f"talao_{tipo}_{receipt.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'html_content': html_content
            }
            
        except Exception as e:
            logger.error(f"Error generating HTML receipt: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_receipt_txt(self, receipt: Receipt, tipo: str = 'cliente') -> Dict[str, Any]:
        """Generate text receipt for simple printing"""
        try:
            lines = []
            width = 80
            
            # Header
            lines.append("=" * width)
            lines.append("🌲 MADEIREIRA MARIA LUIZA".center(width))
            lines.append("Av. Dr. Cládio Gueiros Leite, 6311".center(width))
            lines.append("Pau Amarelo - PE - Tel: (81) 3011-5515".center(width))
            lines.append("CNPJ: 48.905.025/001-61".center(width))
            lines.append("=" * width)
            lines.append("")
            
            # Receipt info
            lines.append(f"TALÃO {tipo.upper()} Nº: {receipt.numero}")
            lines.append(f"Data: {receipt.data_emissao.strftime('%d/%m/%Y %H:%M')}")
            lines.append(f"Cliente: {receipt.cliente_nome}")
            lines.append("")
            lines.append("-" * width)
            
            # Items header
            lines.append(f"{'CÓDIGO':<10} {'DESCRIÇÃO':<35} {'QTD':<5} {'PREÇO':<10} {'TOTAL':<10}")
            lines.append("-" * width)
            
            # Items
            for item in receipt.items:
                codigo = str(item.produto_codigo)[:10]
                descricao = str(item.descricao)[:35]
                qtd = str(item.quantidade)
                preco = f"R$ {item.preco_unitario:.2f}"
                total_item = f"R$ {item.subtotal:.2f}"
                
                lines.append(f"{codigo:<10} {descricao:<35} {qtd:<5} {preco:<10} {total_item:<10}")
            
            lines.append("-" * width)
            
            # Totals
            lines.append(f"{'SUBTOTAL:':<60} R$ {receipt.subtotal:.2f}")
            lines.append(f"{'FRETE:':<60} R$ {receipt.frete:.2f}")
            lines.append("=" * width)
            lines.append(f"{'TOTAL GERAL:':<60} R$ {receipt.total:.2f}")
            lines.append("=" * width)
            
            # Observations
            if receipt.observacoes:
                lines.append("")
                lines.append("OBSERVAÇÕES:")
                lines.append(receipt.observacoes)
            
            # Footer
            lines.append("")
            lines.append("Obrigado pela preferência!".center(width))
            lines.append("")
            
            if tipo == 'loja':
                lines.append("*** VIA DA LOJA ***".center(width))
            else:
                lines.append("*** VIA DO CLIENTE ***".center(width))
            
            content = "\n".join(lines)
            
            # Save to file
            filename = f"talao_{tipo}_{receipt.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath,
                'content': content
            }
            
        except Exception as e:
            logger.error(f"Error generating text receipt: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_receipt_csv(self, receipt: Receipt) -> Dict[str, Any]:
        """Generate CSV receipt for data import"""
        try:
            import csv
            
            filename = f"talao_{receipt.numero}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header info
                writer.writerow(['TALÃO', receipt.numero])
                writer.writerow(['CLIENTE', receipt.cliente_nome])
                writer.writerow(['DATA', receipt.data_emissao.strftime('%d/%m/%Y %H:%M')])
                writer.writerow([])
                
                # Items header
                writer.writerow(['CÓDIGO', 'DESCRIÇÃO', 'QUANTIDADE', 'PREÇO UNITÁRIO', 'SUBTOTAL'])
                
                # Items
                for item in receipt.items:
                    writer.writerow([
                        item.produto_codigo,
                        item.descricao,
                        item.quantidade,
                        float(item.preco_unitario),
                        float(item.subtotal)
                    ])
                
                # Totals
                writer.writerow([])
                writer.writerow(['SUBTOTAL', '', '', '', float(receipt.subtotal)])
                writer.writerow(['FRETE', '', '', '', float(receipt.frete)])
                writer.writerow(['TOTAL', '', '', '', float(receipt.total)])
                
                if receipt.observacoes:
                    writer.writerow([])
                    writer.writerow(['OBSERVAÇÕES', receipt.observacoes])
            
            return {
                'success': True,
                'filename': filename,
                'filepath': filepath
            }
            
        except Exception as e:
            logger.error(f"Error generating CSV receipt: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_freight(self, items: List[ReceiptItem]) -> Decimal:
        """Calculate freight based on weight and configuration"""
        try:
            total_weight = Decimal('0')
            
            for item in items:
                if item.peso:
                    total_weight += item.peso * item.quantidade
            
            if total_weight == 0:
                return Decimal('0')
            
            # Calculate freight
            calculated_freight = total_weight * self.frete_config['valor_por_kg']
            
            # Apply minimum freight
            return max(calculated_freight, self.frete_config['frete_minimo'])
            
        except Exception as e:
            logger.error(f"Error calculating freight: {e}")
            return Decimal('0')
    
    def _generate_receipt_number(self) -> str:
        """Generate unique receipt number"""
        timestamp = datetime.now()
        return f"T{timestamp.strftime('%Y%m%d%H%M%S')}"
    
    def update_freight_config(self, valor_por_kg: float = None, frete_minimo: float = None):
        """Update freight calculation configuration"""
        if valor_por_kg is not None:
            self.frete_config['valor_por_kg'] = Decimal(str(valor_por_kg))
        
        if frete_minimo is not None:
            self.frete_config['frete_minimo'] = Decimal(str(frete_minimo))
        
        logger.info(f"Freight config updated: {self.frete_config}")
    
    def get_freight_config(self) -> Dict[str, float]:
        """Get current freight configuration"""
        return {
            'valor_por_kg': float(self.frete_config['valor_por_kg']),
            'frete_minimo': float(self.frete_config['frete_minimo'])
        }
    
    def preview_receipt(self, receipt: Receipt, tipo: str = 'cliente') -> Dict[str, Any]:
        """Generate receipt preview without saving"""
        try:
            # Generate HTML for preview
            template_name = f'talao_{tipo}.html'
            
            template_data = {
                'receipt': receipt,
                'empresa': {
                    'nome': 'MADEIREIRA MARIA LUIZA',
                    'endereco': 'Av. Dr. Cládio Gueiros Leite, 6311',
                    'cidade': 'Pau Amarelo - PE',
                    'telefone': '(81) 3011-5515',
                    'cnpj': '48.905.025/001-61'
                },
                'data_emissao': receipt.data_emissao.strftime('%d/%m/%Y %H:%M'),
                'tipo': tipo.upper(),
                'is_cliente': tipo == 'cliente',
                'is_loja': tipo == 'loja'
            }
            
            html_content = self.template_manager.render_template(template_name, template_data)
            
            return {
                'success': True,
                'html_content': html_content,
                'preview': True
            }
            
        except Exception as e:
            logger.error(f"Error generating receipt preview: {e}")
            return {'success': False, 'error': str(e)}