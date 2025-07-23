#!/usr/bin/env python3
"""
Test Script for PDV System
Tests core functionality without GUI
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.database import SICConnection, LocalDatabase, Product
        print("✅ Database modules imported successfully")
        
        from src.products import ProductManager, SyncManager, InventoryManager
        print("✅ Product modules imported successfully")
        
        from src.reports import ReportGenerator, ExcelReportGenerator, TxtReportGenerator
        print("✅ Report modules imported successfully")
        
        from src.receipts import ReceiptGenerator, ReceiptTemplateManager
        print("✅ Receipt modules imported successfully")
        
        from src.templates import TemplateManager
        print("✅ Template modules imported successfully")
        
        from src.utils import ConfigManager, PDVLogger, get_default_logger
        print("✅ Utility modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration management"""
    print("\n🧪 Testing configuration...")
    
    try:
        from src.utils import ConfigManager
        
        config_manager = ConfigManager()
        
        # Test getting config
        app_info = config_manager.get_app_info()
        print(f"✅ App info loaded: {app_info.get('name', 'Unknown')}")
        
        business_info = config_manager.get_business_info()
        print(f"✅ Business info loaded: {business_info.get('nome_empresa', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\n🧪 Testing database...")
    
    try:
        from src.database import LocalDatabase
        
        # Test local database
        local_db = LocalDatabase()
        print("✅ Local database initialized")
        
        # Test sync status
        sync_status = local_db.get_sync_status()
        print(f"✅ Sync status retrieved: {sync_status.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_product_manager():
    """Test product management"""
    print("\n🧪 Testing product manager...")
    
    try:
        from src.products import ProductManager
        
        product_manager = ProductManager()
        print("✅ Product manager initialized")
        
        # Test getting products (will use local cache if SIC unavailable)
        products = product_manager.get_all_products(force_local=True)
        print(f"✅ Products retrieved: {len(products)} products found")
        
        return True
        
    except Exception as e:
        print(f"❌ Product manager test failed: {e}")
        return False

def test_reports():
    """Test report generation"""
    print("\n🧪 Testing reports...")
    
    try:
        from src.products import ProductManager
        from src.reports import ReportGenerator
        from src.database import ReportConfig
        
        product_manager = ProductManager()
        report_generator = ReportGenerator(product_manager)
        
        print("✅ Report generator initialized")
        
        # Test available reports
        available_reports = report_generator.get_available_reports()
        print(f"✅ Available reports: {len(available_reports)} types")
        
        return True
        
    except Exception as e:
        print(f"❌ Report test failed: {e}")
        return False

def test_templates():
    """Test template system"""
    print("\n🧪 Testing templates...")
    
    try:
        from src.templates import TemplateManager
        
        template_manager = TemplateManager()
        print("✅ Template manager initialized")
        
        # Test available templates
        templates = template_manager.get_available_templates()
        print(f"✅ Available templates: {len(templates)} templates")
        
        return True
        
    except Exception as e:
        print(f"❌ Template test failed: {e}")
        return False

def test_receipts():
    """Test receipt generation"""
    print("\n🧪 Testing receipts...")
    
    try:
        from src.receipts import ReceiptGenerator
        
        receipt_generator = ReceiptGenerator()
        print("✅ Receipt generator initialized")
        
        # Test sample receipt creation
        sample_items = [
            {
                'codigo': '001',
                'descricao': 'Produto Teste',
                'quantidade': 1,
                'preco_unitario': 10.00,
                'peso': 1.0
            }
        ]
        
        receipt_data = receipt_generator.create_receipt('Cliente Teste', sample_items)
        
        if receipt_data['success']:
            print(f"✅ Sample receipt created: {receipt_data['numero']}")
        else:
            print(f"❌ Receipt creation failed: {receipt_data.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Receipt test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🌲 SISTEMA PDV - MADEIREIRA MARIA LUIZA")
    print("📋 Running system tests...\n")
    
    tests = [
        test_imports,
        test_config,
        test_database,
        test_product_manager,
        test_reports,
        test_templates,
        test_receipts
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ Test failed!")
        except Exception as e:
            print(f"❌ Test crashed: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! System is ready.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())