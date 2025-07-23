# scripts/exportar_sic.py
import sqlite3
import os
from conexao_sic import get_conexao_sic
from datetime import datetime

def criar_tabela_produtos():
    """Cria tabela de produtos SQLite"""
    conn = sqlite3.connect('dados/produtos_sic.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            codigo TEXT PRIMARY KEY,
            codigo_barras TEXT,
            descricao TEXT NOT NULL,
            descricao_complementar TEXT,
            preco_venda REAL NOT NULL,
            preco_custo REAL,
            estoque_atual INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 0,
            peso REAL DEFAULT 0,
            categoria TEXT,
            marca TEXT,
            unidade TEXT DEFAULT 'UN',
            ativo BOOLEAN DEFAULT 1,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def exportar_produtos_sic():
    """Exporta produtos do SIC para SQLite local"""
    try:
        criar_tabela_produtos()
        
        # Conecta ao SIC
        sic_conn = get_conexao_sic()
        cursor_sic = sic_conn.cursor()
        
        # Query para buscar produtos do SIC
        # AJUSTE CONFORME SUA ESTRUTURA DE TABELAS SIC
        query_sic = """
        SELECT 
            p.CODIGO,
            p.CODIGO_BARRAS,
            p.DESCRICAO,
            p.DESCRICAO_COMPLEMENTAR,
            p.PRECO_VENDA,
            p.PRECO_CUSTO,
            e.ESTOQUE_ATUAL,
            p.ESTOQUE_MINIMO,
            p.PESO,
            c.DESCRICAO as CATEGORIA,
            m.DESCRICAO as MARCA,
            p.UNIDADE,
            p.ATIVO
        FROM PRODUTOS p
        LEFT JOIN ESTOQUE e ON p.CODIGO = e.CODIGO_PRODUTO
        LEFT JOIN CATEGORIAS c ON p.ID_CATEGORIA = c.ID
        LEFT JOIN MARCAS m ON p.ID_MARCA = m.ID
        WHERE p.ATIVO = 1
        ORDER BY p.DESCRICAO
        """
        
        cursor_sic.execute(query_sic)
        produtos = cursor_sic.fetchall()
        
        # Conecta SQLite local
        local_conn = sqlite3.connect('dados/produtos_sic.db')
        cursor_local = local_conn.cursor()
        
        # Limpa dados antigos
        cursor_local.execute('DELETE FROM produtos')
        
        # Insere produtos
        for produto in produtos:
            cursor_local.execute('''
                INSERT INTO produtos (
                    codigo, codigo_barras, descricao, descricao_complementar,
                    preco_venda, preco_custo, estoque_atual, estoque_minimo,
                    peso, categoria, marca, unidade, ativo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', produto)
        
        local_conn.commit()
        
        # Cleanup
        sic_conn.close()
        local_conn.close()
        
        print(f"✅ Exportados {len(produtos)} produtos do SIC")
        return len(produtos)
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        raise e

def sincronizar_estoque_sic():
    """Sincroniza apenas estoque com SIC"""
    try:
        # Conecta ao SIC
        sic_conn = get_conexao_sic()
        cursor_sic = sic_conn.cursor()
        
        # Busca estoque atualizado
        query_estoque = """
        SELECT CODIGO_PRODUTO, ESTOQUE_ATUAL
        FROM ESTOQUE
        WHERE CODIGO_PRODUTO IN (
            SELECT codigo FROM produtos_local
        )
        """
        
        # Se sua tabela for diferente, ajuste aqui:
        cursor_sic.execute("""
            SELECT p.CODIGO, e.ESTOQUE_ATUAL
            FROM PRODUTOS p
            INNER JOIN ESTOQUE e ON p.CODIGO = e.CODIGO_PRODUTO
            WHERE p.ATIVO = 1
        """)
        
        estoques = cursor_sic.fetchall()
        
        # Atualiza SQLite local
        local_conn = sqlite3.connect('dados/produtos_sic.db')
        cursor_local = local_conn.cursor()
        
        atualizados = 0
        for codigo, estoque in estoques:
            cursor_local.execute('''
                UPDATE produtos 
                SET estoque_atual = ?, data_atualizacao = CURRENT_TIMESTAMP
                WHERE codigo = ?
            ''', (estoque, codigo))
            
            if cursor_local.rowcount > 0:
                atualizados += 1
        
        local_conn.commit()
        
        # Cleanup
        sic_conn.close()
        local_conn.close()
        
        print(f"✅ Sincronizados {atualizados} produtos")
        return atualizados
        
    except Exception as e:
        print(f"❌ Erro na sincronização: {e}")
        raise e

if __name__ == "__main__":
    # Teste direto
    quantidade = exportar_produtos_sic()
    print(f"Processo concluído: {quantidade} produtos")