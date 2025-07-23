"""
Main Window Module
Central UI controller that integrates all system components
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
from typing import Dict, Any, Optional
import threading
import os
from datetime import datetime

# Import our new system modules
from ..products import ProductManager, SyncManager, InventoryManager  
from ..reports import ReportGenerator
from ..receipts import ReceiptGenerator
from ..utils import ConfigManager, PDVLogger, get_default_logger
from ..database import ReportConfig

from .dashboard import Dashboard
from .config_window import ConfigWindow

logger = get_default_logger()

class MainWindow:
    """Main application window with integrated system functionality"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌲 Sistema PDV - Madeireira Maria Luiza")
        
        # Initialize system components
        self.config_manager = ConfigManager()
        self.product_manager = ProductManager()
        self.sync_manager = SyncManager(self.product_manager)
        self.inventory_manager = InventoryManager(self.product_manager)
        self.report_generator = ReportGenerator(self.product_manager)
        self.receipt_generator = ReceiptGenerator()
        
        # UI state variables
        self.status_var = tk.StringVar(value="🟡 Sistema iniciado - Verificando SIC...")
        self.sic_status_var = tk.StringVar(value="🔴 SIC: Verificando...")
        self.sync_status_var = tk.StringVar(value="💾 Dados: Cache local")
        
        # Setup UI
        self.setup_window()
        self.create_interface()
        self.setup_sync_callbacks()
        self.start_background_tasks()
        
        logger.info("Main window initialized")
    
    def setup_window(self):
        """Configure main window properties"""
        ui_config = self.config_manager.get_config('ui_config', 'window')
        
        # Window size and position
        width = ui_config.get('width', 1200)
        height = ui_config.get('height', 800)
        
        if ui_config.get('center_on_screen', True):
            # Center window on screen
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.root.geometry(f"{width}x{height}")
        
        # Window properties
        self.root.resizable(ui_config.get('resizable', True), ui_config.get('resizable', True))
        
        # Icon (if available)
        try:
            icon_path = os.path.join('assets', 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Icon not available
    
    def create_interface(self):
        """Create the main interface"""
        # Title bar
        self.create_title_bar()
        
        # Status panel
        self.create_status_panel()
        
        # Main content area with tabs
        self.create_main_content()
        
        # Status bar at bottom
        self.create_status_bar()
    
    def create_title_bar(self):
        """Create title bar with company branding"""
        business_info = self.config_manager.get_business_info()
        
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text=f"🌲 {business_info.get('nome_empresa', 'MADEIREIRA MARIA LUIZA')} - SISTEMA PDV",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(expand=True)
        
        # Version info
        app_info = self.config_manager.get_app_info()
        version_label = tk.Label(
            title_frame,
            text=f"v{app_info.get('version', '1.0.0')}",
            font=("Arial", 8),
            bg="#2c3e50",
            fg="#bdc3c7"
        )
        version_label.place(relx=0.98, rely=0.1, anchor='ne')
    
    def create_status_panel(self):
        """Create status indicators panel"""
        status_frame = ttk.LabelFrame(self.root, text="📊 Status do Sistema")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Left side - System status
        left_frame = tk.Frame(status_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, textvariable=self.sic_status_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Label(left_frame, textvariable=self.sync_status_var).pack(side=tk.LEFT, padx=10)
        
        # Right side - Control buttons  
        right_frame = tk.Frame(status_frame)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="🔄 Sincronizar", command=self.force_sync).pack(side=tk.RIGHT, padx=5)
        ttk.Button(right_frame, text="⚙️ Config", command=self.open_config).pack(side=tk.RIGHT, padx=5)
    
    def create_main_content(self):
        """Create main content area with tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Dashboard tab
        self.dashboard = Dashboard(self.notebook, self)
        self.notebook.add(self.dashboard.frame, text="📊 Dashboard")
        
        # Products tab
        self.create_products_tab()
        
        # Reports tab  
        self.create_reports_tab()
        
        # Receipts tab
        self.create_receipts_tab()
        
        # Inventory tab
        self.create_inventory_tab()
    
    def create_products_tab(self):
        """Create products management tab"""
        products_frame = ttk.Frame(self.notebook)
        self.notebook.add(products_frame, text="📦 Produtos")
        
        # Search frame
        search_frame = ttk.LabelFrame(products_frame, text="🔍 Buscar Produtos")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 11))
        search_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        ttk.Button(search_frame, text="🔍 Buscar", command=self.search_products).pack(side=tk.RIGHT, padx=5)
        ttk.Button(search_frame, text="🔄 Atualizar", command=self.refresh_products).pack(side=tk.RIGHT, padx=5)
        
        # Products treeview
        tree_frame = ttk.Frame(products_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        # Treeview
        self.products_tree = ttk.Treeview(
            tree_frame,
            columns=('codigo', 'descricao', 'categoria', 'preco', 'estoque', 'valor_total'),
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Configure scrollbars
        v_scrollbar.config(command=self.products_tree.yview)
        h_scrollbar.config(command=self.products_tree.xview)
        
        # Column headings
        columns = {
            'codigo': ('Código', 80),
            'descricao': ('Descrição', 300),
            'categoria': ('Categoria', 120),
            'preco': ('Preço', 100),
            'estoque': ('Estoque', 80),
            'valor_total': ('Valor Total', 120)
        }
        
        for col, (heading, width) in columns.items():
            self.products_tree.heading(col, text=heading)
            self.products_tree.column(col, width=width, anchor='center' if col != 'descricao' else 'w')
        
        # Pack treeview and scrollbars
        self.products_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Load initial data
        self.refresh_products()
    
    def create_reports_tab(self):
        """Create reports generation tab"""
        reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(reports_frame, text="📋 Relatórios")
        
        # Report selection
        selection_frame = ttk.LabelFrame(reports_frame, text="📊 Tipo de Relatório")
        selection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.report_type_var = tk.StringVar(value="products")
        
        reports = [
            ("products", "📦 Relatório de Produtos"),
            ("inventory", "📊 Relatório de Estoque"),
            ("low_stock", "⚠️ Produtos em Falta"),
            ("price_list", "💰 Lista de Preços"),
            ("categories", "📂 Relatório por Categoria"),
            ("reorder", "🔄 Sugestões de Reposição")
        ]
        
        for value, text in reports:
            ttk.Radiobutton(
                selection_frame,
                text=text,
                value=value,
                variable=self.report_type_var
            ).pack(anchor=tk.W, padx=10, pady=2)
        
        # Format selection
        format_frame = ttk.LabelFrame(reports_frame, text="📄 Formato")
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.report_format_var = tk.StringVar(value="excel")
        
        ttk.Radiobutton(format_frame, text="📊 Excel", value="excel", variable=self.report_format_var).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_frame, text="📄 Texto", value="txt", variable=self.report_format_var).pack(side=tk.LEFT, padx=10)
        
        # Generate button
        ttk.Button(
            reports_frame,
            text="📋 Gerar Relatório",
            command=self.generate_report
        ).pack(pady=20)
    
    def create_receipts_tab(self):
        """Create receipts generation tab"""
        receipts_frame = ttk.Frame(self.notebook)
        self.notebook.add(receipts_frame, text="🧾 Talões")
        
        # Customer info
        customer_frame = ttk.LabelFrame(receipts_frame, text="👤 Dados do Cliente")
        customer_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(customer_frame, text="Nome:").pack(side=tk.LEFT, padx=5)
        self.customer_name_var = tk.StringVar()
        ttk.Entry(customer_frame, textvariable=self.customer_name_var, width=50).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Items frame (placeholder for now)
        items_frame = ttk.LabelFrame(receipts_frame, text="📦 Items do Talão")
        items_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(items_frame, text="Funcionalidade de adição de items será implementada na próxima versão").pack(pady=50)
        
        # Generate buttons
        buttons_frame = ttk.Frame(receipts_frame)
        buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(buttons_frame, text="🧾 Gerar Talão Cliente", command=lambda: self.generate_receipt('cliente')).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="🏪 Gerar Talão Loja", command=lambda: self.generate_receipt('loja')).pack(side=tk.LEFT, padx=5)
    
    def create_inventory_tab(self):
        """Create inventory management tab"""
        inventory_frame = ttk.Frame(self.notebook)
        self.notebook.add(inventory_frame, text="📊 Estoque")
        
        # Summary frame
        summary_frame = ttk.LabelFrame(inventory_frame, text="📊 Resumo do Estoque")
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.inventory_summary_text = tk.Text(summary_frame, height=8, wrap=tk.WORD)
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.inventory_summary_text.yview)
        self.inventory_summary_text.config(yscrollcommand=summary_scrollbar.set)
        
        self.inventory_summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        summary_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        controls_frame = ttk.Frame(inventory_frame)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="🔄 Atualizar Estoque", command=self.update_inventory_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="⚠️ Produtos em Falta", command=self.show_low_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="📊 Relatório Completo", command=self.export_inventory).pack(side=tk.LEFT, padx=5)
        
        # Load initial inventory data
        self.update_inventory_summary()
    
    def create_status_bar(self):
        """Create bottom status bar"""
        status_bar = tk.Frame(self.root, relief=tk.SUNKEN, bd=1)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(status_bar, textvariable=self.status_var, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Time display
        self.time_label = tk.Label(status_bar, text="", anchor=tk.E)
        self.time_label.pack(side=tk.RIGHT, padx=5)
        self.update_time()
    
    def setup_sync_callbacks(self):
        """Setup synchronization callbacks"""
        def sync_callback(result):
            if result['success']:
                self.sic_status_var.set("🟢 SIC: Online")
                self.sync_status_var.set(f"💾 Sincronizado: {result['products_synced']} produtos")
                self.status_var.set("✅ Sincronização concluída com sucesso")
            else:
                self.sic_status_var.set("🔴 SIC: Offline")
                self.sync_status_var.set("💾 Dados: Cache local")
                self.status_var.set("⚠️ Falha na sincronização - Modo offline")
        
        self.sync_manager.add_sync_callback(sync_callback)
    
    def start_background_tasks(self):
        """Start background tasks"""
        # Start auto sync
        self.sync_manager.start_auto_sync()
        
        # Initial sync test
        threading.Thread(target=self.test_initial_connection, daemon=True).start()
    
    def test_initial_connection(self):
        """Test initial connection in background"""
        try:
            result = self.sync_manager.test_sync_connection()
            if result['success']:
                self.root.after(0, lambda: self.sic_status_var.set("🟢 SIC: Online"))
            else:
                self.root.after(0, lambda: self.sic_status_var.set("🔴 SIC: Offline"))
        except Exception as e:
            logger.error(f"Error testing initial connection: {e}")
    
    # Event handlers
    def on_search_change(self, *args):
        """Handle search text change"""
        # Debounce search - could implement timer here
        pass
    
    def search_products(self):
        """Search products based on search term"""
        search_term = self.search_var.get().strip()
        
        if not search_term:
            self.refresh_products()
            return
        
        try:
            products = self.product_manager.search_products(search_term)
            self.update_products_tree(products)
            self.status_var.set(f"🔍 Encontrados {len(products)} produtos")
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            messagebox.showerror("Erro", f"Erro ao buscar produtos: {e}")
    
    def refresh_products(self):
        """Refresh products list"""
        try:
            products = self.product_manager.get_all_products()
            self.update_products_tree(products)
            self.status_var.set(f"📦 {len(products)} produtos carregados")
        except Exception as e:
            logger.error(f"Error refreshing products: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar produtos: {e}")
    
    def update_products_tree(self, products):
        """Update products treeview"""
        # Clear existing items
        for item in self.products_tree.get_children():
            self.products_tree.delete(item)
        
        # Add products
        for product in products:
            valor_total = float(product.preco_venda * product.estoque_atual)
            
            self.products_tree.insert('', 'end', values=(
                product.codigo,
                product.descricao,
                product.categoria or 'Sem Categoria',
                f"R$ {product.preco_venda:.2f}",
                product.estoque_atual,
                f"R$ {valor_total:.2f}"
            ))
    
    def force_sync(self):
        """Force synchronization"""
        def sync_task():
            try:
                self.status_var.set("🔄 Sincronizando...")
                result = self.sync_manager.force_sync()
                
                if result['success']:
                    self.root.after(0, lambda: self.status_var.set("✅ Sincronização concluída"))
                    self.root.after(0, self.refresh_products)
                else:
                    error_msg = ', '.join(result.get('errors', ['Erro desconhecido']))
                    self.root.after(0, lambda: self.status_var.set(f"❌ Erro na sincronização: {error_msg}"))
                    
            except Exception as e:
                logger.error(f"Error in force sync: {e}")
                self.root.after(0, lambda: self.status_var.set(f"❌ Erro: {e}"))
        
        threading.Thread(target=sync_task, daemon=True).start()
    
    def open_config(self):
        """Open configuration window"""
        try:
            config_window = ConfigWindow(self.root, self.config_manager)
            config_window.show()
        except Exception as e:
            logger.error(f"Error opening config window: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir configurações: {e}")
    
    def generate_report(self):
        """Generate selected report"""
        try:
            report_type = self.report_type_var.get()
            report_format = self.report_format_var.get()
            
            # Create report config
            config = ReportConfig(
                tipo=report_format,
                titulo=f"Relatório - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            self.status_var.set("📋 Gerando relatório...")
            
            # Generate report based on type
            if report_type == "products":
                result = self.report_generator.generate_products_report(config)
            elif report_type == "inventory":
                result = self.report_generator.generate_inventory_report(config)
            elif report_type == "low_stock":
                result = self.report_generator.generate_low_stock_report(config)
            elif report_type == "price_list":
                result = self.report_generator.generate_price_list(config)
            elif report_type == "categories":
                result = self.report_generator.generate_category_report(config)
            elif report_type == "reorder":
                result = self.report_generator.generate_reorder_report(config)
            else:
                raise ValueError("Tipo de relatório inválido")
            
            if result['success']:
                filename = result['filename']
                self.status_var.set(f"✅ Relatório gerado: {filename}")
                
                # Ask to open file
                if messagebox.askyesno("Relatório Gerado", f"Relatório salvo como {filename}\n\nDeseja abrir o arquivo?"):
                    output_path = os.path.join('output', filename)
                    os.startfile(output_path)  # Windows
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                self.status_var.set(f"❌ Erro ao gerar relatório: {error_msg}")
                messagebox.showerror("Erro", f"Erro ao gerar relatório: {error_msg}")
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar relatório: {e}")
    
    def generate_receipt(self, tipo):
        """Generate receipt (placeholder implementation)"""
        customer_name = self.customer_name_var.get().strip()
        
        if not customer_name:
            messagebox.showwarning("Aviso", "Por favor, informe o nome do cliente")
            return
        
        # Sample receipt for demonstration
        sample_items = [
            {
                'codigo': '001',
                'descricao': 'Produto de Exemplo',
                'quantidade': 1,
                'preco_unitario': 10.00,
                'peso': 1.0
            }
        ]
        
        try:
            receipt_data = self.receipt_generator.create_receipt(customer_name, sample_items)
            
            if receipt_data['success']:
                result = self.receipt_generator.generate_receipt_html(receipt_data['receipt'], tipo)
                
                if result['success']:
                    filename = result['filename']
                    self.status_var.set(f"✅ Talão gerado: {filename}")
                    
                    if messagebox.askyesno("Talão Gerado", f"Talão salvo como {filename}\n\nDeseja abrir o arquivo?"):
                        output_path = os.path.join('output', filename)
                        os.startfile(output_path)
                else:
                    messagebox.showerror("Erro", f"Erro ao gerar talão: {result.get('error')}")
            else:
                messagebox.showerror("Erro", f"Erro ao criar talão: {receipt_data.get('error')}")
                
        except Exception as e:
            logger.error(f"Error generating receipt: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar talão: {e}")
    
    def update_inventory_summary(self):
        """Update inventory summary display"""
        try:
            stock_report = self.inventory_manager.get_stock_report()
            
            # Clear text
            self.inventory_summary_text.delete(1.0, tk.END)
            
            # Add summary information
            summary_text = f"""📊 RESUMO DO ESTOQUE
{'-' * 50}

📦 Total de Produtos: {stock_report.get('total_products', 0)}
💰 Valor Total: R$ {stock_report.get('total_stock_value', 0):.2f}
🔴 Produtos em Falta: {stock_report.get('out_of_stock_count', 0)}
⚠️ Estoque Baixo: {stock_report.get('low_stock_count', 0)}

📂 RESUMO POR CATEGORIA:
{'-' * 30}
"""
            
            for categoria, data in stock_report.get('categories', {}).items():
                summary_text += f"{categoria}: {data['count']} produtos - R$ {data['total_value']:.2f}\n"
            
            self.inventory_summary_text.insert(1.0, summary_text)
            
        except Exception as e:
            logger.error(f"Error updating inventory summary: {e}")
            self.inventory_summary_text.delete(1.0, tk.END)
            self.inventory_summary_text.insert(1.0, f"Erro ao carregar dados do estoque: {e}")
    
    def show_low_stock(self):
        """Show low stock alerts"""
        try:
            alerts = self.inventory_manager.get_low_stock_alert()
            
            if not alerts:
                messagebox.showinfo("Estoque", "Nenhum produto com estoque baixo encontrado!")
                return
            
            # Create alert window
            alert_window = tk.Toplevel(self.root)
            alert_window.title("⚠️ Produtos com Estoque Baixo")
            alert_window.geometry("600x400")
            alert_window.grab_set()
            
            # Alert list
            text_widget = tk.Text(alert_window, wrap=tk.WORD)
            scrollbar = ttk.Scrollbar(alert_window, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            alert_text = "⚠️ PRODUTOS COM ESTOQUE BAIXO\n"
            alert_text += "=" * 50 + "\n\n"
            
            for alert in alerts:
                urgency_icon = "🔴" if alert['urgency'] == 'CRITICAL' else "🟡" if alert['urgency'] == 'HIGH' else "🟢"
                alert_text += f"{urgency_icon} {alert['codigo']} - {alert['descricao']}\n"
                alert_text += f"   Estoque: {alert['estoque_atual']} | Categoria: {alert['categoria'] or 'N/A'}\n\n"
            
            text_widget.insert(1.0, alert_text)
            text_widget.config(state=tk.DISABLED)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
        except Exception as e:
            logger.error(f"Error showing low stock: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar alertas de estoque: {e}")
    
    def export_inventory(self):
        """Export inventory to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Salvar Inventário",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                success = self.inventory_manager.export_inventory_csv(filename)
                
                if success:
                    messagebox.showinfo("Sucesso", f"Inventário exportado para {filename}")
                else:
                    messagebox.showerror("Erro", "Erro ao exportar inventário")
                    
        except Exception as e:
            logger.error(f"Error exporting inventory: {e}")
            messagebox.showerror("Erro", f"Erro ao exportar inventário: {e}")
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def run(self):
        """Start the application"""
        logger.info("Starting main application")
        
        # Handle window close
        def on_closing():
            self.sync_manager.stop_auto_sync()
            logger.info("Application closed")
            self.root.destroy()
        
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()