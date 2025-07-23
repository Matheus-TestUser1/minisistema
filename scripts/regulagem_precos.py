# scripts/regulagem_precos.py - NOVO MÓDULO
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from decimal import Decimal, ROUND_HALF_UP

class RegulagemPrecos:
    def __init__(self, parent):
        self.parent = parent
        self.criar_janela()
    
    def criar_janela(self):
        """Cria janela de regulagem de preços"""
        self.janela = tk.Toplevel(self.parent)
        self.janela.title("💰 Regulagem de Preços - SIC 5.1.14")
        self.janela.geometry("800x600")
        self.janela.transient(self.parent)
        
        # Frame principal
        main_frame = ttk.Frame(self.janela, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="💰 REGULAGEM DE PREÇOS", 
                 font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Filtros
        filtros_frame = ttk.LabelFrame(main_frame, text="Filtros de Produtos", padding="10")
        filtros_frame.pack(fill=tk.X, pady=5)
        
        # Categoria
        ttk.Label(filtros_frame, text="Categoria:").grid(row=0, column=0, sticky=tk.W)
        self.combo_categoria = ttk.Combobox(filtros_frame, width=30)
        self.combo_categoria.grid(row=0, column=1, padx=5)
        
        # Marca
        ttk.Label(filtros_frame, text="Marca:").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        self.combo_marca = ttk.Combobox(filtros_frame, width=20)
        self.combo_marca.grid(row=0, column=3, padx=5)
        
        # Faixa de preço
        ttk.Label(filtros_frame, text="Preço de:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        self.entry_preco_min = ttk.Entry(filtros_frame, width=15)
        self.entry_preco_min.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(10,0))
        
        ttk.Label(filtros_frame, text="até:").grid(row=1, column=2, sticky=tk.W, padx=(20,0), pady=(10,0))
        self.entry_preco_max = ttk.Entry(filtros_frame, width=15)
        self.entry_preco_max.grid(row=1, column=3, sticky=tk.W, padx=5, pady=(10,0))
        
        # Botão buscar
        ttk.Button(filtros_frame, text="🔍 Buscar Produtos", 
                  command=self.buscar_produtos).grid(row=2, column=0, columnspan=4, pady=10)
        
        # Regulagem
        regulagem_frame = ttk.LabelFrame(main_frame, text="Aplicar Regulagem", padding="10")
        regulagem_frame.pack(fill=tk.X, pady=5)
        
        # Tipo de regulagem
        ttk.Label(regulagem_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W)
        self.tipo_regulagem = tk.StringVar(value="percentual")
        
        ttk.Radiobutton(regulagem_frame, text="% Percentual", 
                       variable=self.tipo_regulagem, value="percentual").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(regulagem_frame, text="R$ Valor Fixo", 
                       variable=self.tipo_regulagem, value="fixo").grid(row=0, column=2, sticky=tk.W, padx=(20,0))
        
        # Valor
        ttk.Label(regulagem_frame, text="Valor:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        self.entry_valor_regulagem = ttk.Entry(regulagem_frame, width=15)
        self.entry_valor_regulagem.grid(row=1, column=1, sticky=tk.W, padx=5, pady=(10,0))
        
        # Operação
        ttk.Label(regulagem_frame, text="Operação:").grid(row=1, column=2, sticky=tk.W, padx=(20,0), pady=(10,0))
        self.operacao = tk.StringVar(value="aumentar")
        
        ttk.Radiobutton(regulagem_frame, text="➕ Aumentar", 
                       variable=self.operacao, value="aumentar").grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(regulagem_frame, text="➖ Diminuir", 
                       variable=self.operacao, value="diminuir").grid(row=2, column=2, sticky=tk.W, padx=(20,0))
        
        # Botões de ação
        btn_frame = ttk.Frame(regulagem_frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=15)
        
        ttk.Button(btn_frame, text="🧮 Calcular Prévia", 
                  command=self.calcular_previa).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✅ Aplicar Regulagem", 
                  command=self.aplicar_regulagem).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Salvar Lista", 
                  command=self.salvar_lista_precos).pack(side=tk.LEFT, padx=5)
        
        # Lista de produtos
        lista_frame = ttk.LabelFrame(main_frame, text="Produtos Encontrados", padding="5")
        lista_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview
        columns = ('codigo', 'descricao', 'categoria', 'preco_atual', 'preco_novo', 'diferenca')
        self.tree_produtos = ttk.Treeview(lista_frame, columns=columns, show='headings', height=15)
        
        # Cabeçalhos
        self.tree_produtos.heading('codigo', text='Código')
        self.tree_produtos.heading('descricao', text='Descrição')
        self.tree_produtos.heading('categoria', text='Categoria')
        self.tree_produtos.heading('preco_atual', text='Preço Atual')
        self.tree_produtos.heading('preco_novo', text='Preço Novo')
        self.tree_produtos.heading('diferenca', text='Diferença')
        
        # Larguras
        self.tree_produtos.column('codigo', width=80)
        self.tree_produtos.column('descricao', width=250)
        self.tree_produtos.column('categoria', width=120)
        self.tree_produtos.column('preco_atual', width=100)
        self.tree_produtos.column('preco_novo', width=100)
        self.tree_produtos.column('diferenca', width=100)
        
        # Scrollbar
        scrollbar_produtos = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL, command=self.tree_produtos.yview)
        self.tree_produtos.configure(yscrollcommand=scrollbar_produtos.set)
        
        self.tree_produtos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_produtos.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status
        self.status_regulagem = tk.StringVar(value="Pronto para regular preços - Matheus-TestUser1")
        ttk.Label(main_frame, textvariable=self.status_regulagem).pack(pady=5)
        
        # Carrega dados iniciais
        self.carregar_filtros()
    
    def carregar_filtros(self):
        """Carrega categorias e marcas para os filtros"""
        try:
            conn = sqlite3.connect('dados/produtos_sic.db')
            cursor = conn.cursor()
            
            # Categorias
            cursor.execute('SELECT DISTINCT categoria FROM produtos WHERE categoria IS NOT NULL ORDER BY categoria')
            categorias = ['Todas'] + [row[0] for row in cursor.fetchall()]
            self.combo_categoria['values'] = categorias
            self.combo_categoria.set('Todas')
            
            # Marcas
            cursor.execute('SELECT DISTINCT marca FROM produtos WHERE marca IS NOT NULL ORDER BY marca')
            marcas = ['Todas'] + [row[0] for row in cursor.fetchall()]
            self.combo_marca['values'] = marcas
            self.combo_marca.set('Todas')
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar filtros: {e}")
    
    def buscar_produtos(self):
        """Busca produtos conforme filtros"""
        try:
            conn = sqlite3.connect('dados/produtos_sic.db')
            cursor = conn.cursor()
            
            # Monta query com filtros
            where_clauses = []
            params = []
            
            # Filtro categoria
            if self.combo_categoria.get() != 'Todas' and self.combo_categoria.get():
                where_clauses.append("categoria = ?")
                params.append(self.combo_categoria.get())
            
            # Filtro marca
            if self.combo_marca.get() != 'Todas' and self.combo_marca.get():
                where_clauses.append("marca = ?")
                params.append(self.combo_marca.get())
            
            # Filtro preço mínimo
            if self.entry_preco_min.get():
                where_clauses.append("preco >= ?")
                params.append(float(self.entry_preco_min.get().replace(',', '.')))
            
            # Filtro preço máximo
            if self.entry_preco_max.get():
                where_clauses.append("preco <= ?")
                params.append(float(self.entry_preco_max.get().replace(',', '.')))
            
            # Query final
            query = "SELECT codigo, descricao, categoria, preco FROM produtos"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            query += " ORDER BY descricao"
            
            cursor.execute(query, params)
            produtos = cursor.fetchall()
            
            # Limpa tree
            for item in self.tree_produtos.get_children():
                self.tree_produtos.delete(item)
            
            # Adiciona produtos
            for produto in produtos:
                self.tree_produtos.insert('', tk.END, values=(
                    produto[0],  # codigo
                    produto[1],  # descricao
                    produto[2] or '',  # categoria
                    f"R$ {produto[3]:.2f}".replace('.', ','),  # preco_atual
                    '',  # preco_novo (vazio por enquanto)
                    ''   # diferenca (vazio por enquanto)
                ))
            
            conn.close()
            self.status_regulagem.set(f"✅ {len(produtos)} produtos encontrados")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na busca: {e}")
    
    def calcular_previa(self):
        """Calcula prévia dos novos preços"""
        try:
            if not self.entry_valor_regulagem.get():
                messagebox.showwarning("Aviso", "Digite o valor da regulagem!")
                return
            
            valor = float(self.entry_valor_regulagem.get().replace(',', '.'))
            tipo = self.tipo_regulagem.get()
            operacao = self.operacao.get()
            
            # Atualiza tree com novos preços
            for item in self.tree_produtos.get_children():
                valores = self.tree_produtos.item(item)['values']
                preco_atual_str = valores[3].replace('R$ ', '').replace(',', '.')
                preco_atual = float(preco_atual_str)
                
                # Calcula novo preço
                if tipo == "percentual":
                    if operacao == "aumentar":
                        preco_novo = preco_atual * (1 + valor / 100)
                    else:
                        preco_novo = preco_atual * (1 - valor / 100)
                else:  # fixo
                    if operacao == "aumentar":
                        preco_novo = preco_atual + valor
                    else:
                        preco_novo = preco_atual - valor
                
                # Garante que não fique negativo
                preco_novo = max(0.01, preco_novo)
                
                # Arredonda para 2 casas
                preco_novo = float(Decimal(str(preco_novo)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
                
                diferenca = preco_novo - preco_atual
                
                # Atualiza valores na tree
                novos_valores = list(valores)
                novos_valores[4] = f"R$ {preco_novo:.2f}".replace('.', ',')
                novos_valores[5] = f"R$ {diferenca:+.2f}".replace('.', ',')
                
                self.tree_produtos.item(item, values=novos_valores)
            
            self.status_regulagem.set("🧮 Prévia calculada - Clique 'Aplicar' para confirmar")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no cálculo: {e}")
    
    def aplicar_regulagem(self):
        """Aplica regulagem definitivamente no banco"""
        try:
            # Confirma operação
            total_produtos = len(self.tree_produtos.get_children())
            if total_produtos == 0:
                messagebox.showwarning("Aviso", "Nenhum produto para regular!")
                return
            
            resposta = messagebox.askyesno(
                "Confirmar Regulagem",
                f"Aplicar regulagem em {total_produtos} produtos?\n\n" +
                "⚠️ Esta operação não pode ser desfeita!",
                icon='warning'
            )
            
            if not resposta:
                return
            
            conn = sqlite3.connect('dados/produtos_sic.db')
            cursor = conn.cursor()
            
            atualizados = 0
            
            for item in self.tree_produtos.get_children():
                valores = self.tree_produtos.item(item)['values']
                codigo = valores[0]
                preco_novo_str = valores[4]
                
                if preco_novo_str:  # Se tem preço novo calculado
                    preco_novo = float(preco_novo_str.replace('R$ ', '').replace(',', '.'))
                    
                    cursor.execute('UPDATE produtos SET preco = ? WHERE codigo = ?', 
                                 (preco_novo, codigo))
                    atualizados += 1
            
            conn.commit()
            conn.close()
            
            self.status_regulagem.set(f"✅ Regulagem aplicada: {atualizados} produtos atualizados")
            messagebox.showinfo("Sucesso", f"Regulagem aplicada com sucesso!\n\n" +
                               f"🔄 {atualizados} produtos atualizados")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar regulagem: {e}")
    
    def salvar_lista_precos(self):
        """Salva lista de preços em arquivo"""
        try:
            from tkinter import filedialog
            
            arquivo = filedialog.asksaveasfilename(
                title="Salvar Lista de Preços",
                defaultextension=".csv",
                filetypes=[
                    ("CSV files", "*.csv"),
                    ("Excel files", "*.xlsx"),
                    ("Text files", "*.txt")
                ]
            )
            
            if not arquivo:
                return
            
            # Gera conteúdo
            linhas = ["Codigo;Descricao;Categoria;Preco_Atual;Preco_Novo;Diferenca\n"]
            
            for item in self.tree_produtos.get_children():
                valores = self.tree_produtos.item(item)['values']
                linha = ";".join(str(v) for v in valores) + "\n"
                linhas.append(linha)
            
            # Salva arquivo
            with open(arquivo, 'w', encoding='utf-8') as f:
                f.writelines(linhas)
            
            self.status_regulagem.set(f"💾 Lista salva: {arquivo}")
            messagebox.showinfo("Sucesso", f"Lista de preços salva!\n\n{arquivo}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")

def abrir_regulagem_precos(parent):
    """Abre janela de regulagem de preços"""
    RegulagemPrecos(parent)