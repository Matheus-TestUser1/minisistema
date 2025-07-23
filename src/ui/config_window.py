"""
Configuration Window Module
Provides interface for system configuration
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigWindow:
    """Configuration management window"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.window = None
        self.config_vars = {}
    
    def show(self):
        """Show configuration window"""
        if self.window is not None:
            self.window.focus_set()
            return
        
        self.window = tk.Toplevel(self.parent)
        self.window.title("⚙️ Configurações do Sistema")
        self.window.geometry("700x600")
        self.window.grab_set()
        
        # Center window
        self.window.transient(self.parent)
        
        self.create_interface()
        self.load_current_config()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_interface(self):
        """Create configuration interface"""
        # Title
        title_label = tk.Label(
            self.window,
            text="⚙️ Configurações do Sistema",
            font=("Arial", 14, "bold"),
            pady=10
        )
        title_label.pack()
        
        # Notebook for different config sections
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Database configuration
        self.create_database_tab(notebook)
        
        # Business information
        self.create_business_tab(notebook)
        
        # System settings
        self.create_system_tab(notebook)
        
        # UI settings
        self.create_ui_tab(notebook)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            buttons_frame,
            text="💾 Salvar",
            command=self.save_config
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="❌ Cancelar",
            command=self.on_close
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🔄 Restaurar Padrões",
            command=self.restore_defaults
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            buttons_frame,
            text="🧪 Testar Conexão",
            command=self.test_connection
        ).pack(side=tk.LEFT, padx=5)
    
    def create_database_tab(self, notebook):
        """Create database configuration tab"""
        db_frame = ttk.Frame(notebook)
        notebook.add(db_frame, text="💾 Banco de Dados")
        
        # SIC Configuration
        sic_frame = ttk.LabelFrame(db_frame, text="🔌 Configuração SIC (SQL Server)")
        sic_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Server
        ttk.Label(sic_frame, text="Servidor:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_servidor'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_servidor'], width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Database
        ttk.Label(sic_frame, text="Banco:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_banco'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_banco'], width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # User
        ttk.Label(sic_frame, text="Usuário:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_usuario'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_usuario'], width=40).grid(row=2, column=1, padx=5, pady=5)
        
        # Password
        ttk.Label(sic_frame, text="Senha:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_senha'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_senha'], width=40, show="*").grid(row=3, column=1, padx=5, pady=5)
        
        # Port
        ttk.Label(sic_frame, text="Porta:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_porta'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_porta'], width=40).grid(row=4, column=1, padx=5, pady=5)
        
        # Timeout
        ttk.Label(sic_frame, text="Timeout (s):").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sic_timeout'] = tk.StringVar()
        ttk.Entry(sic_frame, textvariable=self.config_vars['sic_timeout'], width=40).grid(row=5, column=1, padx=5, pady=5)
        
        # Local Database Configuration
        local_frame = ttk.LabelFrame(db_frame, text="📱 Configuração Local (SQLite)")
        local_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Database path
        ttk.Label(local_frame, text="Caminho do Banco:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['local_database_path'] = tk.StringVar()
        ttk.Entry(local_frame, textvariable=self.config_vars['local_database_path'], width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Backup settings
        self.config_vars['local_backup_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(
            local_frame,
            text="Habilitar backup automático",
            variable=self.config_vars['local_backup_enabled']
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def create_business_tab(self, notebook):
        """Create business information tab"""
        business_frame = ttk.Frame(notebook)
        notebook.add(business_frame, text="🏢 Empresa")
        
        # Business info frame
        info_frame = ttk.LabelFrame(business_frame, text="📋 Informações da Empresa")
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Company name
        ttk.Label(info_frame, text="Nome da Empresa:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_nome_empresa'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_nome_empresa'], width=50).grid(row=0, column=1, padx=5, pady=5)
        
        # Address
        ttk.Label(info_frame, text="Endereço:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_endereco'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_endereco'], width=50).grid(row=1, column=1, padx=5, pady=5)
        
        # City
        ttk.Label(info_frame, text="Cidade:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_cidade'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_cidade'], width=50).grid(row=2, column=1, padx=5, pady=5)
        
        # Phone
        ttk.Label(info_frame, text="Telefone:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_telefone'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_telefone'], width=50).grid(row=3, column=1, padx=5, pady=5)
        
        # CNPJ
        ttk.Label(info_frame, text="CNPJ:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_cnpj'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_cnpj'], width=50).grid(row=4, column=1, padx=5, pady=5)
        
        # Email
        ttk.Label(info_frame, text="Email:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['business_email'] = tk.StringVar()
        ttk.Entry(info_frame, textvariable=self.config_vars['business_email'], width=50).grid(row=5, column=1, padx=5, pady=5)
        
        # Freight settings
        frete_frame = ttk.LabelFrame(business_frame, text="🚚 Configurações de Frete")
        frete_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Price per kg
        ttk.Label(frete_frame, text="Valor por kg (R$):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['frete_valor_por_kg'] = tk.StringVar()
        ttk.Entry(frete_frame, textvariable=self.config_vars['frete_valor_por_kg'], width=20).grid(row=0, column=1, padx=5, pady=5)
        
        # Minimum freight
        ttk.Label(frete_frame, text="Frete mínimo (R$):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['frete_frete_minimo'] = tk.StringVar()
        ttk.Entry(frete_frame, textvariable=self.config_vars['frete_frete_minimo'], width=20).grid(row=1, column=1, padx=5, pady=5)
        
        # Auto calculation
        self.config_vars['frete_calculo_automatico'] = tk.BooleanVar()
        ttk.Checkbutton(
            frete_frame,
            text="Cálculo automático de frete",
            variable=self.config_vars['frete_calculo_automatico']
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
    
    def create_system_tab(self, notebook):
        """Create system settings tab"""
        system_frame = ttk.Frame(notebook)
        notebook.add(system_frame, text="⚙️ Sistema")
        
        # App settings
        app_frame = ttk.LabelFrame(system_frame, text="📱 Configurações da Aplicação")
        app_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Debug mode
        self.config_vars['app_debug'] = tk.BooleanVar()
        ttk.Checkbutton(
            app_frame,
            text="Modo debug",
            variable=self.config_vars['app_debug']
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Log level
        ttk.Label(app_frame, text="Nível de log:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['app_log_level'] = tk.StringVar()
        log_combo = ttk.Combobox(
            app_frame,
            textvariable=self.config_vars['app_log_level'],
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=20
        )
        log_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Sync settings
        sync_frame = ttk.LabelFrame(system_frame, text="🔄 Configurações de Sincronização")
        sync_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Auto sync
        self.config_vars['sync_auto_sync_enabled'] = tk.BooleanVar()
        ttk.Checkbutton(
            sync_frame,
            text="Sincronização automática",
            variable=self.config_vars['sync_auto_sync_enabled']
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Sync interval
        ttk.Label(sync_frame, text="Intervalo (minutos):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sync_sync_interval_minutes'] = tk.StringVar()
        ttk.Entry(sync_frame, textvariable=self.config_vars['sync_sync_interval_minutes'], width=20).grid(row=1, column=1, padx=5, pady=5)
        
        # Max retry attempts
        ttk.Label(sync_frame, text="Tentativas máximas:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sync_max_retry_attempts'] = tk.StringVar()
        ttk.Entry(sync_frame, textvariable=self.config_vars['sync_max_retry_attempts'], width=20).grid(row=2, column=1, padx=5, pady=5)
        
        # Timeout
        ttk.Label(sync_frame, text="Timeout (segundos):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['sync_timeout_seconds'] = tk.StringVar()
        ttk.Entry(sync_frame, textvariable=self.config_vars['sync_timeout_seconds'], width=20).grid(row=3, column=1, padx=5, pady=5)
    
    def create_ui_tab(self, notebook):
        """Create UI settings tab"""
        ui_frame = ttk.Frame(notebook)
        notebook.add(ui_frame, text="🎨 Interface")
        
        # Window settings
        window_frame = ttk.LabelFrame(ui_frame, text="🪟 Configurações da Janela")
        window_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Window size
        ttk.Label(window_frame, text="Largura:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['window_width'] = tk.StringVar()
        ttk.Entry(window_frame, textvariable=self.config_vars['window_width'], width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(window_frame, text="Altura:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['window_height'] = tk.StringVar()
        ttk.Entry(window_frame, textvariable=self.config_vars['window_height'], width=20).grid(row=1, column=1, padx=5, pady=5)
        
        # Resizable
        self.config_vars['window_resizable'] = tk.BooleanVar()
        ttk.Checkbutton(
            window_frame,
            text="Janela redimensionável",
            variable=self.config_vars['window_resizable']
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Center on screen
        self.config_vars['window_center_on_screen'] = tk.BooleanVar()
        ttk.Checkbutton(
            window_frame,
            text="Centralizar na tela",
            variable=self.config_vars['window_center_on_screen']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Grid settings
        grid_frame = ttk.LabelFrame(ui_frame, text="📋 Configurações da Grade")
        grid_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Rows per page
        ttk.Label(grid_frame, text="Linhas por página:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['grid_rows_per_page'] = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.config_vars['grid_rows_per_page'], width=20).grid(row=0, column=1, padx=5, pady=5)
        
        # Auto refresh
        self.config_vars['grid_auto_refresh'] = tk.BooleanVar()
        ttk.Checkbutton(
            grid_frame,
            text="Atualização automática",
            variable=self.config_vars['grid_auto_refresh']
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Refresh interval
        ttk.Label(grid_frame, text="Intervalo de atualização (s):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.config_vars['grid_refresh_interval'] = tk.StringVar()
        ttk.Entry(grid_frame, textvariable=self.config_vars['grid_refresh_interval'], width=20).grid(row=2, column=1, padx=5, pady=5)
    
    def load_current_config(self):
        """Load current configuration values"""
        try:
            # Database config
            db_config = self.config_manager.get_config('database')
            sic_config = db_config.get('sic', {})
            local_config = db_config.get('local', {})
            
            self.config_vars['sic_servidor'].set(sic_config.get('servidor', ''))
            self.config_vars['sic_banco'].set(sic_config.get('banco', ''))
            self.config_vars['sic_usuario'].set(sic_config.get('usuario', ''))
            self.config_vars['sic_senha'].set(sic_config.get('senha', ''))
            self.config_vars['sic_porta'].set(str(sic_config.get('porta', 1433)))
            self.config_vars['sic_timeout'].set(str(sic_config.get('timeout', 30)))
            
            self.config_vars['local_database_path'].set(local_config.get('database_path', ''))
            self.config_vars['local_backup_enabled'].set(local_config.get('backup_enabled', True))
            
            # App config
            app_config = self.config_manager.get_config('app_config')
            business_config = app_config.get('business', {})
            frete_config = app_config.get('frete', {})
            sync_config = app_config.get('sync', {})
            app_info = app_config.get('app', {})
            
            self.config_vars['business_nome_empresa'].set(business_config.get('nome_empresa', ''))
            self.config_vars['business_endereco'].set(business_config.get('endereco', ''))
            self.config_vars['business_cidade'].set(business_config.get('cidade', ''))
            self.config_vars['business_telefone'].set(business_config.get('telefone', ''))
            self.config_vars['business_cnpj'].set(business_config.get('cnpj', ''))
            self.config_vars['business_email'].set(business_config.get('email', ''))
            
            self.config_vars['frete_valor_por_kg'].set(str(frete_config.get('valor_por_kg', 3.50)))
            self.config_vars['frete_frete_minimo'].set(str(frete_config.get('frete_minimo', 15.00)))
            self.config_vars['frete_calculo_automatico'].set(frete_config.get('calculo_automatico', True))
            
            self.config_vars['app_debug'].set(app_info.get('debug', False))
            self.config_vars['app_log_level'].set(app_info.get('log_level', 'INFO'))
            
            self.config_vars['sync_auto_sync_enabled'].set(sync_config.get('auto_sync_enabled', True))
            self.config_vars['sync_sync_interval_minutes'].set(str(sync_config.get('sync_interval_minutes', 5)))
            self.config_vars['sync_max_retry_attempts'].set(str(sync_config.get('max_retry_attempts', 3)))
            self.config_vars['sync_timeout_seconds'].set(str(sync_config.get('timeout_seconds', 30)))
            
            # UI config
            ui_config = self.config_manager.get_config('ui_config')
            window_config = ui_config.get('window', {})
            grid_config = ui_config.get('grid', {})
            
            self.config_vars['window_width'].set(str(window_config.get('width', 1200)))
            self.config_vars['window_height'].set(str(window_config.get('height', 800)))
            self.config_vars['window_resizable'].set(window_config.get('resizable', True))
            self.config_vars['window_center_on_screen'].set(window_config.get('center_on_screen', True))
            
            self.config_vars['grid_rows_per_page'].set(str(grid_config.get('rows_per_page', 50)))
            self.config_vars['grid_auto_refresh'].set(grid_config.get('auto_refresh', True))
            self.config_vars['grid_refresh_interval'].set(str(grid_config.get('refresh_interval', 30)))
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar configurações: {e}")
    
    def save_config(self):
        """Save configuration changes"""
        try:
            # Save database config
            sic_config = {
                'servidor': self.config_vars['sic_servidor'].get(),
                'banco': self.config_vars['sic_banco'].get(),
                'usuario': self.config_vars['sic_usuario'].get(),
                'senha': self.config_vars['sic_senha'].get(),
                'porta': int(self.config_vars['sic_porta'].get() or 1433),
                'timeout': int(self.config_vars['sic_timeout'].get() or 30),
                'driver': 'ODBC Driver 17 for SQL Server'
            }
            
            local_config = {
                'database_path': self.config_vars['local_database_path'].get(),
                'backup_enabled': self.config_vars['local_backup_enabled'].get(),
                'backup_interval_hours': 24,
                'max_backups': 7
            }
            
            self.config_manager.update_config_section('database', 'sic', sic_config)
            self.config_manager.update_config_section('database', 'local', local_config)
            
            # Save business config
            business_config = {
                'nome_empresa': self.config_vars['business_nome_empresa'].get(),
                'endereco': self.config_vars['business_endereco'].get(),
                'cidade': self.config_vars['business_cidade'].get(),
                'telefone': self.config_vars['business_telefone'].get(),
                'cnpj': self.config_vars['business_cnpj'].get(),
                'email': self.config_vars['business_email'].get()
            }
            
            frete_config = {
                'valor_por_kg': float(self.config_vars['frete_valor_por_kg'].get() or 3.50),
                'frete_minimo': float(self.config_vars['frete_frete_minimo'].get() or 15.00),
                'calculo_automatico': self.config_vars['frete_calculo_automatico'].get()
            }
            
            app_config = {
                'name': 'Sistema PDV - Madeireira Maria Luiza',
                'version': '1.0.0',
                'debug': self.config_vars['app_debug'].get(),
                'log_level': self.config_vars['app_log_level'].get()
            }
            
            sync_config = {
                'auto_sync_enabled': self.config_vars['sync_auto_sync_enabled'].get(),
                'sync_interval_minutes': int(self.config_vars['sync_sync_interval_minutes'].get() or 5),
                'max_retry_attempts': int(self.config_vars['sync_max_retry_attempts'].get() or 3),
                'timeout_seconds': int(self.config_vars['sync_timeout_seconds'].get() or 30)
            }
            
            self.config_manager.update_config_section('app_config', 'business', business_config)
            self.config_manager.update_config_section('app_config', 'frete', frete_config)
            self.config_manager.update_config_section('app_config', 'app', app_config)
            self.config_manager.update_config_section('app_config', 'sync', sync_config)
            
            # Save UI config
            window_config = {
                'width': int(self.config_vars['window_width'].get() or 1200),
                'height': int(self.config_vars['window_height'].get() or 800),
                'resizable': self.config_vars['window_resizable'].get(),
                'center_on_screen': self.config_vars['window_center_on_screen'].get()
            }
            
            grid_config = {
                'rows_per_page': int(self.config_vars['grid_rows_per_page'].get() or 50),
                'auto_refresh': self.config_vars['grid_auto_refresh'].get(),
                'refresh_interval': int(self.config_vars['grid_refresh_interval'].get() or 30)
            }
            
            self.config_manager.update_config_section('ui_config', 'window', window_config)
            self.config_manager.update_config_section('ui_config', 'grid', grid_config)
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!\n\nReinicie o sistema para aplicar todas as alterações.")
            self.on_close()
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            messagebox.showerror("Erro", f"Erro ao salvar configurações: {e}")
    
    def test_connection(self):
        """Test database connection"""
        try:
            # Create temporary SIC connection for testing
            from ..database import SICConnection
            
            # Update connection with current form values
            test_connection = SICConnection()
            test_connection.connection_string = None  # Force rebuild
            
            success, message = test_connection.test_connection()
            
            if success:
                messagebox.showinfo("Teste de Conexão", "✅ Conexão com SIC realizada com sucesso!")
            else:
                messagebox.showwarning("Teste de Conexão", f"❌ Falha na conexão:\n{message}")
                
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            messagebox.showerror("Erro", f"Erro ao testar conexão: {e}")
    
    def restore_defaults(self):
        """Restore default configuration"""
        if messagebox.askyesno("Restaurar Padrões", "Deseja restaurar todas as configurações para os valores padrão?\n\nEsta ação não pode ser desfeita."):
            try:
                # Recreate default configs
                self.config_manager.create_default_configs()
                
                # Reload interface
                self.load_current_config()
                
                messagebox.showinfo("Sucesso", "Configurações padrão restauradas com sucesso!")
                
            except Exception as e:
                logger.error(f"Error restoring defaults: {e}")
                messagebox.showerror("Erro", f"Erro ao restaurar padrões: {e}")
    
    def on_close(self):
        """Handle window close"""
        self.window.destroy()
        self.window = None