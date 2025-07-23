"""
Dashboard Module
Provides overview and quick access to system functions
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class Dashboard:
    """Dashboard widget showing system overview"""
    
    def __init__(self, parent, main_window):
        self.parent = parent
        self.main_window = main_window
        self.frame = ttk.Frame(parent)
        
        self.create_dashboard()
        self.update_data()
    
    def create_dashboard(self):
        """Create dashboard layout"""
        # Title
        title_label = tk.Label(
            self.frame,
            text="📊 Dashboard - Visão Geral do Sistema",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Main content area
        content_frame = ttk.Frame(self.frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Left column - System status
        left_frame = ttk.LabelFrame(content_frame, text="🔧 Status do Sistema")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.system_status_text = tk.Text(left_frame, height=15, wrap=tk.WORD, font=("Consolas", 9))
        system_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.system_status_text.yview)
        self.system_status_text.config(yscrollcommand=system_scrollbar.set)
        
        self.system_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        system_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Right column - Quick actions and stats
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Quick stats
        stats_frame = ttk.LabelFrame(right_frame, text="📈 Estatísticas Rápidas")
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD, font=("Arial", 10))
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.config(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(right_frame, text="⚡ Ações Rápidas")
        actions_frame.pack(fill=tk.X)
        
        # Action buttons
        ttk.Button(
            actions_frame,
            text="🔄 Sincronizar Agora",
            command=self.main_window.force_sync
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            actions_frame,
            text="📦 Atualizar Produtos",
            command=self.main_window.refresh_products
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            actions_frame,
            text="📊 Relatório de Estoque",
            command=self.generate_inventory_report
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            actions_frame,
            text="⚠️ Produtos em Falta",
            command=self.main_window.show_low_stock
        ).pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(
            actions_frame,
            text="🔄 Atualizar Dashboard",
            command=self.update_data
        ).pack(fill=tk.X, padx=5, pady=2)
        
        # Bottom update info
        self.last_update_var = tk.StringVar(value="Última atualização: --")
        update_label = ttk.Label(self.frame, textvariable=self.last_update_var, font=("Arial", 8))
        update_label.pack(side=tk.BOTTOM, pady=5)
    
    def update_data(self):
        """Update dashboard data"""
        try:
            # Update system status
            self.update_system_status()
            
            # Update statistics
            self.update_statistics()
            
            # Update timestamp
            self.last_update_var.set(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def update_system_status(self):
        """Update system status display"""
        try:
            # Clear text
            self.system_status_text.delete(1.0, tk.END)
            
            # Get sync status
            sync_stats = self.main_window.sync_manager.get_sync_statistics()
            
            # Build status text
            status_text = f"""🔧 SISTEMA PDV - STATUS GERAL
{'=' * 40}

🔌 CONEXÃO SIC:
   Status: {'🟢 Online' if sync_stats.get('sic_available') else '🔴 Offline'}
   Modo: {'Online' if not sync_stats.get('offline_mode') else 'Offline (Cache Local)'}

🔄 SINCRONIZAÇÃO:
   Auto-sync: {'✅ Ativo' if sync_stats.get('auto_sync_enabled') else '❌ Inativo'}
   Executando: {'✅ Sim' if sync_stats.get('auto_sync_running') else '❌ Não'}
   Intervalo: {sync_stats.get('sync_interval', 0)} segundos
   Última sync: {sync_stats.get('last_successful_sync', 'Nunca') or 'Nunca'}

💾 DADOS:
   Total produtos: {sync_stats.get('total_products', 0)}
   Movimentos pendentes: {sync_stats.get('pending_movements', 0)}
   Status: {sync_stats.get('status', 'Desconhecido')}

📊 CONFIGURAÇÃO:
   Versão: {self.main_window.config_manager.get_app_info().get('version', '1.0.0')}
   Empresa: {self.main_window.config_manager.get_business_info().get('nome_empresa', 'N/A')}
   Debug: {self.main_window.config_manager.get_app_info().get('debug', False)}
"""
            
            self.system_status_text.insert(1.0, status_text)
            
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
            self.system_status_text.delete(1.0, tk.END)
            self.system_status_text.insert(1.0, f"Erro ao carregar status do sistema: {e}")
    
    def update_statistics(self):
        """Update statistics display"""
        try:
            # Clear text
            self.stats_text.delete(1.0, tk.END)
            
            # Get inventory summary
            inventory_report = self.main_window.inventory_manager.get_stock_report()
            
            # Get low stock alerts
            low_stock_alerts = self.main_window.inventory_manager.get_low_stock_alert()
            
            # Build stats text
            stats_text = f"""📈 ESTATÍSTICAS RÁPIDAS
{'=' * 25}

📦 PRODUTOS:
   Total: {inventory_report.get('total_products', 0)}
   Valor total: R$ {inventory_report.get('total_stock_value', 0):.2f}

⚠️ ALERTAS:
   Em falta: {inventory_report.get('out_of_stock_count', 0)}
   Estoque baixo: {inventory_report.get('low_stock_count', 0)}
   Total alertas: {len(low_stock_alerts)}

📂 CATEGORIAS:
   Total: {len(inventory_report.get('categories', {}))}
"""
            
            # Top categories by value
            categories = inventory_report.get('categories', {})
            if categories:
                sorted_categories = sorted(categories.items(), key=lambda x: x[1]['total_value'], reverse=True)[:3]
                stats_text += "\n🏆 TOP CATEGORIAS:\n"
                for i, (cat_name, cat_data) in enumerate(sorted_categories, 1):
                    stats_text += f"   {i}. {cat_name}: R$ {cat_data['total_value']:.2f}\n"
            
            self.stats_text.insert(1.0, stats_text)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, f"Erro ao carregar estatísticas: {e}")
    
    def generate_inventory_report(self):
        """Generate quick inventory report"""
        try:
            from ..database import ReportConfig
            
            config = ReportConfig(
                tipo='excel',
                titulo=f'Relatório de Estoque - {datetime.now().strftime("%d/%m/%Y %H:%M")}'
            )
            
            result = self.main_window.report_generator.generate_inventory_report(config)
            
            if result['success']:
                self.main_window.status_var.set(f"✅ Relatório gerado: {result['filename']}")
            else:
                self.main_window.status_var.set(f"❌ Erro: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error generating inventory report: {e}")
            self.main_window.status_var.set(f"❌ Erro ao gerar relatório: {e}")