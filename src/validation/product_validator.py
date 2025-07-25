"""
Enhanced Product Validator Module
Provides comprehensive product validation with real-time feedback
"""
import sqlite3
import re
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, InvalidOperation


class ProductValidator:
    """Enhanced product validation with real-time feedback"""
    
    def __init__(self, db_path: str = "dados/produtos_sic.db"):
        self.db_path = db_path
        
    def validate_required_fields(self, product_data: Dict[str, Any], is_update: bool = False) -> List[str]:
        """Validate required fields"""
        errors = []
        
        # Required fields for new products
        if not is_update:
            required_fields = {
                'codigo': 'Código do produto',
                'descricao': 'Descrição',
                'preco_venda': 'Preço de venda'
            }
            
            for field, label in required_fields.items():
                value = product_data.get(field, '')
                if not str(value).strip():
                    errors.append(f"{label} é obrigatório")
        
        return errors
    
    def validate_product_code(self, codigo: str, is_update: bool = False, original_code: str = None) -> List[str]:
        """Validate product code format and uniqueness"""
        errors = []
        
        if not codigo or not codigo.strip():
            errors.append("Código do produto é obrigatório")
            return errors
        
        codigo = codigo.strip()
        
        # Validate format (alphanumeric, max 20 chars)
        if not re.match(r'^[A-Za-z0-9_-]+$', codigo):
            errors.append("Código deve conter apenas letras, números, _ ou -")
        
        if len(codigo) > 20:
            errors.append("Código deve ter no máximo 20 caracteres")
        
        if len(codigo) < 2:
            errors.append("Código deve ter pelo menos 2 caracteres")
        
        # Check uniqueness only for new products or when code changes
        if not is_update or (is_update and codigo != original_code):
            if self._code_exists(codigo):
                errors.append(f"Código '{codigo}' já existe no sistema")
        
        return errors
    
    def validate_description(self, descricao: str) -> List[str]:
        """Validate product description"""
        errors = []
        
        if not descricao or not descricao.strip():
            errors.append("Descrição é obrigatória")
            return errors
        
        descricao = descricao.strip()
        
        if len(descricao) < 3:
            errors.append("Descrição deve ter pelo menos 3 caracteres")
        
        if len(descricao) > 200:
            errors.append("Descrição deve ter no máximo 200 caracteres")
        
        # Check for suspicious characters
        if re.search(r'[<>"]', descricao):
            errors.append("Descrição contém caracteres não permitidos")
        
        return errors
    
    def validate_price(self, preco: Any, field_name: str = "Preço de venda", allow_zero: bool = False) -> List[str]:
        """Validate price fields"""
        errors = []
        
        if preco is None or preco == '':
            if field_name == "Preço de venda":
                errors.append(f"{field_name} é obrigatório")
            return errors
        
        try:
            # Handle string prices with comma as decimal separator
            if isinstance(preco, str):
                preco = preco.replace(',', '.').strip()
                if not preco:
                    if field_name == "Preço de venda":
                        errors.append(f"{field_name} é obrigatório")
                    return errors
            
            preco_decimal = Decimal(str(preco))
            
            # Validate range
            if not allow_zero and preco_decimal <= 0:
                errors.append(f"{field_name} deve ser maior que zero")
            elif allow_zero and preco_decimal < 0:
                errors.append(f"{field_name} não pode ser negativo")
            
            if preco_decimal > Decimal('9999999.99'):
                errors.append(f"{field_name} é muito alto (máximo: R$ 9.999.999,99)")
            
            # Validate decimal places
            if preco_decimal.as_tuple().exponent < -2:
                errors.append(f"{field_name} deve ter no máximo 2 casas decimais")
                
        except (InvalidOperation, ValueError, TypeError):
            errors.append(f"{field_name} tem formato inválido")
        
        return errors
    
    def validate_stock(self, estoque: Any) -> List[str]:
        """Validate stock quantity"""
        errors = []
        
        if estoque is None or estoque == '':
            return errors  # Stock is optional
        
        try:
            estoque_int = int(estoque)
            
            if estoque_int < 0:
                errors.append("Estoque não pode ser negativo")
            
            if estoque_int > 999999:
                errors.append("Estoque é muito alto (máximo: 999.999)")
                
        except (ValueError, TypeError):
            errors.append("Estoque deve ser um número inteiro")
        
        return errors
    
    def validate_weight(self, peso: Any) -> List[str]:
        """Validate product weight"""
        errors = []
        
        if peso is None or peso == '':
            return errors  # Weight is optional
        
        try:
            if isinstance(peso, str):
                peso = peso.replace(',', '.').strip()
                if not peso:
                    return errors
            
            peso_decimal = Decimal(str(peso))
            
            if peso_decimal < 0:
                errors.append("Peso não pode ser negativo")
            
            if peso_decimal > Decimal('99999.999'):
                errors.append("Peso é muito alto (máximo: 99.999,999 kg)")
            
            # Validate decimal places
            if peso_decimal.as_tuple().exponent < -3:
                errors.append("Peso deve ter no máximo 3 casas decimais")
                
        except (InvalidOperation, ValueError, TypeError):
            errors.append("Peso tem formato inválido")
        
        return errors
    
    def validate_category(self, categoria: str) -> List[str]:
        """Validate product category"""
        errors = []
        
        if categoria and len(categoria.strip()) > 50:
            errors.append("Categoria deve ter no máximo 50 caracteres")
        
        return errors
    
    def validate_brand(self, marca: str) -> List[str]:
        """Validate product brand"""
        errors = []
        
        if marca and len(marca.strip()) > 50:
            errors.append("Marca deve ter no máximo 50 caracteres")
        
        return errors
    
    def validate_unit(self, unidade: str) -> List[str]:
        """Validate product unit"""
        errors = []
        
        valid_units = ['UN', 'KG', 'MT', 'LT', 'PC', 'CX', 'PCT', 'M2', 'M3']
        
        if unidade and unidade.upper() not in valid_units:
            errors.append(f"Unidade deve ser uma das opções: {', '.join(valid_units)}")
        
        return errors
    
    def validate_product_data(self, product_data: Dict[str, Any], is_update: bool = False, original_code: str = None) -> Dict[str, Any]:
        """Comprehensive product validation"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'field_errors': {}
        }
        
        # Validate required fields
        errors = self.validate_required_fields(product_data, is_update)
        result['errors'].extend(errors)
        
        # Validate individual fields
        validations = [
            ('codigo', self.validate_product_code, [product_data.get('codigo', ''), is_update, original_code]),
            ('descricao', self.validate_description, [product_data.get('descricao', '')]),
            ('preco_venda', self.validate_price, [product_data.get('preco_venda'), "Preço de venda", False]),
            ('preco_custo', self.validate_price, [product_data.get('preco_custo'), "Preço de custo", True]),
            ('estoque', self.validate_stock, [product_data.get('estoque')]),
            ('peso', self.validate_weight, [product_data.get('peso')]),
            ('categoria', self.validate_category, [product_data.get('categoria', '')]),
            ('marca', self.validate_brand, [product_data.get('marca', '')]),
            ('unidade', self.validate_unit, [product_data.get('unidade', '')])
        ]
        
        for field_name, validator, args in validations:
            field_errors = validator(*args)
            if field_errors:
                result['field_errors'][field_name] = field_errors
                result['errors'].extend(field_errors)
        
        # Business logic validations
        if (product_data.get('preco_custo') and product_data.get('preco_venda')):
            try:
                custo = Decimal(str(product_data['preco_custo']).replace(',', '.'))
                venda = Decimal(str(product_data['preco_venda']).replace(',', '.'))
                
                if custo > venda:
                    result['warnings'].append("Preço de custo é maior que o preço de venda")
                
                # Calculate margin
                if custo > 0:
                    margem = ((venda - custo) / custo) * 100
                    if margem < 10:
                        result['warnings'].append(f"Margem de lucro baixa: {margem:.1f}%")
                        
            except (ValueError, InvalidOperation):
                pass  # Already handled in individual validations
        
        result['is_valid'] = len(result['errors']) == 0
        
        return result
    
    def _code_exists(self, codigo: str) -> bool:
        """Check if product code exists in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM produtos WHERE codigo = ? LIMIT 1", (codigo,))
            exists = cursor.fetchone() is not None
            
            conn.close()
            return exists
            
        except sqlite3.Error:
            return False  # Assume doesn't exist if we can't check
    
    def get_validation_suggestions(self, field_name: str, value: str) -> List[str]:
        """Get real-time validation suggestions"""
        suggestions = []
        
        if field_name == 'codigo':
            if value and not re.match(r'^[A-Za-z0-9_-]+$', value):
                suggestions.append("Use apenas letras, números, _ ou -")
            if len(value) > 20:
                suggestions.append("Máximo 20 caracteres")
        
        elif field_name == 'descricao':
            if len(value) > 200:
                suggestions.append("Máximo 200 caracteres")
            if len(value) < 3 and value:
                suggestions.append("Mínimo 3 caracteres")
        
        elif field_name in ['preco_venda', 'preco_custo']:
            if value and ',' in value and '.' in value:
                suggestions.append("Use vírgula OU ponto como separador decimal")
        
        return suggestions
    
    def format_price_display(self, price: Any) -> str:
        """Format price for display"""
        try:
            if price is None or price == '':
                return ''
            
            if isinstance(price, str):
                price = price.replace(',', '.')
            
            price_decimal = Decimal(str(price))
            return f"R$ {price_decimal:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
        except (ValueError, InvalidOperation):
            return str(price) if price else ''