# scripts/importar_arquivo_sic.py - VERSÃO MELHORADA
import xml.etree.ElementTree as ET
import csv
import pandas as pd
import sqlite3
import os
from tkinter import filedialog, messagebox
import json

class ImportadorSIC:
    def __init__(self):
        self.tipos_suportados = {
            'XML': ['.xml'],
            'CSV': ['.csv', '.txt'],
            'Excel': ['.xlsx', '.xls'],
            'JSON': ['.json'],
            'DBF': ['.dbf']  # ← ADICIONADO
        }
    
    def selecionar_arquivo(self):
        """Abre diálogo para selecionar arquivo"""
        filetypes = [
            ('Todos Suportados', '*.xml;*.csv;*.txt;*.xlsx;*.xls;*.json;*.dbf'),
            ('XML files', '*.xml'),
            ('CSV files', '*.csv;*.txt'),
            ('Excel files', '*.xlsx;*.xls'),
            ('JSON files', '*.json'),
            ('DBF files', '*.dbf'),  # ← ADICIONADO
            ('Todos os arquivos', '*.*')
        ]
        
        arquivo = filedialog.askopenfilename(
            title="📁 Selecione o arquivo de produtos do SIC 5.1.14",  # ← MELHORADO
            filetypes=filetypes,
            initialdir=os.getcwd()
        )
        
        return arquivo
    
    def detectar_formato(self, arquivo):
        """Detecta formato do arquivo"""
        extensao = os.path.splitext(arquivo)[1].lower()
        
        if extensao == '.xml':
            return 'XML'
        elif extensao in ['.csv', '.txt']:
            return 'CSV'
        elif extensao in ['.xlsx', '.xls']:
            return 'EXCEL'
        elif extensao == '.json':
            return 'JSON'
        elif extensao == '.dbf':
            return 'DBF'  # ← ADICIONADO
        else:
            return 'DESCONHECIDO'
    
    def importar_xml_sic(self, arquivo):
        """Importa produtos de XML do SIC"""
        try:
            print(f"📄 Lendo arquivo XML: {os.path.basename(arquivo)}")
            
            tree = ET.parse(arquivo)
            root = tree.getroot()
            
            produtos = []
            
            # Estrutura XML típica do SIC (ajustar conforme necessário)
            for produto in root.findall('.//produto') or root.findall('.//PRODUTO') or root.findall('.//item'):
                item = {
                    'codigo': self.get_xml_text(produto, ['codigo', 'CODIGO', 'cod', 'id']),
                    'codigo_barras': self.get_xml_text(produto, ['codigo_barras', 'CODIGO_BARRAS', 'barras', 'ean']),
                    'descricao': self.get_xml_text(produto, ['descricao', 'DESCRICAO', 'nome', 'name']),
                    'preco_venda': self.get_xml_float(produto, ['preco_venda', 'PRECO_VENDA', 'preco', 'valor']),
                    'preco_custo': self.get_xml_float(produto, ['preco_custo', 'PRECO_CUSTO', 'custo']),
                    'estoque': self.get_xml_int(produto, ['estoque', 'ESTOQUE', 'quantidade', 'saldo']),
                    'peso': self.get_xml_float(produto, ['peso', 'PESO']),
                    'categoria': self.get_xml_text(produto, ['categoria', 'CATEGORIA', 'grupo']),
                    'marca': self.get_xml_text(produto, ['marca', 'MARCA', 'fabricante']),  # ← ADICIONADO
                    'unidade': self.get_xml_text(produto, ['unidade', 'UNIDADE', 'un'])
                }
                
                if item['codigo'] and item['descricao']:
                    produtos.append(item)
            
            print(f"✅ XML processado: {len(produtos)} produtos encontrados")
            return produtos
            
        except Exception as e:
            raise Exception(f"Erro ao ler XML: {e}")
    
    def importar_csv_sic(self, arquivo):
        """Importa produtos de CSV do SIC"""
        try:
            print(f"📊 Lendo arquivo CSV/TXT: {os.path.basename(arquivo)}")
            
            # Tenta detectar encoding e separador
            encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
            separators = [';', ',', '\t', '|']  # ← MELHORADO
            
            df = None
            encoding_usado = None
            separador_usado = None
            
            for encoding in encodings:
                for sep in separators:
                    try:
                        df_teste = pd.read_csv(arquivo, encoding=encoding, sep=sep, nrows=5)
                        if len(df_teste.columns) > 1:  # Se tem mais de 1 coluna
                            df = pd.read_csv(arquivo, encoding=encoding, sep=sep)
                            encoding_usado = encoding
                            separador_usado = sep
                            break
                    except:
                        continue
                if df is not None:
                    break
            
            if df is None:
                # Fallback para engine python
                df = pd.read_csv(arquivo, sep=None, engine='python', encoding='utf-8')
                separador_usado = 'auto-detectado'
                encoding_usado = 'utf-8'
            
            print(f"📋 Encoding: {encoding_usado}, Separador: '{separador_usado}'")
            print(f"📊 Colunas encontradas: {list(df.columns)}")
            
            # Mapeia colunas (nomes comuns do SIC) - EXPANDIDO
            mapeamento_colunas = {
                'codigo': ['codigo', 'cod', 'code', 'id', 'ref', 'referencia'],
                'codigo_barras': ['codigo_barras', 'barras', 'ean', 'gtin', 'codbar'],
                'descricao': ['descricao', 'nome', 'produto', 'description', 'desc'],
                'preco_venda': ['preco_venda', 'preco', 'valor', 'price', 'pvenda', 'preço'],
                'preco_custo': ['preco_custo', 'custo', 'cost', 'pcusto'],
                'estoque': ['estoque', 'quantidade', 'qty', 'stock', 'saldo', 'qtd'],
                'peso': ['peso', 'weight', 'kg'],
                'categoria': ['categoria', 'grupo', 'category', 'cat', 'tipo'],
                'marca': ['marca', 'brand', 'fabricante', 'manufacturer'],  # ← ADICIONADO
                'unidade': ['unidade', 'un', 'unit', 'medida']
            }
            
            # Normaliza nomes das colunas
            df.columns = [str(col).lower().strip() for col in df.columns]
            
            produtos = []
            total_linhas = len(df)
            
            for index, row in df.iterrows():
                try:
                    item = {}
                    
                    for campo, opcoes in mapeamento_colunas.items():
                        valor = None
                        for opcao in opcoes:
                            if opcao in df.columns:
                                valor = row[opcao]
                                break
                        
                        # Converte tipos
                        if campo in ['preco_venda', 'preco_custo', 'peso']:
                            item[campo] = self.safe_float(valor)
                        elif campo == 'estoque':
                            item[campo] = self.safe_int(valor)
                        else:
                            item[campo] = str(valor) if valor is not None and str(valor).lower() not in ['nan', 'none', ''] else ''
                    
                    # Só adiciona se tem código e descrição válidos
                    if item.get('codigo') and item.get('descricao') and item['codigo'] != '' and item['descricao'] != '':
                        produtos.append(item)
                    
                    # Progress feedback
                    if (index + 1) % 500 == 0:
                        print(f"📊 Processando linha {index + 1}/{total_linhas}")
                        
                except Exception as e:
                    print(f"⚠️ Erro na linha {index + 1}: {e}")
                    continue
            
            print(f"✅ CSV processado: {len(produtos)} produtos válidos de {total_linhas} linhas")
            return produtos
            
        except Exception as e:
            raise Exception(f"Erro ao ler CSV: {e}")
    
    def importar_excel_sic(self, arquivo):
        """Importa produtos de Excel do SIC"""
        try:
            print(f"📈 Lendo arquivo Excel: {os.path.basename(arquivo)}")
            
            # Lê Excel - tenta diferentes planilhas se necessário
            try:
                df = pd.read_excel(arquivo, sheet_name=0)  # Primeira planilha
            except:
                # Se falhar, tenta outras planilhas
                xls = pd.ExcelFile(arquivo)
                sheet_names = xls.sheet_names
                print(f"📋 Planilhas encontradas: {sheet_names}")
                df = pd.read_excel(arquivo, sheet_name=sheet_names[0])
            
            print(f"📊 Excel - {len(df)} linhas, {len(df.columns)} colunas")
            
            # Converte para CSV temporário e usa a função CSV
            arquivo_temp = 'temp_excel.csv'
            df.to_csv(arquivo_temp, index=False, encoding='utf-8', sep=';')
            
            produtos = self.importar_csv_sic(arquivo_temp)
            
            # Remove arquivo temporário
            if os.path.exists(arquivo_temp):
                os.remove(arquivo_temp)
            
            return produtos
            
        except Exception as e:
            raise Exception(f"Erro ao ler Excel: {e}")
    
    def importar_dbf_sic(self, arquivo):
        """Importa produtos de DBF do SIC - NOVO"""
        try:
            print(f"🗃️ Lendo arquivo DBF: {os.path.basename(arquivo)}")
            
            try:
                from dbfread import DBF
                
                table = DBF(arquivo, encoding='latin-1')
                records = list(table)
                
                if not records:
                    raise Exception("Arquivo DBF vazio")
                
                df = pd.DataFrame(records)
                print(f"📊 DBF - {len(df)} registros, {len(df.columns)} campos")
                
                # Converte para CSV e usa função CSV
                arquivo_temp = 'temp_dbf.csv'
                df.to_csv(arquivo_temp, index=False, encoding='utf-8', sep=';')
                
                produtos = self.importar_csv_sic(arquivo_temp)
                
                # Remove arquivo temporário
                if os.path.exists(arquivo_temp):
                    os.remove(arquivo_temp)
                
                return produtos
                
            except ImportError:
                raise Exception("Biblioteca dbfread não instalada.\nInstale com: pip install dbfread")
                
        except Exception as e:
            raise Exception(f"Erro ao ler DBF: {e}")
    
    def salvar_no_sqlite(self, produtos):
        """Salva produtos no SQLite local"""
        try:
            print("💾 Salvando produtos no banco local...")
            
            # Cria diretório se não existir
            os.makedirs('dados', exist_ok=True)
            
            conn = sqlite3.connect('dados/produtos_sic.db')
            cursor = conn.cursor()
            
            # Cria tabela com estrutura melhorada
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    codigo TEXT PRIMARY KEY,
                    codigo_barras TEXT,
                    descricao TEXT NOT NULL,
                    preco REAL NOT NULL DEFAULT 0,  -- ← COMPATIBILIDADE
                    preco_venda REAL NOT NULL DEFAULT 0,
                    preco_custo REAL DEFAULT 0,
                    estoque INTEGER DEFAULT 0,       -- ← COMPATIBILIDADE
                    estoque_atual INTEGER DEFAULT 0,
                    peso REAL DEFAULT 0.5,
                    categoria TEXT,
                    marca TEXT,                      -- ← ADICIONADO
                    unidade TEXT DEFAULT 'UN',
                    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Atualiza tabela se campos não existem
            try:
                cursor.execute('ALTER TABLE produtos ADD COLUMN marca TEXT')
            except:
                pass
            
            # Opção: limpar dados antigos ou atualizar
            resposta = messagebox.askyesno(
                "Dados Existentes",
                "Limpar produtos existentes e importar novos?\n\n" +
                "✅ SIM = Substitui todos os produtos\n" +
                "❌ NÃO = Adiciona/atualiza produtos existentes"
            )
            
            if resposta:
                cursor.execute('DELETE FROM produtos')
                print("🗑️ Produtos antigos removidos")
            
            # Insere/atualiza produtos
            inseridos = 0
            atualizados = 0
            
            for produto in produtos:
                try:
                    # Verifica se produto existe
                    cursor.execute('SELECT codigo FROM produtos WHERE codigo = ?', (produto.get('codigo', ''),))
                    existe = cursor.fetchone()
                    
                    if existe and not resposta:  # Se existe e não escolheu limpar
                        # Atualiza produto existente
                        cursor.execute('''
                            UPDATE produtos SET 
                            codigo_barras = ?, descricao = ?, preco = ?, preco_venda = ?,
                            preco_custo = ?, estoque = ?, estoque_atual = ?, peso = ?, 
                            categoria = ?, marca = ?, unidade = ?, data_importacao = CURRENT_TIMESTAMP
                            WHERE codigo = ?
                        ''', (
                            produto.get('codigo_barras', ''),
                            produto.get('descricao', ''),
                            produto.get('preco_venda', 0),  # preco = preco_venda para compatibilidade
                            produto.get('preco_venda', 0),
                            produto.get('preco_custo', 0),
                            produto.get('estoque', 0),  # estoque = estoque_atual para compatibilidade
                            produto.get('estoque', 0),
                            produto.get('peso', 0.5),
                            produto.get('categoria', ''),
                            produto.get('marca', ''),
                            produto.get('unidade', 'UN'),
                            produto.get('codigo', '')
                        ))
                        atualizados += 1
                    else:
                        # Insere novo produto
                        cursor.execute('''
                            INSERT OR REPLACE INTO produtos (
                                codigo, codigo_barras, descricao, preco, preco_venda,
                                preco_custo, estoque, estoque_atual, peso, categoria, marca, unidade
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            produto.get('codigo', ''),
                            produto.get('codigo_barras', ''),
                            produto.get('descricao', ''),
                            produto.get('preco_venda', 0),  # preco = preco_venda
                            produto.get('preco_venda', 0),
                            produto.get('preco_custo', 0),
                            produto.get('estoque', 0),  # estoque = estoque_atual
                            produto.get('estoque', 0),
                            produto.get('peso', 0.5),
                            produto.get('categoria', ''),
                            produto.get('marca', ''),
                            produto.get('unidade', 'UN')
                        ))
                        inseridos += 1
                    
                    # Progress feedback
                    if (inseridos + atualizados) % 100 == 0:
                        print(f"💾 Salvos: {inseridos + atualizados}")
                        
                except sqlite3.Error as e:
                    print(f"❌ Erro ao salvar produto {produto.get('codigo', 'N/A')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            print(f"✅ Salvamento concluído:")
            print(f"   ➕ Inseridos: {inseridos}")
            print(f"   🔄 Atualizados: {atualizados}")
            print(f"   📊 Total: {inseridos + atualizados}")
            
            return inseridos + atualizados
            
        except Exception as e:
            raise Exception(f"Erro ao salvar no banco: {e}")
    
    def processar_arquivo(self, arquivo):
        """Processa arquivo selecionado"""
        print(f"🔍 Detectando formato do arquivo...")
        formato = self.detectar_formato(arquivo)
        print(f"📋 Formato detectado: {formato}")
        
        if formato == 'XML':
            produtos = self.importar_xml_sic(arquivo)
        elif formato == 'CSV':
            produtos = self.importar_csv_sic(arquivo)
        elif formato == 'EXCEL':
            produtos = self.importar_excel_sic(arquivo)
        elif formato == 'JSON':
            produtos = self.importar_json_sic(arquivo)
        elif formato == 'DBF':
            produtos = self.importar_dbf_sic(arquivo)  # ← ADICIONADO
        else:
            raise Exception(f"Formato não suportado: {formato}")
        
        if not produtos:
            raise Exception("Nenhum produto válido encontrado no arquivo")
        
        print(f"📦 {len(produtos)} produtos válidos encontrados")
        
        # Salva no banco
        inseridos = self.salvar_no_sqlite(produtos)
        
        return inseridos, len(produtos)
    
    # Funções auxiliares
    def get_xml_text(self, elemento, tags):
        for tag in tags:
            child = elemento.find(tag)
            if child is not None and child.text:
                return child.text.strip()
        return ''
    
    def get_xml_float(self, elemento, tags):
        text = self.get_xml_text(elemento, tags)
        return self.safe_float(text)
    
    def get_xml_int(self, elemento, tags):
        text = self.get_xml_text(elemento, tags)
        return self.safe_int(text)
    
    def safe_float(self, valor):
        try:
            if valor is None or valor == '' or str(valor).lower() in ['nan', 'none']:
                return 0.0
            # Remove caracteres não numéricos exceto . e , - MELHORADO
            valor_str = str(valor).replace(',', '.').strip()
            # Remove espaços e outros caracteres
            import re
            valor_str = re.sub(r'[^\d.-]', '', valor_str)
            return float(valor_str) if valor_str else 0.0
        except:
            return 0.0
    
    def safe_int(self, valor):
        try:
            if valor is None or valor == '' or str(valor).lower() in ['nan', 'none']:
                return 0
            return int(float(str(valor).replace(',', '.')))
        except:
            return 0
    
    def importar_json_sic(self, arquivo):
        """Importa produtos de JSON"""
        try:
            print(f"📄 Lendo arquivo JSON: {os.path.basename(arquivo)}")
            
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            produtos = []
            
            # Se é uma lista direta
            if isinstance(data, list):
                items = data
            # Se tem uma chave "produtos" ou similar
            elif isinstance(data, dict):
                items = data.get('produtos', data.get('items', data.get('data', [])))
                if not items:
                    # Se não achou, usa os próprios valores do dict
                    items = [data]
            else:
                raise Exception("Estrutura JSON não reconhecida")
            
            for item in items:
                produto = {
                    'codigo': item.get('codigo', item.get('code', item.get('id', ''))),
                    'codigo_barras': item.get('codigo_barras', item.get('barcode', item.get('ean', ''))),
                    'descricao': item.get('descricao', item.get('nome', item.get('name', item.get('description', '')))),
                    'preco_venda': self.safe_float(item.get('preco_venda', item.get('price', item.get('preco', 0)))),
                    'preco_custo': self.safe_float(item.get('preco_custo', item.get('cost', 0))),
                    'estoque': self.safe_int(item.get('estoque', item.get('stock', item.get('quantidade', 0)))),
                    'peso': self.safe_float(item.get('peso', item.get('weight', 0.5))),
                    'categoria': item.get('categoria', item.get('category', item.get('grupo', ''))),
                    'marca': item.get('marca', item.get('brand', item.get('fabricante', ''))),  # ← ADICIONADO
                    'unidade': item.get('unidade', item.get('unit', 'UN'))
                }
                
                if produto['codigo'] and produto['descricao']:
                    produtos.append(produto)
            
            print(f"✅ JSON processado: {len(produtos)} produtos encontrados")
            return produtos
            
        except Exception as e:
            raise Exception(f"Erro ao ler JSON: {e}")

# Função para usar no sistema principal
def importar_arquivo_sic():
    """Função principal para importar arquivo do SIC"""
    try:
        print("🚀 Iniciando importação de arquivo SIC...")
        print("👤 Usuário: Matheus-TestUser1")
        print("📅 Data: 2025-07-14 17:51:43")
        
        importador = ImportadorSIC()
        
        arquivo = importador.selecionar_arquivo()
        if not arquivo:
            return 0, "Operação cancelada pelo usuário"
        
        print(f"📁 Arquivo selecionado: {os.path.basename(arquivo)}")
        print(f"📂 Caminho completo: {arquivo}")
        
        inseridos, total = importador.processar_arquivo(arquivo)
        
        mensagem = f"✅ Importação concluída!\n\n"
        mensagem += f"📁 Arquivo: {os.path.basename(arquivo)}\n"
        mensagem += f"📊 Produtos processados: {total}\n"
        mensagem += f"💾 Produtos salvos: {inseridos}\n"
        mensagem += f"📅 Data: 2025-07-14 17:51:43"
        
        print(mensagem)
        return inseridos, mensagem
        
    except Exception as e:
        erro_msg = f"❌ Erro na importação: {e}"
        print(erro_msg)
        return 0, erro_msg

if __name__ == "__main__":
    # Teste direto
    inseridos, mensagem = importar_arquivo_sic()
    print(f"\n📋 RESULTADO FINAL:")
    print(f"Inseridos: {inseridos}")
    print(f"Mensagem: {mensagem}")