# scripts/conexao_sic.py - VERSÃO PARA REDE
import pyodbc
import configparser
import os
import socket

def descobrir_servidor_sic():
    """Tenta descobrir servidores SQL na rede"""
    try:
        # Lista servidores SQL disponíveis
        servers = []
        
        # IPs comuns para testar
        ips_teste = [
            '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '192.168.0.100', '192.168.0.101', '192.168.0.102',
            '10.0.0.100', '10.0.0.101'
        ]
        
        for ip in ips_teste:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((ip, 1433))
                sock.close()
                
                if result == 0:
                    servers.append(ip)
            except:
                continue
        
        return servers
    except:
        return []

def testar_conexao_sic():
    """Testa conexão com banco do SIC em rede"""
    try:
        config = configparser.ConfigParser()
        config_path = os.path.join('dados', 'config.ini')
        
        if not os.path.exists(config_path):
            return False, "Arquivo config.ini não encontrado"
        
        config.read(config_path, encoding='utf-8')
        
        # Monta string de conexão
        servidor = config['SIC']['servidor']
        porta = config['SIC'].get('porta', '1433')
        banco = config['SIC']['banco']
        usuario = config['SIC']['usuario']
        senha = config['SIC']['senha']
        timeout = config['SIC'].get('timeout', '30')
        
        # Verifica se tem instância nomeada
        instancia = config['SIC'].get('instancia', '')
        if instancia:
            servidor_completo = f"{servidor}\\{instancia}"
        else:
            servidor_completo = f"{servidor},{porta}"
        
        # String de conexão para SQL Server
        conn_str = f"""
        DRIVER={{ODBC Driver 17 for SQL Server}};
        SERVER={servidor_completo};
        DATABASE={banco};
        UID={usuario};
        PWD={senha};
        TrustServerCertificate=yes;
        Connection Timeout={timeout};
        """
        
        # Tenta drivers alternativos se não tiver o 17
        drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server", 
            "ODBC Driver 11 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server Native Client 10.0",
            "SQL Server"
        ]
        
        conn = None
        driver_usado = ""
        
        for driver in drivers:
            try:
                conn_str_teste = f"""
                DRIVER={{{driver}}};
                SERVER={servidor_completo};
                DATABASE={banco};
                UID={usuario};
                PWD={senha};
                TrustServerCertificate=yes;
                Connection Timeout={timeout};
                """
                
                conn = pyodbc.connect(conn_str_teste)
                driver_usado = driver
                break
                
            except pyodbc.Error:
                continue
        
        if not conn:
            return False, "Nenhum driver SQL Server encontrado"
        
        cursor = conn.cursor()
        
        # Testa acesso às tabelas do SIC
        tabela_produtos = config['SIC_TABELAS'].get('produtos', 'PRODUTOS')
        
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela_produtos}")
            total_produtos = cursor.fetchone()[0]
        except:
            # Tenta nomes alternativos
            nomes_teste = ['PRODUTOS', 'PRODUTO', 'PRD', 'ITEMS', 'CADASTRO_PRODUTOS']
            total_produtos = 0
            tabela_encontrada = ""
            
            for nome in nomes_teste:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {nome}")
                    total_produtos = cursor.fetchone()[0]
                    tabela_encontrada = nome
                    break
                except:
                    continue
        
        # Testa versão do SIC
        try:
            cursor.execute("SELECT @@VERSION")
            versao_sql = cursor.fetchone()[0]
        except:
            versao_sql = "Não identificada"
        
        conn.close()
        
        mensagem = f"""
Conectado com sucesso!
Servidor: {servidor_completo}
Banco: {banco}
Driver: {driver_usado}
Produtos encontrados: {total_produtos}
SQL Server: {versao_sql[:50]}...
        """
        
        return True, mensagem.strip()
        
    except pyodbc.Error as e:
        erro_msg = str(e)
        
        # Mensagens de erro mais amigáveis
        if "server not found" in erro_msg.lower():
            servidores = descobrir_servidor_sic()
            if servidores:
                return False, f"Servidor não encontrado. Servidores SQL detectados: {', '.join(servidores)}"
            else:
                return False, "Servidor não encontrado. Verifique IP/nome do servidor."
        
        elif "login failed" in erro_msg.lower():
            return False, "Falha na autenticação. Verifique usuário e senha."
        
        elif "database" in erro_msg.lower():
            return False, "Banco de dados não encontrado. Verifique nome do banco SIC."
        
        else:
            return False, f"Erro SQL: {erro_msg}"
    
    except Exception as e:
        return False, f"Erro geral: {str(e)}"

def get_conexao_sic():
    """Retorna conexão ativa com SIC"""
    config = configparser.ConfigParser()
    config.read(os.path.join('dados', 'config.ini'), encoding='utf-8')
    
    servidor = config['SIC']['servidor']
    porta = config['SIC'].get('porta', '1433')
    banco = config['SIC']['banco']
    usuario = config['SIC']['usuario']
    senha = config['SIC']['senha']
    
    instancia = config['SIC'].get('instancia', '')
    if instancia:
        servidor_completo = f"{servidor}\\{instancia}"
    else:
        servidor_completo = f"{servidor},{porta}"
    
    # Tenta drivers na ordem de preferência
    drivers = [
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    
    for driver in drivers:
        try:
            conn_str = f"""
            DRIVER={{{driver}}};
            SERVER={servidor_completo};
            DATABASE={banco};
            UID={usuario};
            PWD={senha};
            TrustServerCertificate=yes;
            """
            
            return pyodbc.connect(conn_str)
        except:
            continue
    
    raise Exception("Não foi possível conectar ao SQL Server")

def listar_tabelas_sic():
    """Lista todas as tabelas do banco SIC"""
    try:
        conn = get_conexao_sic()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        
        tabelas = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return tabelas
    except Exception as e:
        return []

if __name__ == "__main__":
    # Teste da conexão
    print("Testando conexão SIC...")
    sucesso, mensagem = testar_conexao_sic()
    
    if sucesso:
        print("✅ CONECTADO!")
        print(mensagem)
        
        print("\n📋 Listando tabelas...")
        tabelas = listar_tabelas_sic()
        for tabela in tabelas[:10]:  # Primeiras 10
            print(f"  - {tabela}")
    else:
        print("❌ ERRO!")
        print(mensagem)