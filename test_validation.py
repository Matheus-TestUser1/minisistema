#!/usr/bin/env python3
"""
Simple tests for the enhanced validation system
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.validation.product_validator import ProductValidator
from src.security.config_manager import SecureConfigManager

def test_product_validation():
    """Test product validation functionality"""
    print("🔬 Testing Product Validation...")
    
    validator = ProductValidator()
    
    # Test valid product
    valid_product = {
        'codigo': 'PROD001',
        'descricao': 'Produto de teste válido',
        'preco_venda': '15.50',
        'preco_custo': '10.00',
        'estoque': '100',
        'categoria': 'Categoria A',
        'marca': 'Marca X',
        'unidade': 'UN',
        'peso': '1.5'
    }
    
    result = validator.validate_product_data(valid_product)
    assert result['is_valid'], f"Valid product failed validation: {result['errors']}"
    print("✅ Valid product validation passed")
    
    # Test invalid product (missing required fields)
    invalid_product = {
        'codigo': '',
        'descricao': '',
        'preco_venda': ''
    }
    
    result = validator.validate_product_data(invalid_product)
    assert not result['is_valid'], "Invalid product passed validation"
    assert len(result['errors']) > 0, "No errors reported for invalid product"
    print("✅ Invalid product validation passed")
    
    # Test price validation
    invalid_price_product = {
        'codigo': 'PROD002',
        'descricao': 'Produto com preço inválido',
        'preco_venda': '-10.50'  # Negative price
    }
    
    result = validator.validate_product_data(invalid_price_product)
    assert not result['is_valid'], "Negative price passed validation"
    print("✅ Price validation passed")
    
    # Test code uniqueness (will fail since we don't have real DB in test)
    # This would be tested in integration tests
    print("✅ All product validation tests passed!")
    
def test_secure_config():
    """Test secure configuration manager"""
    print("🔒 Testing Secure Configuration...")
    
    config_manager = SecureConfigManager()
    
    # Test loading legacy config
    legacy_config = config_manager.load_legacy_config()
    print(f"Legacy config loaded: {bool(legacy_config)}")
    
    # Test session management
    assert not config_manager.has_valid_session(), "Should not have valid session initially"
    print("✅ Session management test passed")
    
    print("✅ All secure configuration tests passed!")

def test_validation_edge_cases():
    """Test edge cases in validation"""
    print("⚠️  Testing Edge Cases...")
    
    validator = ProductValidator()
    
    # Test very long description
    long_desc_product = {
        'codigo': 'PROD003',
        'descricao': 'A' * 250,  # Too long
        'preco_venda': '10.00'
    }
    
    result = validator.validate_product_data(long_desc_product)
    assert not result['is_valid'], "Long description passed validation"
    print("✅ Long description validation passed")
    
    # Test price with comma (Brazilian format)
    comma_price_product = {
        'codigo': 'PROD004',
        'descricao': 'Produto com vírgula',
        'preco_venda': '15,50'  # Brazilian format
    }
    
    result = validator.validate_product_data(comma_price_product)
    assert result['is_valid'], f"Comma price failed validation: {result['errors']}"
    print("✅ Comma price validation passed")
    
    # Test invalid characters in code
    invalid_code_product = {
        'codigo': 'PROD@#$',  # Invalid characters
        'descricao': 'Produto teste',
        'preco_venda': '10.00'
    }
    
    result = validator.validate_product_data(invalid_code_product)
    assert not result['is_valid'], "Invalid code characters passed validation"
    print("✅ Code character validation passed")
    
    print("✅ All edge case tests passed!")

if __name__ == "__main__":
    print("🧪 Running Enhanced Validation Tests\n")
    
    try:
        test_product_validation()
        print()
        test_secure_config()
        print()
        test_validation_edge_cases()
        
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)