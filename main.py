import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import subprocess
import os
import sys
import re
from datetime import datetime
import threading
import time

# Import our enhanced modules
from src.security.config_manager import SecureConfigManager
from src.validation.product_validator import ProductValidator

class SistemaPDV:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🌲 Sistema PDV - Madeireira Maria Luiza")
        self.root.geometry("900x700")
        
        # Variáveis
        self.conectado_sic = False
        self.modo_offline = True
        self.conn_sic = None
        self.dados_cache = {}
        
        # Initialize security and validation
        self.config_manager = SecureConfigManager()
        self.product_validator = ProductValidator()
        
        # Session management
        self.session_start_time = None
        self.session_timeout_minutes = self.config_manager.get_session_timeout()
        
        self.criar_interface()
        self.criar_banco_local()
        self.verificar_sic_periodicamente()
        self.inicializar_sistema_backup()
        
        # Fazer backup inicial se habilitado
        if self.var_backup_auto.get():
            try:
                self.fazer_backup()
            except:
                pass
        
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
        
        # Aba PDV
        self.criar_aba_pdv()
        
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
            text="➕ Novo Produto", 
            command=self.novo_produto
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="✏️ Editar", 
            command=self.editar_produto
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="🗑️ Excluir", 
            command=self.excluir_produto
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
        colunas = ("Código", "Descrição", "Preço Venda", "Preço Custo", "Estoque", "Categoria", "Status")
        self.tree_produtos = ttk.Treeview(frame_produtos, columns=colunas, show="headings", height=15)
        
        # Configure column widths
        column_widths = {"Código": 100, "Descrição": 250, "Preço Venda": 100, "Preço Custo": 100, "Estoque": 80, "Categoria": 120, "Status": 80}
        for col in colunas:
            self.tree_produtos.heading(col, text=col)
            self.tree_produtos.column(col, width=column_widths.get(col, 100))
        
        # Enable selection
        self.tree_produtos.bind('<Double-1>', lambda e: self.editar_produto())
        
        # Scrollbar
        scroll_produtos = ttk.Scrollbar(frame_produtos, orient=tk.VERTICAL, command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scroll_produtos.set)
        
        self.tree_produtos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=5)
        scroll_produtos.pack(side=tk.RIGHT, fill=tk.Y, padx=(0,5), pady=5)
        
        # Carregar produtos iniciais
        self.listar_produtos()
    
    def criar_aba_pdv(self):
        """Aba para PDV - Ponto de Venda"""
        frame_pdv = ttk.Frame(self.notebook)
        self.notebook.add(frame_pdv, text="🛒 PDV")
        
        # Frame principal dividido
        paned = ttk.PanedWindow(frame_pdv, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Lado esquerdo - Busca e seleção de produtos
        frame_esquerdo = ttk.LabelFrame(paned, text="🔍 Buscar Produtos")
        paned.add(frame_esquerdo, weight=1)
        
        # Busca produtos PDV
        frame_busca_pdv = ttk.Frame(frame_esquerdo)
        frame_busca_pdv.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_busca_pdv, text="Código/Descrição:").pack(side=tk.LEFT)
        self.entry_busca_pdv = ttk.Entry(frame_busca_pdv, width=30)
        self.entry_busca_pdv.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.entry_busca_pdv.bind('<Return>', lambda e: self.buscar_produto_pdv())
        
        ttk.Button(frame_busca_pdv, text="🔍", command=self.buscar_produto_pdv).pack(side=tk.RIGHT)
        
        # Lista produtos PDV
        colunas_pdv = ("Código", "Descrição", "Preço", "Estoque")
        self.tree_produtos_pdv = ttk.Treeview(frame_esquerdo, columns=colunas_pdv, show="headings", height=10)
        
        for col in colunas_pdv:
            self.tree_produtos_pdv.heading(col, text=col)
            self.tree_produtos_pdv.column(col, width=120)
        
        self.tree_produtos_pdv.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_produtos_pdv.bind('<Double-1>', lambda e: self.adicionar_ao_carrinho())
        
        # Botão adicionar
        ttk.Button(frame_esquerdo, text="➕ Adicionar ao Carrinho", 
                  command=self.adicionar_ao_carrinho).pack(pady=5)
        
        # Lado direito - Carrinho e totais
        frame_direito = ttk.LabelFrame(paned, text="🛒 Carrinho de Compras")
        paned.add(frame_direito, weight=1)
        
        # Carrinho
        colunas_carrinho = ("Código", "Descrição", "Qtd", "Preço", "Total")
        self.tree_carrinho = ttk.Treeview(frame_direito, columns=colunas_carrinho, show="headings", height=8)
        
        for col in colunas_carrinho:
            self.tree_carrinho.heading(col, text=col)
            self.tree_carrinho.column(col, width=100)
        
        self.tree_carrinho.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree_carrinho.bind('<Delete>', lambda e: self.remover_do_carrinho())
        
        # Botões carrinho
        frame_btn_carrinho = ttk.Frame(frame_direito)
        frame_btn_carrinho.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(frame_btn_carrinho, text="🗑️ Remover Item", 
                  command=self.remover_do_carrinho).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_btn_carrinho, text="🗑️ Limpar Carrinho", 
                  command=self.limpar_carrinho).pack(side=tk.LEFT, padx=2)
        
        # Totais
        frame_totais = ttk.LabelFrame(frame_direito, text="💰 Totais")
        frame_totais.pack(fill=tk.X, padx=5, pady=5)
        
        self.label_subtotal = ttk.Label(frame_totais, text="Subtotal: R$ 0,00", font=("Arial", 10, "bold"))
        self.label_subtotal.pack(anchor=tk.W, padx=10, pady=2)
        
        self.label_total = ttk.Label(frame_totais, text="TOTAL: R$ 0,00", font=("Arial", 12, "bold"))
        self.label_total.pack(anchor=tk.W, padx=10, pady=2)
        
        # Área cliente
        frame_cliente = ttk.LabelFrame(frame_direito, text="👤 Cliente")
        frame_cliente.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(frame_cliente, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_cliente_nome = ttk.Entry(frame_cliente, width=30)
        self.entry_cliente_nome.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W+tk.E)
        frame_cliente.columnconfigure(1, weight=1)
        
        # Botões finais
        frame_finalizar = ttk.Frame(frame_direito)
        frame_finalizar.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(frame_finalizar, text="🧾 Gerar Comprovante", 
                  command=self.gerar_comprovante_venda).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_finalizar, text="💾 Finalizar Venda", 
                  command=self.finalizar_venda).pack(side=tk.RIGHT, padx=2)
        
        # Inicializar carrinho
        self.carrinho = []
        self.atualizar_totais()
    
    def novo_produto(self):
        """Abrir formulário para cadastrar novo produto"""
        self.abrir_formulario_produto()
    
    def editar_produto(self):
        """Editar produto selecionado"""
        item = self.tree_produtos.selection()
        if not item:
            messagebox.showwarning("Seleção", "Selecione um produto para editar!")
            return
        
        # Obter dados do produto selecionado
        valores = self.tree_produtos.item(item[0])['values']
        codigo = valores[0]
        
        # Buscar dados completos do produto
        conn = sqlite3.connect("dados/produtos_sic.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE codigo = ?", (codigo,))
        produto = cursor.fetchone()
        conn.close()
        
        if produto:
            # Converter para dicionário
            produto_data = {
                'codigo': produto[0],
                'descricao': produto[1],
                'preco_venda': produto[2],
                'preco_custo': produto[3],
                'estoque': produto[4],
                'categoria': produto[5],
                'ativo': produto[6],
                'marca': produto[8] if len(produto) > 8 else '',
                'unidade': produto[9] if len(produto) > 9 else 'UN',
                'peso': produto[10] if len(produto) > 10 else 0
            }
            self.abrir_formulario_produto(produto_data)
        else:
            messagebox.showerror("Erro", "Produto não encontrado!")
    
    def excluir_produto(self):
        """Excluir produto selecionado"""
        item = self.tree_produtos.selection()
        if not item:
            messagebox.showwarning("Seleção", "Selecione um produto para excluir!")
            return
        
        valores = self.tree_produtos.item(item[0])['values']
        codigo = valores[0]
        descricao = valores[1]
        
        # Confirmar exclusão
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Deseja realmente excluir o produto?\n\nCódigo: {codigo}\nDescrição: {descricao}"
        )
        
        if resposta:
            try:
                conn = sqlite3.connect("dados/produtos_sic.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM produtos WHERE codigo = ?", (codigo,))
                conn.commit()
                conn.close()
                
                self.log(f"🗑️ Produto excluído: {codigo}")
                messagebox.showinfo("Sucesso", f"Produto {codigo} excluído com sucesso!")
                self.listar_produtos()
                
            except Exception as e:
                self.log(f"❌ Erro ao excluir produto: {e}")
                messagebox.showerror("Erro", f"Erro ao excluir produto:\n{e}")
    
    def abrir_formulario_produto(self, produto_data=None):
        """Abrir formulário de cadastro/edição de produto com layout responsivo e scrollbar"""
        # Criar janela do formulário
        janela = tk.Toplevel(self.root)
        janela.title("➕ Cadastro de Produto" if not produto_data else "✏️ Editar Produto")
        janela.geometry("650x700")
        janela.resizable(True, True)
        janela.minsize(600, 500)
        
        # Configurar para centralizar automaticamente
        janela.transient(self.root)
        janela.grab_set()
        
        # Centralizar janela na tela
        self._center_window(janela)
        
        # Criar frame principal com canvas e scrollbar
        main_frame = ttk.Frame(janela)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas para scroll
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configurar scroll
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas e scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Título estilizado
        titulo_frame = ttk.Frame(scrollable_frame)
        titulo_frame.pack(fill=tk.X, pady=(0, 20))
        
        titulo = tk.Label(titulo_frame, 
                         text="📦 Cadastro de Produto" if not produto_data else "✏️ Edição de Produto",
                         font=("Arial", 16, "bold"),
                         fg="#2c3e50")
        titulo.pack()
        
        subtitulo = tk.Label(titulo_frame,
                           text="Preencha os campos abaixo (* campos obrigatórios)",
                           font=("Arial", 10),
                           fg="#7f8c8d")
        subtitulo.pack(pady=(5, 0))
        
        # Container principal dos campos
        form_container = ttk.Frame(scrollable_frame)
        form_container.pack(fill=tk.X, padx=20)
        
        # Seção 1: Informações Básicas
        self._create_section_header(form_container, "📋 Informações Básicas", 0)
        
        current_row = 1
        
        # Código do produto (obrigatório)
        current_row = self._create_form_field(
            form_container, current_row, "*Código do Produto:", 
            validate_func=self._validate_codigo
        )
        entry_codigo = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_codigo.insert(0, produto_data.get('codigo', ''))
            entry_codigo.config(state='readonly')
        
        # Descrição (obrigatória)
        current_row = self._create_form_field(
            form_container, current_row, "*Descrição:",
            width=40, validate_func=self._validate_descricao
        )
        entry_descricao = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_descricao.insert(0, produto_data.get('descricao', ''))
        
        # Seção 2: Preços
        current_row = self._create_section_header(form_container, "💰 Preços", current_row)
        
        # Preço de venda (obrigatório)
        current_row = self._create_form_field(
            form_container, current_row, "*Preço de Venda (R$):", 
            placeholder="Ex: 15,50", validate_func=self._validate_preco_venda
        )
        entry_preco_venda = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_preco_venda.insert(0, str(produto_data.get('preco_venda', '')))
        
        # Preço de custo (opcional)
        current_row = self._create_form_field(
            form_container, current_row, "Preço de Custo (R$):",
            placeholder="Ex: 10,00", validate_func=self._validate_preco_custo
        )
        entry_preco_custo = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_preco_custo.insert(0, str(produto_data.get('preco_custo', '')))
        
        # Seção 3: Estoque e Características
        current_row = self._create_section_header(form_container, "📦 Estoque e Características", current_row)
        
        # Estoque
        current_row = self._create_form_field(
            form_container, current_row, "Estoque Inicial:",
            placeholder="Ex: 100", validate_func=self._validate_estoque
        )
        entry_estoque = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_estoque.insert(0, str(produto_data.get('estoque', '0')))
        else:
            entry_estoque.insert(0, '0')
        
        # Categoria
        current_row = self._create_form_field(
            form_container, current_row, "Categoria:",
            placeholder="Ex: Madeiras, Ferragens"
        )
        entry_categoria = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_categoria.insert(0, produto_data.get('categoria', ''))
        
        # Marca
        current_row = self._create_form_field(
            form_container, current_row, "Marca:",
            placeholder="Ex: Tigre, Eucatex"
        )
        entry_marca = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_marca.insert(0, produto_data.get('marca', ''))
        
        # Unidade
        label_unidade = ttk.Label(form_container, text="Unidade de Medida:", font=("Arial", 10))
        label_unidade.grid(row=current_row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        combo_unidade = ttk.Combobox(form_container, width=25, 
                                   values=['UN', 'KG', 'MT', 'M2', 'M3', 'LT', 'CX', 'PC', 'DZ', 'CJ'],
                                   state="readonly")
        combo_unidade.grid(row=current_row, column=1, sticky=tk.W+tk.E, pady=8)
        if produto_data:
            combo_unidade.set(produto_data.get('unidade', 'UN'))
        else:
            combo_unidade.set('UN')
        current_row += 1
        
        # Peso
        current_row = self._create_form_field(
            form_container, current_row, "Peso (KG):",
            placeholder="Ex: 1,5", validate_func=self._validate_peso
        )
        entry_peso = form_container.children[f"!entry{current_row-1}"]
        if produto_data:
            entry_peso.insert(0, str(produto_data.get('peso', '')))
        
        # Status ativo
        var_ativo = tk.BooleanVar(value=True)
        frame_ativo = ttk.Frame(form_container)
        frame_ativo.grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=15)
        
        check_ativo = ttk.Checkbutton(frame_ativo, text="✓ Produto Ativo", variable=var_ativo)
        check_ativo.pack(anchor=tk.W)
        
        if produto_data:
            var_ativo.set(bool(produto_data.get('ativo', 1)))
        current_row += 1
        
        # Configurar grid responsivo
        form_container.columnconfigure(1, weight=1)
        
        # Frame para botões (fora do canvas para ficar sempre visível)
        frame_botoes = ttk.Frame(main_frame)
        frame_botoes.pack(fill=tk.X, pady=(10, 0))
        
        # Separador visual
        separator = ttk.Separator(frame_botoes, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, pady=(0, 10))
        
        # Container dos botões
        button_container = ttk.Frame(frame_botoes)
        button_container.pack()
        
        # Função melhorada para salvar com validação visual
        def salvar_produto():
            try:
                # Limpar erros visuais anteriores
                self._clear_field_errors(form_container)
                
                # Coletar dados do formulário
                form_data = {
                    'codigo': entry_codigo.get().strip(),
                    'descricao': entry_descricao.get().strip(),
                    'preco_venda': entry_preco_venda.get().strip(),
                    'preco_custo': entry_preco_custo.get().strip(),
                    'estoque': entry_estoque.get().strip() or '0',
                    'categoria': entry_categoria.get().strip(),
                    'marca': entry_marca.get().strip(),
                    'unidade': combo_unidade.get(),
                    'peso': entry_peso.get().strip(),
                    'ativo': 1 if var_ativo.get() else 0
                }
                
                # Validação robusta
                validation_errors = []
                field_widgets = {
                    'codigo': entry_codigo,
                    'descricao': entry_descricao,
                    'preco_venda': entry_preco_venda,
                    'preco_custo': entry_preco_custo,
                    'estoque': entry_estoque,
                    'peso': entry_peso
                }
                
                # Validações específicas com feedback visual
                if not form_data['codigo']:
                    validation_errors.append("Código do produto é obrigatório")
                    self._mark_field_error(entry_codigo)
                
                if not form_data['descricao']:
                    validation_errors.append("Descrição é obrigatória")
                    self._mark_field_error(entry_descricao)
                
                if not form_data['preco_venda']:
                    validation_errors.append("Preço de venda é obrigatório")
                    self._mark_field_error(entry_preco_venda)
                else:
                    try:
                        preco = self._parse_decimal_number(form_data['preco_venda'])
                        if preco <= 0:
                            validation_errors.append("Preço de venda deve ser maior que zero")
                            self._mark_field_error(entry_preco_venda)
                    except ValueError:
                        validation_errors.append("Preço de venda deve ser um número válido")
                        self._mark_field_error(entry_preco_venda)
                
                # Verificar código único (apenas para novos produtos)
                if not produto_data and form_data['codigo']:
                    if self._check_codigo_exists(form_data['codigo']):
                        validation_errors.append("Código já existe. Use um código único.")
                        self._mark_field_error(entry_codigo)
                
                # Se há erros, mostrar e focar no primeiro campo com erro
                if validation_errors:
                    error_message = "❌ Erros encontrados:\n\n" + "\n".join([f"• {error}" for error in validation_errors])
                    messagebox.showerror("Erro de Validação", error_message)
                    
                    # Focar no primeiro campo com erro
                    for field, widget in field_widgets.items():
                        if hasattr(widget, 'cget') and 'error' in str(widget.cget('style')):
                            widget.focus()
                            canvas.yview_moveto(0.0)  # Scroll para o topo
                            break
                    return
                
                # Confirmação de salvamento
                codigo = form_data['codigo']
                descricao = form_data['descricao']
                preco_display = f"R$ {self._parse_decimal_number(form_data['preco_venda']):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                
                action_text = "editado" if produto_data else "cadastrado"
                confirm_message = f"Confirmar produto {action_text}?\n\n"
                confirm_message += f"📦 Código: {codigo}\n"
                confirm_message += f"📝 Descrição: {descricao}\n"
                confirm_message += f"💰 Preço: {preco_display}"
                
                if not messagebox.askokcancel("🔄 Confirmar Operação", confirm_message):
                    return
                
                # Processar salvamento
                self._processar_salvamento(form_data, produto_data, janela)
                
            except Exception as e:
                self.log(f"❌ Erro ao salvar produto: {e}")
                messagebox.showerror("Erro", f"Erro inesperado ao salvar produto:\n{e}")
        
        # Botões estilizados
        btn_salvar = ttk.Button(button_container, text="💾 Salvar Produto", 
                               command=salvar_produto, style="Accent.TButton")
        btn_salvar.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_cancelar = ttk.Button(button_container, text="❌ Cancelar", 
                                 command=janela.destroy)
        btn_cancelar.pack(side=tk.LEFT)
        
        # Configurar scroll com mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Focar no primeiro campo apropriado
        if not produto_data:
            entry_codigo.focus()
        else:
            entry_descricao.focus()
            
        # Atualizar scroll region após tudo estar carregado
        janela.after(100, lambda: canvas.configure(scrollregion=canvas.bbox("all")))
    
    def _center_window(self, window):
        """Centralizar janela na tela automaticamente"""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (window.winfo_width() // 2)
        y = (window.winfo_screenheight() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")
    
    def _parse_decimal_number(self, value_str):
        """Parse decimal number handling both comma and dot as decimal separator"""
        if not value_str or not value_str.strip():
            return 0.0
            
        # Clean the string
        value_str = value_str.strip()
        
        # Handle Brazilian format (1.234,56) vs international format (1,234.56)
        if ',' in value_str and '.' in value_str:
            # If both comma and dot are present, determine which is decimal separator
            last_comma = value_str.rfind(',')
            last_dot = value_str.rfind('.')
            
            if last_comma > last_dot:
                # Brazilian format: 1.234,56
                value_str = value_str.replace('.', '').replace(',', '.')
            else:
                # International format: 1,234.56
                value_str = value_str.replace(',', '')
        elif ',' in value_str:
            # Only comma, assume decimal separator
            value_str = value_str.replace(',', '.')
        
        return float(value_str)
    
    def _create_section_header(self, parent, title, row):
        """Criar cabeçalho de seção estilizado"""
        # Espaçador
        if row > 0:
            ttk.Separator(parent, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, 
                                                           sticky=tk.W+tk.E, pady=(15, 10))
            row += 1
        
        # Título da seção
        header_label = tk.Label(parent, text=title, font=("Arial", 12, "bold"), 
                               fg="#34495e", anchor="w")
        header_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(5, 10))
        
        return row + 1
    
    def _create_form_field(self, parent, row, label_text, width=30, placeholder="", validate_func=None):
        """Criar campo de formulário padronizado"""
        # Label
        label = ttk.Label(parent, text=label_text, font=("Arial", 10))
        label.grid(row=row, column=0, sticky=tk.W, pady=8, padx=(0, 10))
        
        # Entry com validação
        entry = ttk.Entry(parent, width=width)
        entry.grid(row=row, column=1, sticky=tk.W+tk.E, pady=8)
        
        # Placeholder
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(foreground='grey')
            
            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)
                    entry.config(foreground='black')
            
            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)
                    entry.config(foreground='grey')
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
        
        # Validação em tempo real
        if validate_func:
            entry.bind('<KeyRelease>', lambda e: validate_func(entry))
        
        return row + 1
    
    def _validate_codigo(self, entry):
        """Validar código do produto em tempo real"""
        codigo = entry.get().strip()
        if codigo and not re.match(r'^[A-Za-z0-9_-]+$', codigo):
            entry.config(style="Error.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _validate_descricao(self, entry):
        """Validar descrição do produto"""
        descricao = entry.get().strip()
        if len(descricao) > 100:
            entry.config(style="Warning.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _validate_preco_venda(self, entry):
        """Validar preço de venda"""
        preco = entry.get().strip()
        if preco:
            try:
                valor = self._parse_decimal_number(preco)
                if valor <= 0:
                    entry.config(style="Error.TEntry")
                else:
                    entry.config(style="TEntry")
            except ValueError:
                entry.config(style="Error.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _validate_preco_custo(self, entry):
        """Validar preço de custo"""
        preco = entry.get().strip()
        if preco:
            try:
                valor = self._parse_decimal_number(preco)
                if valor < 0:
                    entry.config(style="Error.TEntry")
                else:
                    entry.config(style="TEntry")
            except ValueError:
                entry.config(style="Error.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _validate_estoque(self, entry):
        """Validar estoque"""
        estoque = entry.get().strip()
        if estoque:
            try:
                valor = int(estoque)
                if valor < 0:
                    entry.config(style="Error.TEntry")
                else:
                    entry.config(style="TEntry")
            except ValueError:
                entry.config(style="Error.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _validate_peso(self, entry):
        """Validar peso"""
        peso = entry.get().strip()
        if peso:
            try:
                valor = self._parse_decimal_number(peso)
                if valor < 0:
                    entry.config(style="Error.TEntry")
                else:
                    entry.config(style="TEntry")
            except ValueError:
                entry.config(style="Error.TEntry")
        else:
            entry.config(style="TEntry")
    
    def _mark_field_error(self, entry):
        """Marcar campo com erro visual"""
        entry.config(style="Error.TEntry")
    
    def _clear_field_errors(self, container):
        """Limpar marcações de erro nos campos"""
        for child in container.winfo_children():
            if isinstance(child, ttk.Entry):
                child.config(style="TEntry")
    
    def _check_codigo_exists(self, codigo):
        """Verificar se código já existe no banco"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM produtos WHERE codigo = ?", (codigo,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception:
            return False
    
    def _processar_salvamento(self, form_data, produto_data, janela):
        """Processar salvamento do produto com indicador de progresso"""
        # Criar janela de progresso
        progress_window = tk.Toplevel(janela)
        progress_window.title("Salvando...")
        progress_window.geometry("350x120")
        progress_window.transient(janela)
        progress_window.grab_set()
        progress_window.resizable(False, False)
        
        # Centralizar janela de progresso
        self._center_window(progress_window)
        
        # Conteúdo da janela de progresso
        progress_frame = ttk.Frame(progress_window)
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        progress_label = tk.Label(progress_frame, text="💾 Salvando produto...", 
                                font=("Arial", 12), fg="#2c3e50")
        progress_label.pack(pady=(0, 10))
        
        progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', length=300)
        progress_bar.pack(pady=5)
        progress_bar.start()
        
        status_label = tk.Label(progress_frame, text="Processando dados...", 
                              font=("Arial", 9), fg="#7f8c8d")
        status_label.pack(pady=(5, 0))
        
        # Função para salvar em thread separada
        def salvar_em_thread():
            try:
                # Atualizar status
                progress_window.after(0, lambda: status_label.config(text="Validando dados..."))
                time.sleep(0.3)
                
                # Converter tipos
                preco_venda_float = self._parse_decimal_number(form_data['preco_venda'])
                preco_custo_float = self._parse_decimal_number(form_data['preco_custo']) if form_data['preco_custo'] else 0
                estoque_int = int(form_data['estoque'])
                peso_float = self._parse_decimal_number(form_data['peso']) if form_data['peso'] else 0
                
                # Atualizar status
                progress_window.after(0, lambda: status_label.config(text="Conectando ao banco..."))
                time.sleep(0.3)
                
                # Salvar no banco
                conn = sqlite3.connect("dados/produtos_sic.db")
                cursor = conn.cursor()
                
                progress_window.after(0, lambda: status_label.config(text="Salvando produto..."))
                
                if produto_data:  # Editar
                    cursor.execute('''
                        UPDATE produtos SET
                            descricao = ?, preco_venda = ?, preco_custo = ?, estoque = ?,
                            categoria = ?, marca = ?, unidade = ?, peso = ?, ativo = ?,
                            ultima_atualizacao = CURRENT_TIMESTAMP, atualizado_em = CURRENT_TIMESTAMP
                        WHERE codigo = ?
                    ''', (
                        form_data['descricao'], preco_venda_float, preco_custo_float,
                        estoque_int, form_data['categoria'], form_data['marca'],
                        form_data['unidade'], peso_float, form_data['ativo'],
                        form_data['codigo']
                    ))
                    self.log(f"✏️ Produto editado: {form_data['codigo']}")
                    message = f"✅ Produto {form_data['codigo']} editado com sucesso!"
                else:  # Novo
                    cursor.execute('''
                        INSERT INTO produtos (
                            codigo, descricao, preco_venda, preco_custo, estoque,
                            categoria, marca, unidade, peso, ativo, atualizado_em
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ''', (
                        form_data['codigo'], form_data['descricao'], preco_venda_float,
                        preco_custo_float, estoque_int, form_data['categoria'],
                        form_data['marca'], form_data['unidade'], peso_float, form_data['ativo']
                    ))
                    self.log(f"➕ Produto cadastrado: {form_data['codigo']}")
                    message = f"✅ Produto {form_data['codigo']} cadastrado com sucesso!"
                
                conn.commit()
                conn.close()
                
                # Finalizar
                progress_window.after(0, lambda: status_label.config(text="Finalizando..."))
                time.sleep(0.3)
                
                # Fechar janela de progresso e mostrar sucesso
                self.root.after(0, lambda: [
                    progress_window.destroy(),
                    messagebox.showinfo("🎉 Sucesso", message),
                    self.listar_produtos(),
                    janela.destroy()
                ])
                
            except Exception as e:
                # Fechar janela de progresso e mostrar erro
                error_msg = f"❌ Erro ao salvar produto:\n{e}"
                self.root.after(0, lambda: [
                    progress_window.destroy(),
                    messagebox.showerror("Erro", error_msg)
                ])
                self.log(f"❌ Erro ao salvar produto: {e}")
        
        # Executar salvamento em thread
        threading.Thread(target=salvar_em_thread, daemon=True).start()
    
    # Métodos PDV
    def buscar_produto_pdv(self):
        """Buscar produto para o PDV"""
        termo = self.entry_busca_pdv.get().strip()
        if not termo:
            return
        
        # Limpar lista
        for item in self.tree_produtos_pdv.get_children():
            self.tree_produtos_pdv.delete(item)
        
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT codigo, descricao, preco_venda, estoque
                FROM produtos 
                WHERE (codigo LIKE ? OR descricao LIKE ?) AND ativo = 1
                ORDER BY descricao
                LIMIT 50
            """, (f"%{termo}%", f"%{termo}%"))
            
            produtos = cursor.fetchall()
            conn.close()
            
            for produto in produtos:
                codigo, descricao, preco, estoque = produto
                self.tree_produtos_pdv.insert("", tk.END, values=(
                    codigo,
                    descricao[:40],
                    f"R$ {preco:.2f}",
                    estoque
                ))
                
        except Exception as e:
            self.log(f"❌ Erro buscar produto PDV: {e}")
    
    def adicionar_ao_carrinho(self):
        """Adicionar produto selecionado ao carrinho"""
        item = self.tree_produtos_pdv.selection()
        if not item:
            messagebox.showwarning("Seleção", "Selecione um produto!")
            return
        
        valores = self.tree_produtos_pdv.item(item[0])['values']
        codigo = valores[0]
        descricao = valores[1]
        preco_str = valores[2].replace('R$ ', '').replace(',', '.')
        estoque = int(valores[3])
        
        if estoque <= 0:
            messagebox.showwarning("Estoque", f"Produto {codigo} sem estoque!")
            return
        
        # Perguntar quantidade
        quantidade = tk.simpledialog.askinteger(
            "Quantidade", 
            f"Produto: {descricao}\nPreço: {valores[2]}\n\nQuantidade:",
            minvalue=1, maxvalue=estoque, initialvalue=1
        )
        
        if quantidade:
            preco = float(preco_str)
            total = quantidade * preco
            
            # Verificar se produto já está no carrinho
            for item_carrinho in self.tree_carrinho.get_children():
                if self.tree_carrinho.item(item_carrinho)['values'][0] == codigo:
                    # Atualizar quantidade
                    valores_existentes = self.tree_carrinho.item(item_carrinho)['values']
                    nova_qtd = int(valores_existentes[2]) + quantidade
                    novo_total = nova_qtd * preco
                    
                    self.tree_carrinho.item(item_carrinho, values=(
                        codigo, descricao, nova_qtd, f"R$ {preco:.2f}", f"R$ {novo_total:.2f}"
                    ))
                    
                    # Atualizar lista de carrinho interna
                    for item_interno in self.carrinho:
                        if item_interno['codigo'] == codigo:
                            item_interno['quantidade'] = nova_qtd
                            item_interno['total'] = novo_total
                            break
                    
                    self.atualizar_totais()
                    return
            
            # Adicionar novo item
            self.tree_carrinho.insert("", tk.END, values=(
                codigo, descricao, quantidade, f"R$ {preco:.2f}", f"R$ {total:.2f}"
            ))
            
            # Adicionar à lista interna
            self.carrinho.append({
                'codigo': codigo,
                'descricao': descricao,
                'quantidade': quantidade,
                'preco': preco,
                'total': total
            })
            
            self.atualizar_totais()
            self.log(f"🛒 Adicionado ao carrinho: {codigo} x{quantidade}")
    
    def remover_do_carrinho(self):
        """Remover item selecionado do carrinho"""
        item = self.tree_carrinho.selection()
        if not item:
            messagebox.showwarning("Seleção", "Selecione um item para remover!")
            return
        
        valores = self.tree_carrinho.item(item[0])['values']
        codigo = valores[0]
        
        # Remover da treeview
        self.tree_carrinho.delete(item[0])
        
        # Remover da lista interna
        self.carrinho = [item for item in self.carrinho if item['codigo'] != codigo]
        
        self.atualizar_totais()
        self.log(f"🗑️ Removido do carrinho: {codigo}")
    
    def limpar_carrinho(self):
        """Limpar todo o carrinho"""
        if self.carrinho and messagebox.askyesno("Confirmar", "Limpar todo o carrinho?"):
            # Limpar treeview
            for item in self.tree_carrinho.get_children():
                self.tree_carrinho.delete(item)
            
            # Limpar lista interna
            self.carrinho = []
            self.atualizar_totais()
            self.log("🗑️ Carrinho limpo")
    
    def atualizar_totais(self):
        """Atualizar totais do carrinho"""
        subtotal = sum(item['total'] for item in self.carrinho)
        
        self.label_subtotal.config(text=f"Subtotal: R$ {subtotal:.2f}")
        self.label_total.config(text=f"TOTAL: R$ {subtotal:.2f}")
    
    def gerar_comprovante_venda(self):
        """Gerar comprovante da venda"""
        if not self.carrinho:
            messagebox.showwarning("Carrinho Vazio", "Adicione produtos ao carrinho!")
            return
        
        try:
            cliente_nome = self.entry_cliente_nome.get().strip() or "Cliente"
            
            # Criar comprovante
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            arquivo = f"relatorios/comprovante_{timestamp}.txt"
            os.makedirs("relatorios", exist_ok=True)
            
            subtotal = sum(item['total'] for item in self.carrinho)
            
            conteudo = f"""
{'='*60}
           MADEIREIRA MARIA LUIZA
        Rua das Madeiras, 456 - Sua Cidade - SP
            (11) 9999-8888 | CNPJ: XX.XXX.XXX/0001-XX
{'='*60}

              COMPROVANTE DE VENDA

Nº: {timestamp[-6:]}        Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
Cliente: {cliente_nome}

{'='*60}
Cód. | Descrição                    | Qtd | Preço  | Total
{'='*60}
"""
            
            for item in self.carrinho:
                linha = f"{item['codigo']:<5}| {item['descricao'][:25]:<25}| {item['quantidade']:>3} | {item['preco']:>6.2f} | {item['total']:>6.2f}\n"
                conteudo += linha
            
            conteudo += f"""
{'='*60}
                              TOTAL: R$ {subtotal:.2f}
{'='*60}
    Obrigado pela preferência! Volte sempre!
           MADEIREIRA MARIA LUIZA
{'='*60}
"""
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            self.log(f"🧾 Comprovante gerado: {arquivo}")
            
            if messagebox.askyesno("Comprovante Gerado", f"Comprovante criado!\n\n📄 {arquivo}\n\nAbrir para impressão?"):
                os.startfile(arquivo)
                
        except Exception as e:
            self.log(f"❌ Erro gerar comprovante: {e}")
            messagebox.showerror("Erro", f"Erro ao gerar comprovante:\n{e}")
    
    def finalizar_venda(self):
        """Finalizar venda e atualizar estoque"""
        if not self.carrinho:
            messagebox.showwarning("Carrinho Vazio", "Adicione produtos ao carrinho!")
            return
        
        # Confirmar venda
        subtotal = sum(item['total'] for item in self.carrinho)
        if not messagebox.askyesno("Finalizar Venda", f"Finalizar venda no valor de R$ {subtotal:.2f}?"):
            return
        
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            cursor = conn.cursor()
            
            # Atualizar estoque de cada produto
            for item in self.carrinho:
                cursor.execute('''
                    UPDATE produtos SET 
                        estoque = estoque - ?,
                        ultima_atualizacao = CURRENT_TIMESTAMP 
                    WHERE codigo = ?
                ''', (item['quantidade'], item['codigo']))
            
            conn.commit()
            conn.close()
            
            # Gerar comprovante
            self.gerar_comprovante_venda()
            
            # Limpar carrinho
            self.limpar_carrinho()
            
            # Limpar cliente
            self.entry_cliente_nome.delete(0, tk.END)
            
            self.log(f"💰 Venda finalizada: R$ {subtotal:.2f}")
            messagebox.showinfo("Venda Finalizada", f"Venda de R$ {subtotal:.2f} finalizada com sucesso!")
            
            # Atualizar lista de produtos
            self.listar_produtos()
            
        except Exception as e:
            self.log(f"❌ Erro finalizar venda: {e}")
            messagebox.showerror("Erro", f"Erro ao finalizar venda:\n{e}")
    
    def fazer_backup_manual(self):
        """Fazer backup manual dos dados"""
        try:
            self.fazer_backup()
            messagebox.showinfo("Backup", "Backup realizado com sucesso!")
        except Exception as e:
            self.log(f"❌ Erro backup manual: {e}")
            messagebox.showerror("Erro", f"Erro ao fazer backup:\n{e}")
    
    def fazer_backup(self):
        """Fazer backup do banco de dados"""
        try:
            import shutil
            
            # Criar pasta de backups
            backup_dir = "backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nome do arquivo de backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/backup_produtos_{timestamp}.db"
            
            # Copiar banco de dados
            if os.path.exists("dados/produtos_sic.db"):
                shutil.copy2("dados/produtos_sic.db", backup_file)
                
                # Também criar backup em formato SQL
                sql_backup = f"{backup_dir}/backup_produtos_{timestamp}.sql"
                self.exportar_backup_sql(sql_backup)
                
                self.log(f"💾 Backup criado: {backup_file}")
                return True
            else:
                self.log("❌ Banco de dados não encontrado para backup")
                return False
                
        except Exception as e:
            self.log(f"❌ Erro fazer backup: {e}")
            raise
    
    def exportar_backup_sql(self, arquivo_sql):
        """Exportar backup em formato SQL"""
        try:
            conn = sqlite3.connect("dados/produtos_sic.db")
            
            with open(arquivo_sql, 'w', encoding='utf-8') as f:
                # Cabeçalho
                f.write(f"-- Backup Sistema PDV - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write("-- Madeireira Maria Luiza\n\n")
                
                # Dump do banco
                for linha in conn.iterdump():
                    f.write(f"{linha}\n")
            
            conn.close()
            self.log(f"💾 Backup SQL criado: {arquivo_sql}")
            
        except Exception as e:
            self.log(f"❌ Erro backup SQL: {e}")
    
    def abrir_pasta_backups(self):
        """Abrir pasta de backups"""
        try:
            backup_dir = os.path.abspath("backups")
            os.makedirs(backup_dir, exist_ok=True)
            os.startfile(backup_dir)
            self.log("📂 Pasta backups aberta")
        except Exception as e:
            self.log(f"❌ Erro abrir pasta backups: {e}")
    
    def verificar_backup_automatico(self):
        """Verificar se deve fazer backup automático"""
        try:
            if not self.var_backup_auto.get():
                return
            
            # Verificar último backup
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                # Primeiro backup
                self.fazer_backup()
                return
            
            # Encontrar último backup
            backups = [f for f in os.listdir(backup_dir) if f.startswith("backup_produtos_") and f.endswith(".db")]
            if not backups:
                # Nenhum backup encontrado
                self.fazer_backup()
                return
            
            # Verificar data do último backup
            ultimo_backup = max(backups)
            backup_path = os.path.join(backup_dir, ultimo_backup)
            backup_time = os.path.getmtime(backup_path)
            agora = time.time()
            
            # Fazer backup se o último foi há mais de 24 horas
            if (agora - backup_time) > (24 * 60 * 60):
                self.fazer_backup()
                
        except Exception as e:
            self.log(f"❌ Erro verificar backup automático: {e}")
    
    def inicializar_sistema_backup(self):
        """Inicializar sistema de backup automático"""
        def verificar_periodicamente():
            while True:
                try:
                    self.verificar_backup_automatico()
                except:
                    pass
                time.sleep(3600)  # Verificar a cada hora
        
        thread = threading.Thread(target=verificar_periodicamente, daemon=True)
        thread.start()
    
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
        
        # Load current config from secure manager
        legacy_config = self.config_manager.load_legacy_config()
        
        ttk.Label(group_sic, text="Servidor SQL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_servidor = ttk.Entry(group_sic, width=40)
        self.entry_servidor.insert(0, legacy_config.get('servidor', ''))
        self.entry_servidor.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Database:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_database = ttk.Entry(group_sic, width=40)
        self.entry_database.insert(0, legacy_config.get('banco', ''))
        self.entry_database.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Usuário:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_usuario = ttk.Entry(group_sic, width=40)
        self.entry_usuario.insert(0, legacy_config.get('usuario', ''))
        self.entry_usuario.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(group_sic, text="Senha:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.entry_senha = ttk.Entry(group_sic, width=40, show="*")
        # Não carregar senha por segurança
        self.entry_senha.grid(row=3, column=1, padx=5, pady=2)
        
        # Adicionar aviso sobre segurança
        ttk.Label(group_sic, text="⚠️ Por segurança, a senha deve ser inserida a cada conexão", 
                 foreground="orange", font=("Arial", 8)).grid(row=4, column=0, columnspan=2, pady=5)
        
        
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
        
        # Botões de backup
        frame_backup = ttk.Frame(group_sistema)
        frame_backup.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            frame_backup,
            text="💾 Fazer Backup",
            command=self.fazer_backup_manual
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            frame_backup,
            text="📂 Abrir Pasta Backups",
            command=self.abrir_pasta_backups
        ).pack(side=tk.LEFT, padx=5)
        
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
            
            # Add missing columns if they don't exist
            self._add_missing_columns(cursor)
            
            conn.commit()
            conn.close()
            
            self.log("✅ Banco local criado/verificado")
            
        except Exception as e:
            self.log(f"❌ Erro criar banco local: {e}")
    
    def _add_missing_columns(self, cursor):
        """Add missing columns to produtos table if they don't exist"""
        missing_columns = [
            ('marca', 'TEXT'),
            ('unidade', 'TEXT DEFAULT "UN"'),
            ('peso', 'REAL DEFAULT 0'),
            ('atualizado_em', 'TIMESTAMP')  # Cannot use CURRENT_TIMESTAMP as default when adding column
        ]
        
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(produtos)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        for column_name, column_type in missing_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE produtos ADD COLUMN {column_name} {column_type}")
                    self.log(f"✅ Coluna adicionada: {column_name}")
                    
                    # For atualizado_em, update existing records to current timestamp
                    if column_name == 'atualizado_em':
                        cursor.execute("UPDATE produtos SET atualizado_em = CURRENT_TIMESTAMP WHERE atualizado_em IS NULL")
                        
                except Exception as e:
                    self.log(f"⚠️ Erro ao adicionar coluna {column_name}: {e}")

    def verificar_sic_periodicamente(self):
        """Verificar status SIC em background com timeout de sessão"""
        def verificar():
            while True:
                try:
                    # Verificar timeout de sessão
                    if self.conectado_sic and self.check_session_timeout():
                        self.log("⏰ Sessão SIC expirou por timeout")
                        self.desconectar_sic()
                    
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
        """Conectar ao banco SIC com autenticação segura"""
        try:
            # Obter credenciais seguras
            sic_credentials = self.config_manager.get_sic_credentials()
            if not sic_credentials:
                self.log("❌ Falha na autenticação SIC")
                return False
            
            import pyodbc
            
            # Construir string de conexão com credenciais seguras
            conn_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={sic_credentials['servidor']};"
                f"DATABASE={sic_credentials['banco']};"
                f"UID={sic_credentials['usuario']};"
                f"PWD={sic_credentials['senha']};"
                f"Timeout={sic_credentials.get('timeout', '30')};"
                f"TrustServerCertificate=yes;"
            )
            
            self.conn_sic = pyodbc.connect(conn_string)
            self.conectado_sic = True
            self.session_start_time = datetime.now()
            self.log("✅ Conectado ao SIC com autenticação segura")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro conexão SIC: {e}")
            self.conectado_sic = False
            return False

    def check_session_timeout(self):
        """Verificar se a sessão expirou"""
        if not self.session_start_time:
            return True
        
        elapsed_minutes = (datetime.now() - self.session_start_time).total_seconds() / 60
        return elapsed_minutes > self.session_timeout_minutes

    def desconectar_sic(self):
        """Desconectar do SIC e limpar sessão"""
        try:
            if self.conn_sic:
                self.conn_sic.close()
                self.conn_sic = None
            self.conectado_sic = False
            self.session_start_time = None
            self.config_manager.clear_session()
            self.log("🔒 Sessão SIC encerrada")
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
                SELECT codigo, descricao, preco_venda, preco_custo, estoque, categoria, ativo
                FROM produtos 
                ORDER BY descricao
                LIMIT 1000
            """)
            
            produtos = cursor.fetchall()
            conn.close()
            
            # Inserir na treeview
            for produto in produtos:
                codigo, descricao, preco_venda, preco_custo, estoque, categoria, ativo = produto
                status = "Ativo" if ativo else "Inativo"
                self.tree_produtos.insert("", tk.END, values=(
                    codigo,
                    descricao[:50] if descricao else "",  # Limitar descrição
                    f"R$ {preco_venda:.2f}" if preco_venda else "R$ 0,00",
                    f"R$ {preco_custo:.2f}" if preco_custo else "R$ 0,00",
                    estoque or 0,
                    categoria or "",
                    status
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