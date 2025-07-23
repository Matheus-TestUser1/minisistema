#!/usr/bin/env python3
"""
Sistema PDV - Madeireira Maria Luiza
Main application entry point
"""

import os
import sys
import logging

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui import MainWindow
from src.utils import setup_logger, get_default_logger

def main():
    """Main application entry point"""
    # Setup logging
    logger = setup_logger(
        name='pdv_system',
        log_level='INFO',
        log_dir='logs',
        console_output=True,
        file_output=True
    )
    
    logger.info("=" * 50)
    logger.info("Starting Sistema PDV - Madeireira Maria Luiza")
    logger.info("=" * 50)
    
    try:
        # Create and run main application
        app = MainWindow()
        app.run()
        
    except Exception as e:
        logger.critical(f"Critical error starting application: {e}", exc_info=True)
        import tkinter.messagebox as msgbox
        msgbox.showerror(
            "Erro Crítico", 
            f"Erro crítico ao iniciar o sistema:\n\n{e}\n\nVerifique os logs para mais detalhes."
        )
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

# Legacy support - keep the old class for backward compatibility with existing scripts
class SistemaPDV:
    """Legacy PDV system class for backward compatibility"""
    
    def __init__(self):
        import tkinter as tk
        from tkinter import ttk, messagebox, filedialog
        import sqlite3
        import subprocess
        import os
        import sys
        from datetime import datetime
        import threading
        import time

        self.root = tk.Tk()
        self.root.title("🌲 Sistema PDV - Madeireira Maria Luiza (Legacy)")
        self.root.geometry("900x700")
        
        # Variáveis
        self.conectado_sic = False
        self.modo_offline = True
        self.conn_sic = None
        self.dados_cache = {}
        
        # Configurações SIC (ajustar conforme sua instalação)
        self.servidor_sql = "localhost\\SQLEXPRESS"  # Seu servidor
        self.database_sic = "SIC"                    # Nome do banco SIC
        self.usuario_sql = "sa"                      # Usuário SQL
        self.senha_sql = ""                          # Senha SQL (em branco se Windows Auth)
        
        # Show deprecation warning
        messagebox.showwarning(
            "Sistema Legacy",
            "Você está usando a versão legacy do sistema.\n\n"
            "Para usar a nova versão, execute:\npython main.py\n\n"
            "A versão legacy será removida em versões futuras."
        )
        
        self.criar_interface()
        self.criar_banco_local()
        self.verificar_sic_periodicamente()
        
    def criar_interface(self):
        """Interface principal do sistema"""
        # Título
        titulo = tk.Label(
            self.root, 
            text="🌲 MADEIREIRA MARIA LUIZA - SISTEMA PDV",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        titulo.pack(fill=tk.X)
        
        # Status
        self.frame_status = ttk.LabelFrame(self.root, text="📊 Status Sistema")
        self.frame_status.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="🟡 Sistema iniciado - Verificando SIC...")
        self.label_status = ttk.Label(self.frame_status, textvariable=self.status_var)
        self.label_status.pack(padx=10, pady=5)
        
        # Controles SIC
        self.criar_controles_sic()
        
        # Área principal com abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Aba Produtos
        self.criar_aba_produtos()
        
        # Aba Relatórios
        self.criar_aba_relatorios()
        
        # Aba Templates
        self.criar_aba_templates()
        
        # Aba Configurações
        self.criar_aba_config()
        
    def criar_controles_sic(self):
        """Controles para gerenciar conexão SIC"""
        frame_sic = ttk.LabelFrame(self.root, text="🔌 Controles SIC")
        frame_sic.pack(fill=tk.X, padx=10, pady=5)
        
        # Indicadores
        self.label_sic_status = ttk.Label(
            frame_sic, 
            text="🔴 SIC: Verificando...",
            font=("Arial", 10, "bold")
        )
        self.label_sic_status.pack(side=tk.LEFT, padx=10)
        
        self.label_dados_status = ttk.Label(
            frame_sic,
            text="💾 Dados: Cache local"
        )
        self.label_dados_status.pack(side=tk.LEFT, padx=10)
        
        # Botões
        ttk.Button(
            frame_sic, 
            text="🔄 Sync Rápido", 
            command=self.tentar_sync_rapido
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            frame_sic, 
            text="💾 Forçar Offline", 
            command=self.forcar_modo_offline
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            frame_sic, 
            text="🔧 Testar Conexão", 
            command=self.testar_conexao_sic
        ).pack(side=tk.RIGHT, padx=5)
    
    def criar_aba_produtos(self):
        """Aba para gerenciar produtos"""
        frame_produtos = ttk.Frame(self.notebook)
        self.notebook.add(frame_produtos, text="📦 Produtos")
        
        # Barra de ferramentas
        toolbar = ttk.Frame(frame_produtos)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            toolbar, 
            text="🔍 Buscar Produto", 
            command=self.buscar_produto
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="📋 Listar Todos", 
            command=self.listar_produtos
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="📤 Exportar Excel", 
            command=self.exportar_produtos_excel
        ).pack(side=tk.LEFT, padx=5)
        
        # Campo busca
        ttk.Label(toolbar, text="Buscar:").pack(side=tk.LEFT, padx=(20,5))
        self.entry_busca = ttk.Entry(toolbar, width=30)
        self.entry_busca.pack(side=tk.LEFT, padx=5)
        self.entry_busca.bind('<Return>', lambda e: self.buscar_produto())
        
        # Lista produtos
        colunas = ("Código", "Descrição", "Preço", "Estoque")
        self.tree_produtos = ttk.Treeview(frame_produtos, columns=colunas, show="headings", height=15)
        
        for col in colunas:
            self.tree_produtos.heading(col, text=col)
            self.tree_produtos.column(col, width=150)
        
        # Scrollbar
        scroll_produtos = ttk.Scrollbar(frame_produtos, orient=tk.VERTICAL, command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scroll_produtos.set)
        
        self.tree_produtos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        scroll_produtos.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        
        # Carregar produtos iniciais
        self.listar_produtos()
    
    def criar_aba_relatorios(self):
        """Aba para relatórios"""
        frame_relatorios = ttk.Frame(self.notebook)
        self.notebook.add(frame_relatorios, text="📊 Relatórios")
        
        # Botões relatórios
        ttk.Button(
            frame_relatorios,
            text="📋 Gerar Talão de Balcão",
            command=self.gerar_talao_balcao,
            width=30
        ).pack(pady=10)
        
        ttk.Button(
            frame_relatorios,
            text="📊 Relatório de Produtos",
            command=self.gerar_relatorio_produtos,
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            frame_relatorios,
            text="💰 Análise de Preços",
            command=self.analise_precos,
            width=30
        ).pack(pady=5)
        
        ttk.Button(
            frame_relatorios,
            text="📈 Produtos em Falta",
            command=self.produtos_em_falta,
            width=30
        ).pack(pady=5)
        
        # Área de log
        ttk.Label(frame_relatorios, text="📝 Log de Operações:").pack(anchor=tk.W, padx=10, pady=(20,5))
        
        self.text_log = tk.Text(frame_relatorios, height=15, width=80)
        scroll_log = ttk.Scrollbar(frame_relatorios, orient=tk.VERTICAL, command=self.text_log.yview)
        self.text_log.configure(yscrollcommand=scroll_log.set)
        
        self.text_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10,0), pady=(0,10))
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,10), pady=(0,10))
    
    def criar_aba_templates(self):
        """Aba para templates LibreOffice"""
        frame_templates = ttk.Frame(self.notebook)
        self.notebook.add(frame_templates, text="📄 Templates")
        
        ttk.Label(
            frame_templates, 
            text="🎨 Templates LibreOffice",
            font=("Arial", 14, "bold")
        ).pack(pady=10)
        
        # Botões templates
        ttk.Button(
            frame_templates,
            text="📝 Criar Template Talão Cliente",
            command=self.criar_template_talao_cliente,
            width=35
        ).pack(pady=5)
        
        ttk.Button(
            frame_templates,
            text="📝 Criar Template Talão Loja",
            command=self.criar_template_talao_loja,
            width=35
        ).pack(pady=5)
        
        ttk.Button(
            frame_templates,
            text="📊 Criar Template Relatório",
            command=self.criar_template_relatorio,
            width=35
        ).pack(pady=5)
        
        ttk.Button(
            frame_templates,
            text="📂 Abrir Pasta Templates",
            command=self.abrir_pasta_templates,
            width=35
        ).pack(pady=20)
        
        # Instruções
        instrucoes = """
📋 INSTRUÇÕES TEMPLATES:

1. 🎨 Clique para criar template base
2. ✏️ LibreOffice abrirá automaticamente  
3. 🔧 Edite conforme sua necessidade
4. 💾 Salve como .ots (template Calc)
5. 🚀 Use nos relatórios do sistema

💡 DICA: Templates ficam em 'templates/' 
🔄 Modifique quando quiser!
        """
        
        label_instrucoes = tk.Label(
            frame_templates,
            text=instrucoes,
            justify=tk.LEFT,
            font=("Courier", 9),
            bg="#f8f9fa",
            padx=20,
            pady=20
        )
        label_instrucoes.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
    def criar_aba_config(self):
        """Aba para configurações"""
        frame_config = ttk.Frame(self.notebook)
        self.notebook.add(frame_config, text="⚙️ Configurações")
        
        # Configurações SIC
        group_sic = ttk.LabelFrame(frame_config, text="🔌 Configurações SIC")
        group_sic.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(group_sic, text="Servidor SQL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_servidor = ttk.Entry(group_sic, width=40)
        self.entry_servidor.insert(0, self.servidor_sql)
        self.entry_servidor.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Database:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_database = ttk.Entry(group_sic, width=40)
        self.entry_database.insert(0, self.database_sic)
        self.entry_database.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Usuário:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_usuario = ttk.Entry(group_sic, width=40)
        self.entry_usuario.insert(0, self.usuario_sql)
        self.entry_usuario.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Senha:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_senha = ttk.Entry(group_sic, width=40, show="*")
        self.entry_senha.insert(0, self.senha_sql)
        self.entry_senha.grid(row=3, column=1, padx=5, pady=2)
        
        ttk.Button(
            group_sic,
            text="💾 Salvar Configurações",
            command=self.salvar_configuracoes
        ).grid(row=4, column=1, padx=5, pady=10, sticky=tk.E)
        
        # Configurações Sistema
        group_sistema = ttk.LabelFrame(frame_config, text="⚙️ Configurações Sistema")
        group_sistema.pack(fill=tk.X, padx=10, pady=10)
        
        self.var_auto_sync = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            group_sistema,
            text="🔄 Sincronização automática",
            variable=self.var_auto_sync
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        self.var_backup_auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            group_sistema,
            text="💾 Backup automático",
            variable=self.var_backup_auto
        ).pack(anchor=tk.W, padx=10, pady=5)
        
        # Informações sistema
        group_info = ttk.LabelFrame(frame_config, text="ℹ️ Informações")
        group_info.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info_text = f"""
💻 Sistema: Windows 7 - Python 3.8
🐍 Versão Python: {sys.version.split()[0]}
📂 Diretório: {os.path.dirname(os.path.abspath(__file__))}
🕒 Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        """
        
        tk.Label(
            group_info,
            text=info_text,
            justify=tk.LEFT,
            font=("Courier", 9)
        ).pack(anchor=tk.W, padx=10, pady=10)

    def criar_banco_local(self):
        """Criar banco SQLite local"""
        try:
            os.makedirs("dados", exist_ok=True)
            
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            # Tabela produtos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    codigo TEXT PRIMARY KEY,
                    descricao TEXT,
                    preco_venda REAL,
                    preco_custo REAL,
                    estoque INTEGER,
                    categoria TEXT,
                    ativo INTEGER DEFAULT 1,
                    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tabela cache info
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_info (
                    tipo TEXT PRIMARY KEY,
                    ultimo_update TIMESTAMP,
                    total_registros INTEGER
                )
            ''')
            
            conn.commit()
            conn.close()
            
            self.log("✅ Banco local criado/verificado")
            
        except Exception as e:
            self.log(f"❌ Erro criar banco local: {e}")

    def verificar_sic_periodicamente(self):
        """Verificar status SIC em background"""
        def verificar():
            while True:
                try:
                    sic_livre = self.detectar_sic_livre()
                    
                    if sic_livre:
                        self.label_sic_status.config(
                            text="🟢 SIC: Livre (pode sincronizar)",
                            foreground="green"
                        )
                        
                        # Auto-sync se habilitado
                        if self.var_auto_sync.get() and not self.conectado_sic:
                            self.auto_sincronizar()
                    else:
                        self.label_sic_status.config(
                            text="🟡 SIC: Em uso (modo offline)",
                            foreground="orange"
                        )
                        
                except Exception as e:
                    self.label_sic_status.config(
                        text="🔴 SIC: Erro verificação",
                        foreground="red"
                    )
                
                time.sleep(30)  # Verificar a cada 30 segundos
        
        thread = threading.Thread(target=verificar, daemon=True)
        thread.start()

    def detectar_sic_livre(self):
        """Detectar se SIC está livre para conexão"""
        try:
            # Tentar conexão rápida
            import pyodbc
            
            conn_string = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.servidor_sql};"
                f"DATABASE={self.database_sic};"
                f"UID={self.usuario_sql};"
                f"PWD={self.senha_sql};"
                f"Timeout=2;"
            )
            
            conn = pyodbc.connect(conn_string)
            conn.close()
            return True
            
        except:
            return False

    def tentar_sync_rapido(self):
        """Tentar sincronização rápida"""
        if not self.detectar_sic_livre():
            messagebox.showwarning(
                "SIC Em Uso",
                "🟡 SIC está sendo usado!\n\n" +
                "💡 Feche o SIC e tente novamente\n" +
                "📊 Ou continue trabalhando offline"
            )
            return
        
        # SIC livre, sincronizar
        self.sincronizar_dados_sic()

    def sincronizar_dados_sic(self):
        """Sincronizar dados do SIC"""
        try:
            self.status_var.set("🔄 Conectando ao SIC...")
            self.root.update()
            
            # Conectar SIC
            if self.conectar_sic():
                self.status_var.set("📊 Sincronizando produtos...")
                self.root.update()
                
                # Buscar produtos
                produtos = self.buscar_produtos_sic()
                
                if produtos:
                    # Salvar no banco local
                    self.salvar_produtos_local(produtos)
                    
                    # Atualizar lista
                    self.listar_produtos()
                    
                    self.status_var.set(f"✅ Sincronizado! {len(produtos)} produtos")
                    self.log(f"✅ Sincronização concluída: {len(produtos)} produtos")
                else:
                    self.status_var.set("⚠️ Nenhum produto encontrado")
                
                # Desconectar
                self.desconectar_sic()
            else:
                self.status_var.set("❌ Erro na conexão SIC")
                
        except Exception as e:
            self.status_var.set(f"❌ Erro sincronização: {e}")
            self.log(f"❌ Erro sincronização: {e}")
            self.desconectar_sic()

    def conectar_sic(self):
        """Conectar ao banco SIC"""
        try:
            import pyodbc
            
            conn_string = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={self.servidor_sql};"
                f"DATABASE={self.database_sic};"
                f"UID={self.usuario_sql};"
                f"PWD={self.senha_sql};"
                f"Timeout=10;"
            )
            
            self.conn_sic = pyodbc.connect(conn_string)
            self.conectado_sic = True
            return True
            
        except Exception as e:
            self.log(f"❌ Erro conexão SIC: {e}")
            return False

    def desconectar_sic(self):
        """Desconectar do SIC"""
        try:
            if self.conn_sic:
                self.conn_sic.close()
                self.conn_sic = None
            self.conectado_sic = False
        except:
            pass

    def buscar_produtos_sic(self):
        """Buscar produtos do SIC"""
        try:
            cursor = self.conn_sic.cursor()
            
            # Query ajustar conforme estrutura do seu SIC
            query = """
                SELECT 
                    Codigo,
                    Descricao,
                    PrecoVenda,
                    PrecoCusto,
                    Estoque,
                    Categoria
                FROM Produto 
                WHERE Ativo = 1
                ORDER BY Descricao
            """
            
            cursor.execute(query)
            produtos = cursor.fetchall()
            
            return produtos
            
        except Exception as e:
            self.log(f"❌ Erro buscar produtos SIC: {e}")
            return []

    def salvar_produtos_local(self, produtos):
        """Salvar produtos no banco local"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            # Limpar produtos antigos
            cursor.execute("DELETE FROM produtos")
            
            # Inserir produtos
            for produto in produtos:
                cursor.execute("""
                    INSERT INTO produtos 
                    (codigo, descricao, preco_venda, preco_custo, estoque, categoria)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, produto)
            
            # Atualizar info cache
            cursor.execute("""
                INSERT OR REPLACE INTO cache_info 
                (tipo, ultimo_update, total_registros)
                VALUES ('produtos', CURRENT_TIMESTAMP, ?)
            """, (len(produtos),))
            
            conn.commit()
            conn.close()
            
            self.label_dados_status.config(
                text=f"💾 Cache: {len(produtos)} produtos ({datetime.now().strftime('%H:%M')})"
            )
            
        except Exception as e:
            self.log(f"❌ Erro salvar produtos local: {e}")

    def listar_produtos(self):
        """Listar produtos na treeview"""
        try:
            # Limpar lista atual
            for item in self.tree_produtos.get_children():
                self.tree_produtos.delete(item)
            
            # Buscar produtos do banco local
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT codigo, descricao, preco_venda, estoque
                FROM produtos 
                ORDER BY descricao
                LIMIT 1000
            """)
            
            produtos = cursor.fetchall()
            conn.close()
            
            # Inserir na treeview
            for produto in produtos:
                codigo, descricao, preco, estoque = produto
                self.tree_produtos.insert("", tk.END, values=(
                    codigo,
                    descricao[:50],  # Limitar descrição
                    f"R$ {preco:.2f}" if preco else "R$ 0,00",
                    estoque or 0
                ))
            
            self.log(f"📋 Listados {len(produtos)} produtos")
            
        except Exception as e:
            self.log(f"❌ Erro listar produtos: {e}")

    def buscar_produto(self):
        """Buscar produto específico"""
        termo = self.entry_busca.get().strip()
        if not termo:
            self.listar_produtos()
            return
        
        try:
            # Limpar lista
            for item in self.tree_produtos.get_children():
                self.tree_produtos.delete(item)
            
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT codigo, descricao, preco_venda, estoque
                FROM produtos 
                WHERE codigo LIKE ? OR descricao LIKE ?
                ORDER BY descricao
                LIMIT 100
            """, (f"%{termo}%", f"%{termo}%"))
            
            produtos = cursor.fetchall()
            conn.close()
            
            # Inserir resultados
            for produto in produtos:
                codigo, descricao, preco, estoque = produto
                self.tree_produtos.insert("", tk.END, values=(
                    codigo,
                    descricao[:50],
                    f"R$ {preco:.2f}" if preco else "R$ 0,00",
                    estoque or 0
                ))
            
            self.log(f"🔍 Encontrados {len(produtos)} produtos para '{termo}'")
            
        except Exception as e:
            self.log(f"❌ Erro buscar produto: {e}")

    def exportar_produtos_excel(self):
        """Exportar produtos para Excel"""
        try:
            # Verificar se tem pandas
            try:
                import pandas as pd
            except ImportError:
                messagebox.showerror(
                    "Pandas Necessário",
                    "❌ Pandas não instalado!\n\n" +
                    "💡 Execute: pip install pandas openpyxl"
                )
                return
            
            # Buscar produtos
            conn = sqlite3.connect("dados/produtos_sic.db")
            df = pd.read_sql_query("""
                SELECT 
                    codigo as 'Código',
                    descricao as 'Descrição',
                    preco_venda as 'Preço Venda',
                    preco_custo as 'Preço Custo',
                    estoque as 'Estoque',
                    categoria as 'Categoria'
                FROM produtos 
                ORDER BY descricao
            """, conn)
            conn.close()
            
            if df.empty:
                messagebox.showwarning("Sem Dados", "❌ Nenhum produto para exportar!")
                return
            
            # Escolher arquivo
            arquivo = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Salvar relatório como..."
            )
            
            if arquivo:
                # Salvar Excel
                df.to_excel(arquivo, index=False, sheet_name="Produtos")
                
                self.log(f"📊 Produtos exportados: {arquivo}")
                
                # Perguntar se quer abrir
                if messagebox.askyesno("Exportado!", f"✅ Arquivo salvo!\n\n📂 {arquivo}\n\nAbrir agora?"):
                    os.startfile(arquivo)
            
        except Exception as e:
            self.log(f"❌ Erro exportar Excel: {e}")
            messagebox.showerror("Erro", f"Erro ao exportar:\n{e}")

    def gerar_talao_balcao(self):
        """Gerar talão de balcão"""
        try:
            # Criar pasta relatórios
            os.makedirs("relatorios", exist_ok=True)
            
            # Nome arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = f"relatorios/talao_balcao_{timestamp}.txt"
            
            # Gerar conteúdo
            conteudo = f"""
{'='*60}
           MADEIREIRA MARIA LUIZA
        Rua das Madeiras, 456 - Sua Cidade - SP
            (11) 9999-8888 | CNPJ: XX.XXX.XXX/0001-XX
{'='*60}

              TALÃO DE BALCÃO - VIA CLIENTE

Nº: {timestamp[-6:]}        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Vendedor: ________________________________

Cliente: _____________________________________
CPF/CNPJ: ___________________________________

{'='*60}
Cód. | Descrição                    | Qtd | Preço  | Total
{'='*60}
     |                              |     |        |
     |                              |     |        |
     |                              |     |        |
     |                              |     |        |
     |                              |     |        |
     |                              |     |        |
{'='*60}

                              SUBTOTAL: R$ _______
                              DESCONTO: R$ _______
                                 TOTAL: R$ _______

Forma Pagamento: ____________________________

Observações:
_____________________________________________
_____________________________________________

{'='*60}
    Obrigado pela preferência! Volte sempre!
           MADEIREIRA MARIA LUIZA
{'='*60}
"""
            
            # Salvar arquivo
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            self.log(f"🖨️ Talão gerado: {arquivo}")
            
            # Abrir arquivo
            if messagebox.askyesno("Talão Gerado", f"✅ Talão criado!\n\n📄 {arquivo}\n\nAbrir para impressão?"):
                os.startfile(arquivo)
                
        except Exception as e:
            self.log(f"❌ Erro gerar talão: {e}")

    def gerar_relatorio_produtos(self):
        """Gerar relatório completo de produtos"""
        try:
            # Verificar pandas
            try:
                import pandas as pd
            except ImportError:
                # Gerar relatório simples sem pandas
                self.gerar_relatorio_simples()
                return
            
            conn = sqlite3.connect("dados/produtos_sic.db")
            df = pd.read_sql_query("""
                SELECT * FROM produtos ORDER BY descricao
            """, conn)
            conn.close()
            
            if df.empty:
                messagebox.showwarning("Sem Dados", "❌ Nenhum produto no cache!")
                return
            
            # Análises
            total_produtos = len(df)
            valor_estoque = (df['preco_venda'] * df['estoque']).sum()
            produtos_sem_estoque = len(df[df['estoque'] <= 0])
            
            # Arquivo relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo_excel = f"relatorios/relatorio_produtos_{timestamp}.xlsx"
            
            # Criar pasta
            os.makedirs("relatorios", exist_ok=True)
            
            # Salvar Excel com múltiplas abas
            with pd.ExcelWriter(arquivo_excel, engine='openpyxl') as writer:
                # Aba principal
                df.to_excel(writer, sheet_name='Produtos', index=False)
                
                # Aba resumo
                resumo = pd.DataFrame({
                    'Métrica': [
                        'Total de Produtos',
                        'Valor Total Estoque',
                        'Produtos sem Estoque',
                        'Preço Médio',
                        'Data Relatório'
                    ],
                    'Valor': [
                        total_produtos,
                        f"R$ {valor_estoque:.2f}",
                        produtos_sem_estoque,
                        f"R$ {df['preco_venda'].mean():.2f}",
                        datetime.now().strftime('%d/%m/%Y %H:%M')
                    ]
                })
                resumo.to_excel(writer, sheet_name='Resumo', index=False)
                
                # Top 20 mais caros
                top_caros = df.nlargest(20, 'preco_venda')[['codigo', 'descricao', 'preco_venda']]
                top_caros.to_excel(writer, sheet_name='Top Preços', index=False)
            
            self.log(f"📊 Relatório gerado: {arquivo_excel}")
            
            # Abrir arquivo
            if messagebox.askyesno("Relatório Gerado", f"✅ Relatório criado!\n\n📊 {arquivo_excel}\n\nAbrir agora?"):
                os.startfile(arquivo_excel)
                
        except Exception as e:
            self.log(f"❌ Erro gerar relatório: {e}")

    def gerar_relatorio_simples(self):
        """Gerar relatório simples sem pandas"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM produtos")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(preco_venda * estoque) FROM produtos")
            valor_estoque = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT COUNT(*) FROM produtos WHERE estoque <= 0")
            sem_estoque = cursor.fetchone()[0]
            
            conn.close()
            
            # Arquivo texto
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = f"relatorios/relatorio_simples_{timestamp}.txt"
            
            os.makedirs("relatorios", exist_ok=True)
            
            conteudo = f"""
RELATÓRIO DE PRODUTOS - {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'='*50}

Total de Produtos: {total}
Valor Total Estoque: R$ {valor_estoque:.2f}
Produtos sem Estoque: {sem_estoque}

{'='*50}
Relatório gerado pelo Sistema PDV
            """
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            self.log(f"📄 Relatório simples: {arquivo}")
            
            if messagebox.askyesno("Relatório Gerado", f"✅ Relatório criado!\n\n📄 {arquivo}\n\nAbrir agora?"):
                os.startfile(arquivo)
                
        except Exception as e:
            self.log(f"❌ Erro relatório simples: {e}")

    def analise_precos(self):
        """Análise de preços"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    AVG(preco_venda) as preco_medio,
                    MIN(preco_venda) as preco_min,
                    MAX(preco_venda) as preco_max,
                    COUNT(*) as total
                FROM produtos 
                WHERE preco_venda > 0
            """)
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado and resultado[3] > 0:
                preco_medio, preco_min, preco_max, total = resultado
                
                mensagem = f"""
📊 ANÁLISE DE PREÇOS

Total de produtos: {total}
Preço médio: R$ {preco_medio:.2f}
Menor preço: R$ {preco_min:.2f}
Maior preço: R$ {preco_max:.2f}
                """
                
                messagebox.showinfo("Análise de Preços", mensagem)
                self.log("📊 Análise de preços executada")
            else:
                messagebox.showwarning("Sem Dados", "❌ Nenhum produto com preço para análise!")
                
        except Exception as e:
            self.log(f"❌ Erro análise preços: {e}")

    def produtos_em_falta(self):
        """Listar produtos em falta"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT codigo, descricao, estoque
                FROM produtos 
                WHERE estoque <= 0
                ORDER BY descricao
                LIMIT 50
            """)
            
            produtos = cursor.fetchall()
            conn.close()
            
            if produtos:
                # Criar janela com lista
                janela = tk.Toplevel(self.root)
                janela.title("📈 Produtos em Falta")
                janela.geometry("600x400")
                
                # Lista
                colunas = ("Código", "Descrição", "Estoque")
                tree = ttk.Treeview(janela, columns=colunas, show="headings")
                
                for col in colunas:
                    tree.heading(col, text=col)
                
                for produto in produtos:
                    tree.insert("", tk.END, values=produto)
                
                tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Botão fechar
                ttk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=5)
                
                self.log(f"📈 {len(produtos)} produtos em falta listados")
            else:
                messagebox.showinfo("Parabéns!", "✅ Nenhum produto em falta!")
                
        except Exception as e:
            self.log(f"❌ Erro produtos em falta: {e}")

    def criar_template_talao_cliente(self):
        """Criar template talão cliente"""
        self.criar_template_base("talao_cliente", "Talão de Balcão - Cliente")

    def criar_template_talao_loja(self):
        """Criar template talão loja"""
        self.criar_template_base("talao_loja", "Talão de Balcão - Loja")

    def criar_template_relatorio(self):
        """Criar template relatório"""
        self.criar_template_base("relatorio", "Relatório de Produtos")

    def criar_template_base(self, tipo, titulo):
        """Criar template base LibreOffice"""
        try:
            # Criar pasta templates
            os.makedirs("templates", exist_ok=True)
            
            arquivo = f"templates/{tipo}_template.ods"
            
            # Verificar se LibreOffice está instalado
            calc_paths = [
                r"C:\Program Files\LibreOffice\program\scalc.exe",
                r"C:\Program Files (x86)\LibreOffice\program\scalc.exe",
                r"C:\LibreOffice\program\scalc.exe"
            ]
            
            calc_exe = None
            for path in calc_paths:
                if os.path.exists(path):
                    calc_exe = path
                    break
            
            if not calc_exe:
                messagebox.showerror(
                    "LibreOffice Não Encontrado",
                    "❌ LibreOffice não encontrado!\n\n" +
                    "💡 Instale o LibreOffice primeiro:\n" +
                    "https://www.libreoffice.org/download/"
                )
                return
            
            # Criar arquivo template básico se não existir
            if not os.path.exists(arquivo):
                # Criar conteúdo básico
                conteudo_template = self.gerar_conteudo_template(tipo, titulo)
                
                # Escrever arquivo temporário CSV para converter
                arquivo_temp = f"templates/{tipo}_temp.csv"
                with open(arquivo_temp, 'w', encoding='utf-8') as f:
                    f.write(conteudo_template)
                
                self.log(f"📄 Template base criado: {arquivo}")
            
            # Abrir LibreOffice
            subprocess.Popen([calc_exe, arquivo_temp if 'arquivo_temp' in locals() else arquivo])
            
            messagebox.showinfo(
                "Template Aberto",
                f"🎨 {titulo} aberto no LibreOffice!\n\n" +
                f"✏️ Edite conforme necessário\n" +
                f"💾 Salve como template (.ots)\n" +
                f"📂 Local: {arquivo}"
            )
            
        except Exception as e:
            self.log(f"❌ Erro criar template: {e}")
            messagebox.showerror("Erro", f"Erro ao criar template:\n{e}")

    def gerar_conteudo_template(self, tipo, titulo):
        """Gerar conteúdo base para template"""
        if tipo == "talao_cliente":
            return """EMPRESA,MADEIREIRA MARIA LUIZA 
ENDEREÇO,Rua do Comércio 123 - Sua Cidade - SP
TELEFONE,(11) 1234-5678
CNPJ,XX.XXX.XXX/0001-XX

DOCUMENTO,TALÃO DE BALCÃO - VIA CLIENTE
NÚMERO,
DATA,
VENDEDOR,

CLIENTE,
CPF/CNPJ,

CÓDIGO,DESCRIÇÃO,QTD,PREÇO,TOTAL
            """
        elif tipo == "talao_loja":
            return """EMPRESA,MADEIREIRA MARIA LUIZA 
ENDEREÇO,Rua do Comércio 123 - Sua Cidade - SP
TELEFONE,(11) 1234-5678
CNPJ,XX.XXX.XXX/0001-XX

DOCUMENTO,TALÃO DE BALCÃO - VIA LOJA
NÚMERO,
DATA,
VENDEDOR,

CLIENTE,
CPF/CNPJ,

CÓDIGO,DESCRIÇÃO,QTD,PREÇO,TOTAL
            """
        else:  # relatório
            return """EMPRESA,MADEIREIRA MARIA LUIZA 
RELATÓRIO,PRODUTOS EM ESTOQUE
DATA,
TOTAL PRODUTOS,
VALOR ESTOQUE,

CÓDIGO,DESCRIÇÃO,PREÇO,ESTOQUE,TOTAL
            """

    def abrir_pasta_templates(self):
        """Abrir pasta templates no Windows Explorer"""
        try:
            pasta = os.path.abspath("templates")
            os.makedirs(pasta, exist_ok=True)
            os.startfile(pasta)
            self.log("📂 Pasta templates aberta")
        except Exception as e:
            self.log(f"❌ Erro abrir pasta: {e}")

    def testar_conexao_sic(self):
        """Testar conexão com SIC"""
        try:
            self.status_var.set("🔧 Testando conexão SIC...")
            self.root.update()
            
            if self.conectar_sic():
                # Testar query simples
                cursor = self.conn_sic.cursor()
                cursor.execute("SELECT COUNT(*) FROM Produto")
                total = cursor.fetchone()[0]
                
                self.desconectar_sic()
                
                messagebox.showinfo(
                    "Conexão OK",
                    f"✅ Conexão com SIC funcionando!\n\n" +
                    f"📊 {total} produtos encontrados\n" +
                    f"🔌 Servidor: {self.servidor_sql}\n" +
                    f"💾 Database: {self.database_sic}"
                )
                
                self.status_var.set("✅ Teste de conexão: OK")
                self.log("✅ Teste conexão SIC: OK")
            else:
                messagebox.showerror(
                    "Conexão Falhou",
                    "❌ Não foi possível conectar ao SIC!\n\n" +
                    "🔧 Verifique:\n" +
                    "• SIC está fechado?\n" +
                    "• Configurações de servidor\n" +
                    "• Usuário e senha\n" +
                    "• SQL Server rodando?"
                )
                self.status_var.set("❌ Teste de conexão: FALHOU")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no teste:\n{e}")
            self.status_var.set("❌ Erro no teste de conexão")
            self.log(f"❌ Erro teste conexão: {e}")

    def forcar_modo_offline(self):
        """Forçar modo offline"""
        self.desconectar_sic()
        self.modo_offline = True
        self.label_sic_status.config(
            text="💾 MODO OFFLINE FORÇADO",
            foreground="blue"
        )
        self.status_var.set("💾 Modo offline ativado - trabalhando com cache")
        self.log("💾 Modo offline ativado")
        messagebox.showinfo(
            "Modo Offline",
            "💾 Sistema em modo offline!\n\n" +
            "✅ Trabalhando com dados em cache\n" +
            "🚀 SIC liberado para uso normal"
        )

    def auto_sincronizar(self):
        """Sincronização automática (se habilitada)"""
        try:
            if not self.var_auto_sync.get():
                return
            
            # Verificar se última sync foi há mais de 1 hora
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ultimo_update FROM cache_info 
                WHERE tipo = 'produtos'
            """)
            
            resultado = cursor.fetchone()
            conn.close()
            
            if resultado:
                ultimo_update = datetime.fromisoformat(resultado[0])
                agora = datetime.now()
                diferenca = (agora - ultimo_update).total_seconds() / 3600
                
                if diferenca < 1:  # Menos de 1 hora
                    return
            
            # Sincronizar em background
            def sync_background():
                try:
                    self.sincronizar_dados_sic()
                except:
                    pass
            
            thread = threading.Thread(target=sync_background, daemon=True)
            thread.start()
            
        except:
            pass

    def salvar_configuracoes(self):
        """Salvar configurações"""
        try:
            self.servidor_sql = self.entry_servidor.get()
            self.database_sic = self.entry_database.get()
            self.usuario_sql = self.entry_usuario.get()
            self.senha_sql = self.entry_senha.get()
            
            # Salvar em arquivo
            config = {
                'servidor': self.servidor_sql,
                'database': self.database_sic,
                'usuario': self.usuario_sql,
                'senha': self.senha_sql
            }
            
            import json
            with open('dados/config.json', 'w') as f:
                json.dump(config, f)
            
            messagebox.showinfo("Configurações", "✅ Configurações salvas!")
            self.log("⚙️ Configurações salvas")
            
        except Exception as e:
            self.log(f"❌ Erro salvar config: {e}")

    def log(self, mensagem):
        """Adicionar mensagem ao log"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_msg = f"[{timestamp}] {mensagem}\n"
            
            self.text_log.insert(tk.END, log_msg)
            self.text_log.see(tk.END)
            
            # Manter apenas últimas 100 linhas
            linhas = self.text_log.get("1.0", tk.END).split('\n')
            if len(linhas) > 100:
                self.text_log.delete("1.0", f"{len(linhas)-100}.0")
                
        except:
            pass

    def run(self):
        """Executar aplicação"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.desconectar_sic()
            self.root.quit()

# Executar sistema
if __name__ == "__main__":
    app = SistemaPDV()
    app.run()