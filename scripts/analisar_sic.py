# scripts/analisar_sic.py
from conexao_sic import get_conexao_sic

def analisar_estrutura_sic():
    """Analisa a estrutura do banco SIC"""
    try:
        conn = get_conexao_sic()
        cursor = conn.cursor()
        
        print("🔍 ANALISANDO ESTRUTURA SIC 5.1.14...")
        print("=" * 50)
        
        # Lista tabelas
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            AND TABLE_NAME LIKE '%PROD%'
            OR TABLE_NAME LIKE '%ESTO%'
            OR TABLE_NAME LIKE '%ITEM%'
            ORDER BY TABLE_NAME
        """)
        
        tabelas_produtos = cursor.fetchall()
        
        print("📦 TABELAS DE PRODUTOS ENCONTRADAS:")
        for tabela in tabelas_produtos:
            print(f"  - {tabela[0]}")
            
            # Mostra estrutura da tabela
            try:
                cursor.execute(f"""
                    SELECT COLUMN_NAME, DATA_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = '{tabela[0]}'
                    ORDER BY ORDINAL_POSITION
                """)
                
                colunas = cursor.fetchall()
                print(f"    Colunas ({len(colunas)}):")
                for coluna in colunas[:5]:  # Primeiras 5
                    print(f"      - {coluna[0]} ({coluna[1]})")
                
                if len(colunas) > 5:
                    print(f"      ... e mais {len(colunas) - 5} colunas")
                
                print()
                
            except:
                print("    (Erro ao acessar estrutura)")
                print()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    analisar_estrutura_sic()