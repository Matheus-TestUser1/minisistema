"""
Receipt Template Manager
Handles HTML/CSS templates for receipt generation
"""
import logging
import os
from typing import Dict, Any, Optional, List
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

class ReceiptTemplateManager:
    """Manages receipt templates using Jinja2"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join('src', 'receipts', 'templates')
        self.default_templates_dir = os.path.join('src', 'templates', 'default_templates')
        
        # Ensure template directories exist
        for dir_path in [self.templates_dir, self.default_templates_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([self.templates_dir, self.default_templates_dir]),
            autoescape=True
        )
        
        # Create default templates if they don't exist
        self.create_default_templates()
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render template with provided data"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
            
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            return self._get_fallback_template(template_name, data)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return self._get_fallback_template(template_name, data)
    
    def _get_fallback_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Generate fallback template when main template fails"""
        receipt = data.get('receipt')
        empresa = data.get('empresa', {})
        
        if not receipt:
            return "<html><body><h1>Error: No receipt data</h1></body></html>"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Talão - {receipt.numero}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; }}
                .receipt-info {{ margin: 20px 0; }}
                .items-table {{ width: 100%; border-collapse: collapse; }}
                .items-table th, .items-table td {{ border: 1px solid #000; padding: 5px; text-align: left; }}
                .totals {{ text-align: right; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{empresa.get('nome', 'MADEIREIRA MARIA LUIZA')}</h2>
                <p>{empresa.get('endereco', '')}</p>
                <p>{empresa.get('cidade', '')} - Tel: {empresa.get('telefone', '')}</p>
            </div>
            
            <div class="receipt-info">
                <p><strong>Talão Nº:</strong> {receipt.numero}</p>
                <p><strong>Cliente:</strong> {receipt.cliente_nome}</p>
                <p><strong>Data:</strong> {data.get('data_emissao', '')}</p>
            </div>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Descrição</th>
                        <th>Qtd</th>
                        <th>Preço</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in receipt.items:
            html += f"""
                    <tr>
                        <td>{item.produto_codigo}</td>
                        <td>{item.descricao}</td>
                        <td>{item.quantidade}</td>
                        <td>R$ {item.preco_unitario:.2f}</td>
                        <td>R$ {item.subtotal:.2f}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <div class="totals">
                <p><strong>Subtotal: R$ {receipt.subtotal:.2f}</strong></p>
                <p><strong>Frete: R$ {receipt.frete:.2f}</strong></p>
                <p><strong>Total: R$ {receipt.total:.2f}</strong></p>
            </div>
            
            <div class="footer">
                <p>Obrigado pela preferência!</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_default_templates(self):
        """Create default templates if they don't exist"""
        templates = {
            'talao_cliente.html': self._get_default_client_template(),
            'talao_loja.html': self._get_default_store_template(),
            'base.html': self._get_base_template()
        }
        
        for template_name, content in templates.items():
            template_path = os.path.join(self.templates_dir, template_name)
            if not os.path.exists(template_path):
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created default template: {template_name}")
    
    def _get_base_template(self) -> str:
        """Base template with common styling"""
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Talão{% endblock %}</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background: #fff;
            color: #333;
            line-height: 1.4;
        }
        
        .receipt-container {
            max-width: 800px;
            margin: 0 auto;
            background: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        .header {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0;
            color: #2c3e50;
            font-size: 28px;
            font-weight: bold;
        }
        
        .header .company-info {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        
        .receipt-info {
            margin-bottom: 30px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 4px solid #2c3e50;
        }
        
        .receipt-info h2 {
            margin: 0 0 15px 0;
            color: #2c3e50;
            font-size: 20px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        .info-item {
            display: flex;
        }
        
        .info-label {
            font-weight: bold;
            min-width: 80px;
        }
        
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        
        .items-table th {
            background: #2c3e50;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: bold;
        }
        
        .items-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #ddd;
        }
        
        .items-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .items-table tr:hover {
            background: #e9ecef;
        }
        
        .totals {
            text-align: right;
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .totals .total-line {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding: 5px 0;
        }
        
        .totals .total-final {
            font-size: 18px;
            font-weight: bold;
            border-top: 2px solid #2c3e50;
            padding-top: 10px;
            color: #2c3e50;
        }
        
        .observations {
            margin-top: 30px;
            padding: 15px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #2c3e50;
            color: #666;
        }
        
        .receipt-type {
            font-size: 16px;
            font-weight: bold;
            color: #e74c3c;
        }
        
        @media print {
            body { margin: 0; padding: 10px; }
            .receipt-container { box-shadow: none; padding: 0; }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>"""
    
    def _get_default_client_template(self) -> str:
        """Default client receipt template"""
        return """{% extends "base.html" %}

{% block title %}Talão Cliente - {{ receipt.numero }}{% endblock %}

{% block content %}
<div class="receipt-container">
    <div class="header">
        <h1>🌲 {{ empresa.nome }}</h1>
        <div class="company-info">
            <div>{{ empresa.endereco }}</div>
            <div>{{ empresa.cidade }}</div>
            <div>Tel: {{ empresa.telefone }} | CNPJ: {{ empresa.cnpj }}</div>
        </div>
    </div>
    
    <div class="receipt-info">
        <h2>TALÃO DO CLIENTE</h2>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Número:</span>
                <span>{{ receipt.numero }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Data:</span>
                <span>{{ data_emissao }}</span>
            </div>
            <div class="info-item" style="grid-column: 1 / -1;">
                <span class="info-label">Cliente:</span>
                <span>{{ receipt.cliente_nome }}</span>
            </div>
        </div>
    </div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th>Código</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Preço Unit.</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in receipt.items %}
            <tr>
                <td>{{ item.produto_codigo }}</td>
                <td>{{ item.descricao }}</td>
                <td>{{ item.quantidade }}</td>
                <td>R$ {{ "%.2f"|format(item.preco_unitario) }}</td>
                <td>R$ {{ "%.2f"|format(item.subtotal) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals">
        <div class="total-line">
            <span>Subtotal:</span>
            <span>R$ {{ "%.2f"|format(receipt.subtotal) }}</span>
        </div>
        <div class="total-line">
            <span>Frete:</span>
            <span>R$ {{ "%.2f"|format(receipt.frete) }}</span>
        </div>
        <div class="total-line total-final">
            <span>TOTAL GERAL:</span>
            <span>R$ {{ "%.2f"|format(receipt.total) }}</span>
        </div>
    </div>
    
    {% if receipt.observacoes %}
    <div class="observations">
        <strong>Observações:</strong><br>
        {{ receipt.observacoes }}
    </div>
    {% endif %}
    
    <div class="footer">
        <p><strong>Obrigado pela preferência!</strong></p>
        <p class="receipt-type">*** VIA DO CLIENTE ***</p>
        <p><em>Guarde este comprovante para garantias e trocas</em></p>
    </div>
</div>
{% endblock %}"""
    
    def _get_default_store_template(self) -> str:
        """Default store receipt template"""
        return """{% extends "base.html" %}

{% block title %}Talão Loja - {{ receipt.numero }}{% endblock %}

{% block extra_css %}
<style>
    .store-specific {
        background: #e8f4f8;
        border-left-color: #3498db;
    }
    .receipt-type {
        color: #3498db;
    }
</style>
{% endblock %}

{% block content %}
<div class="receipt-container">
    <div class="header">
        <h1>🌲 {{ empresa.nome }}</h1>
        <div class="company-info">
            <div>{{ empresa.endereco }}</div>
            <div>{{ empresa.cidade }}</div>
            <div>Tel: {{ empresa.telefone }} | CNPJ: {{ empresa.cnpj }}</div>
        </div>
    </div>
    
    <div class="receipt-info store-specific">
        <h2>TALÃO DA LOJA</h2>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Número:</span>
                <span>{{ receipt.numero }}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Data:</span>
                <span>{{ data_emissao }}</span>
            </div>
            <div class="info-item" style="grid-column: 1 / -1;">
                <span class="info-label">Cliente:</span>
                <span>{{ receipt.cliente_nome }}</span>
            </div>
        </div>
    </div>
    
    <table class="items-table">
        <thead>
            <tr>
                <th>Código</th>
                <th>Descrição</th>
                <th>Qtd</th>
                <th>Preço Unit.</th>
                <th>Total</th>
                <th>Peso (kg)</th>
            </tr>
        </thead>
        <tbody>
            {% for item in receipt.items %}
            <tr>
                <td>{{ item.produto_codigo }}</td>
                <td>{{ item.descricao }}</td>
                <td>{{ item.quantidade }}</td>
                <td>R$ {{ "%.2f"|format(item.preco_unitario) }}</td>
                <td>R$ {{ "%.2f"|format(item.subtotal) }}</td>
                <td>{{ "%.3f"|format(item.peso * item.quantidade) if item.peso else "N/A" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <div class="totals">
        <div class="total-line">
            <span>Subtotal:</span>
            <span>R$ {{ "%.2f"|format(receipt.subtotal) }}</span>
        </div>
        <div class="total-line">
            <span>Frete:</span>
            <span>R$ {{ "%.2f"|format(receipt.frete) }}</span>
        </div>
        <div class="total-line total-final">
            <span>TOTAL GERAL:</span>
            <span>R$ {{ "%.2f"|format(receipt.total) }}</span>
        </div>
    </div>
    
    {% if receipt.observacoes %}
    <div class="observations">
        <strong>Observações:</strong><br>
        {{ receipt.observacoes }}
    </div>
    {% endif %}
    
    <div class="footer">
        <p class="receipt-type">*** VIA DA LOJA ***</p>
        <p><em>Arquivo interno para controle</em></p>
    </div>
</div>
{% endblock %}"""
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        templates = []
        for template_dir in [self.templates_dir, self.default_templates_dir]:
            if os.path.exists(template_dir):
                for file in os.listdir(template_dir):
                    if file.endswith('.html') and file not in templates:
                        templates.append(file)
        return templates
    
    def save_custom_template(self, name: str, content: str) -> bool:
        """Save a custom template"""
        try:
            template_path = os.path.join(self.templates_dir, name)
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved custom template: {name}")
            return True
        except Exception as e:
            logger.error(f"Error saving template {name}: {e}")
            return False