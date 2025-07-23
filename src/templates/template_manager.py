"""
Template Manager Module
Manages all templates for the PDV system
"""
import logging
import os
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger(__name__)

class TemplateManager:
    """Central template manager for the PDV system"""
    
    def __init__(self, templates_dir: str = None):
        self.templates_dir = templates_dir or os.path.join('src', 'templates')
        self.default_templates_dir = os.path.join(self.templates_dir, 'default_templates')
        self.custom_templates_dir = os.path.join(self.templates_dir, 'custom')
        
        # Ensure template directories exist
        for dir_path in [self.templates_dir, self.default_templates_dir, self.custom_templates_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader([
                self.custom_templates_dir,
                self.default_templates_dir,
                self.templates_dir
            ]),
            autoescape=True
        )
        
        # Create default templates
        self.create_default_templates()
    
    def render_template(self, template_name: str, data: Dict[str, Any]) -> str:
        """Render template with provided data"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**data)
            
        except TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise
    
    def create_default_templates(self):
        """Create default templates if they don't exist"""
        templates = {
            'report_base.html': self._get_report_base_template(),
            'email_base.html': self._get_email_base_template(),
            'receipt_styles.css': self._get_receipt_styles(),
        }
        
        for template_name, content in templates.items():
            template_path = os.path.join(self.default_templates_dir, template_name)
            if not os.path.exists(template_path):
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Created default template: {template_name}")
    
    def _get_report_base_template(self) -> str:
        """Base template for reports"""
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Relatório{% endblock %}</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }
        
        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            background: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        
        .report-header {
            text-align: center;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .report-header h1 {
            margin: 0;
            color: #2c3e50;
            font-size: 28px;
        }
        
        .report-meta {
            margin-bottom: 30px;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 5px;
        }
        
        .report-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        
        .report-table th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
        }
        
        .report-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }
        
        .report-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        
        .report-summary {
            background: #e8f6f3;
            padding: 20px;
            border-radius: 5px;
            margin-top: 30px;
        }
        
        @media print {
            body { margin: 0; padding: 10px; background: white; }
            .report-container { box-shadow: none; padding: 0; }
        }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
</body>
</html>"""
    
    def _get_email_base_template(self) -> str:
        """Base template for email notifications"""
        return """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Notificação - Madeireira Maria Luiza{% endblock %}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }
        
        .email-container {
            max-width: 600px;
            margin: 20px auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .email-header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .email-content {
            padding: 30px;
        }
        
        .email-footer {
            background: #ecf0f1;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
        }
        
        .button {
            display: inline-block;
            padding: 12px 24px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
        }
        
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        
        .alert-info { background: #d1ecf1; border-left: 4px solid #bee5eb; }
        .alert-warning { background: #fff3cd; border-left: 4px solid #ffeaa7; }
        .alert-danger { background: #f8d7da; border-left: 4px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1>🌲 Madeireira Maria Luiza</h1>
            <p>{% block subtitle %}Sistema de Gestão{% endblock %}</p>
        </div>
        
        <div class="email-content">
            {% block content %}{% endblock %}
        </div>
        
        <div class="email-footer">
            <p>Este é um email automático do sistema PDV</p>
            <p>Madeireira Maria Luiza - Pau Amarelo, PE</p>
        </div>
    </div>
</body>
</html>"""
    
    def _get_receipt_styles(self) -> str:
        """CSS styles for receipts"""
        return """/* Receipt Styles for Madeireira Maria Luiza */

.receipt-container {
    font-family: 'Courier New', monospace;
    max-width: 300px;
    margin: 0 auto;
    padding: 10px;
    border: 1px solid #000;
}

.receipt-header {
    text-align: center;
    border-bottom: 1px dashed #000;
    padding-bottom: 10px;
    margin-bottom: 10px;
}

.company-name {
    font-weight: bold;
    font-size: 16px;
    margin-bottom: 5px;
}

.company-info {
    font-size: 10px;
    line-height: 1.2;
}

.receipt-number {
    text-align: center;
    font-weight: bold;
    margin: 10px 0;
    padding: 5px;
    background: #f0f0f0;
}

.customer-info {
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 1px dashed #000;
}

.items-list {
    margin-bottom: 10px;
}

.item-row {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2px;
    font-size: 10px;
}

.item-description {
    flex: 1;
    margin-right: 10px;
}

.item-total {
    text-align: right;
    min-width: 60px;
}

.totals-section {
    border-top: 1px dashed #000;
    padding-top: 5px;
    text-align: right;
}

.total-line {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2px;
}

.final-total {
    font-weight: bold;
    font-size: 14px;
    border-top: 1px solid #000;
    padding-top: 5px;
    margin-top: 5px;
}

.receipt-footer {
    text-align: center;
    margin-top: 15px;
    padding-top: 10px;
    border-top: 1px dashed #000;
    font-size: 10px;
}

/* Print styles */
@media print {
    .receipt-container {
        border: none;
        max-width: none;
        width: 80mm;
    }
    
    body {
        margin: 0;
        padding: 0;
    }
}

/* Thermal printer styles */
.thermal-receipt {
    width: 80mm;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.2;
}

.thermal-receipt .large-text {
    font-size: 16px;
    font-weight: bold;
}

.thermal-receipt .small-text {
    font-size: 10px;
}

.thermal-receipt .center {
    text-align: center;
}

.thermal-receipt .right {
    text-align: right;
}

.thermal-receipt .separator {
    border-bottom: 1px dashed #000;
    margin: 5px 0;
}"""
    
    def get_available_templates(self) -> List[str]:
        """Get list of available templates"""
        templates = []
        
        for template_dir in [self.custom_templates_dir, self.default_templates_dir]:
            if os.path.exists(template_dir):
                for file in os.listdir(template_dir):
                    if file.endswith(('.html', '.css', '.txt')) and file not in templates:
                        templates.append(file)
        
        return sorted(templates)
    
    def save_custom_template(self, name: str, content: str) -> bool:
        """Save a custom template"""
        try:
            template_path = os.path.join(self.custom_templates_dir, name)
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved custom template: {name}")
            return True
        except Exception as e:
            logger.error(f"Error saving template {name}: {e}")
            return False
    
    def delete_custom_template(self, name: str) -> bool:
        """Delete a custom template"""
        try:
            template_path = os.path.join(self.custom_templates_dir, name)
            if os.path.exists(template_path):
                os.remove(template_path)
                logger.info(f"Deleted custom template: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting template {name}: {e}")
            return False
    
    def get_template_content(self, name: str) -> Optional[str]:
        """Get template content for editing"""
        try:
            # First try custom templates
            custom_path = os.path.join(self.custom_templates_dir, name)
            if os.path.exists(custom_path):
                with open(custom_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Then try default templates
            default_path = os.path.join(self.default_templates_dir, name)
            if os.path.exists(default_path):
                with open(default_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading template {name}: {e}")
            return None
    
    def validate_template(self, content: str) -> Dict[str, Any]:
        """Validate template syntax"""
        try:
            # Try to parse the template
            self.env.from_string(content)
            return {'valid': True, 'message': 'Template is valid'}
            
        except Exception as e:
            return {'valid': False, 'message': str(e)}
    
    def preview_template(self, template_name: str, sample_data: Dict[str, Any]) -> str:
        """Generate preview of template with sample data"""
        try:
            return self.render_template(template_name, sample_data)
        except Exception as e:
            logger.error(f"Error previewing template {template_name}: {e}")
            return f"<html><body><h1>Error previewing template</h1><p>{e}</p></body></html>"