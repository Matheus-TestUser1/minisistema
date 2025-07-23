# scripts/detectar_sic.py - VERSÃO ATUALIZADA PARA WINSRV
import winreg
import os
import socket
import configparser
import pyodbc
from pathlib import Path

class DetectorSIC:
    def __init__(self):
        self.informacoes_sic = {}
        self.servidores_encontrados = []
        
    def detectar_sic_completo(self):
        """Detecção completa do SIC no sistema"""
        print("🔍 INICIANDO DETECÇÃO AUTOMÁTICA DO SIC...")
        print(f"📅 Data: 2025-07-13 18:57:25")
        print(f"👤 Usuário: Matheus-TestUser1")
        print("=" * 60)
        
        # 1. Detectar instalação local (incluindo WinSRV)
        print("1️⃣ Procurando instalação local do SIC...")
        instalacao_local = self.detectar_instalacao_local()
        
        # 2. Verificar registro do Windows
        print("\n2️⃣ Verificando registro do Windows...")
        config_registro = self.ler_registro_sic()
        
        # 3. Procurar arquivos de configuração
        print("\n3️⃣ Procurando arquivos de configuração...")
        config_arquivos = self.buscar_arquivos_config()
        
        # 4. Detectar servidores SQL na rede
        print("\n4️⃣ Escaneando rede para servidores SQL...")
        self.escanear_rede_sql()
        
        # 5. Testar conexões encontradas
        print("\n5️⃣ Testando conexões encontradas...")
        conexoes_validas = self.testar_conexoes_encontradas()
        
        # 6. Gerar relatório
        print("\n" + "=" * 60)
        self.gerar_relatorio(instalacao_local, config_registro, config_arquivos, conexoes_validas)
        
        return self.informacoes_sic
    
    def detectar_instalacao_local(self):
        """Detecta se o SIC está instalado localmente - INCLUINDO WINSRV"""
        try:
            # Diretórios comuns do SIC - ADICIONADO WINSRV
            diretorios_sic = [
                "C:\\WinSRV",           # ← ADICIONADO!
                "C:\\WINSRV",           # ← ADICIONADO!
                "C:\\winsrv",           # ← ADICIONADO!
                "C:\\SIC",
                "C:\\Program Files\\SIC",
                "C:\\Program Files (x86)\\SIC",
                "C:\\SICNET",
                "C:\\Program Files\\SICNET",
                "C:\\Program Files (x86)\\SICNET",
                "D:\\SIC",
                "D:\\SICNET",
                "D:\\WinSRV",           # ← ADICIONADO!
                "D:\\WINSRV"            # ← ADICIONADO!
            ]
            
            instalacoes = []
            
            print("   🔍 Verificando diretórios...")
            
            for diretorio in diretorios_sic:
                print(f"      Verificando: {diretorio}...", end="")
                
                if os.path.exists(diretorio):
                    print(" ✅ EXISTE!")
                    
                    # Procura executáveis do SIC
                    executaveis = []
                    arquivos_sic = []
                    
                    try:
                        for arquivo in os.listdir(diretorio):
                            arquivo_lower = arquivo.lower()
                            
                            # Executáveis do SIC
                            if arquivo_lower.endswith('.exe') and any(termo in arquivo_lower for termo in ['sic', 'srv', 'sistema']):
                                executaveis.append(arquivo)
                            
                            # Arquivos relacionados ao SIC
                            if any(termo in arquivo_lower for termo in ['sic', 'srv', 'config', 'database', 'bd']):
                                arquivos_sic.append(arquivo)
                    
                    except PermissionError:
                        print(f"      ⚠️ Sem permissão para listar: {diretorio}")
                        continue
                    
                    if executaveis or arquivos_sic:
                        # Tenta detectar versão
                        versao = self.detectar_versao_sic(diretorio)
                        
                        # Procura arquivos de configuração específicos
                        configs = self.buscar_configs_no_diretorio(diretorio)
                        
                        instalacao = {
                            'diretorio': diretorio,
                            'executaveis': executaveis,
                            'arquivos_sic': arquivos_sic,
                            'versao': versao,
                            'configuracoes': configs
                        }
                        instalacoes.append(instalacao)
                        
                        print(f"      ✅ SIC encontrado em: {diretorio}")
                        print(f"         Versão: {versao}")
                        if executaveis:
                            print(f"         Executáveis: {', '.join(executaveis)}")
                        if arquivos_sic:
                            print(f"         Arquivos SIC: {len(arquivos_sic)} encontrados")
                        if configs:
                            print(f"         Configurações: {len(configs)} arquivos")
                else:
                    print(" ❌")
            
            if not instalacoes:
                print("   ❌ Nenhuma instalação local do SIC encontrada")
                print("   💡 Dica: Verifique se o SIC está em outro diretório")
            
            return instalacoes
            
        except Exception as e:
            print(f"   ❌ Erro ao detectar instalação: {e}")
            return []
    
    def buscar_configs_no_diretorio(self, diretorio):
        """Busca arquivos de configuração específicos no diretório"""
        configs = []
        
        # Arquivos de configuração comuns do SIC
        arquivos_config = [
            'sic.ini', 'sicnet.ini', 'config.ini', 'sistema.ini',
            'database.ini', 'conexao.ini', 'bd.ini', 'srv.ini',
            'winsrv.ini', 'configuracao.ini', 'setup.ini'
        ]
        
        try:
            for arquivo in os.listdir(diretorio):
                arquivo_lower = arquivo.lower()
                
                # Verifica se é um arquivo de configuração
                if arquivo_lower in [f.lower() for f in arquivos_config] or arquivo_lower.endswith('.ini'):
                    caminho_completo = os.path.join(diretorio, arquivo)
                    
                    try:
                        # Tenta ler como INI
                        config = configparser.ConfigParser()
                        config.read(caminho_completo, encoding='latin1')
                        
                        if config.sections():
                            config_dict = {}
                            for secao in config.sections():
                                config_dict[secao] = dict(config[secao])
                            
                            configs.append({
                                'arquivo': arquivo,
                                'caminho': caminho_completo,
                                'configuracoes': config_dict
                            })
                    except:
                        # Se não for INI válido, tenta ler como texto
                        try:
                            with open(caminho_completo, 'r', encoding='latin1') as f:
                                conteudo = f.read()
                                
                            if any(termo in conteudo.lower() for termo in ['server', 'database', 'usuario', 'senha']):
                                configs.append({
                                    'arquivo': arquivo,
                                    'caminho': caminho_completo,
                                    'tipo': 'texto',
                                    'conteudo': conteudo[:200] + "..." if len(conteudo) > 200 else conteudo
                                })
                        except:
                            continue
        
        except Exception as e:
            print(f"      ⚠️ Erro ao buscar configs em {diretorio}: {e}")
        
        return configs
    
    def detectar_versao_sic(self, diretorio):
        """Detecta versão do SIC no diretório - MELHORADO PARA WINSRV"""
        try:
            # Procura arquivos de versão - EXPANDIDO
            arquivos_versao = [
                'versao.txt', 'version.txt', 'sic.ini', 'winsrv.ini',
                'config.ini', 'setup.ini', 'sistema.ini', 'about.txt',
                'readme.txt', 'leiame.txt'
            ]
            
            # Procura nos arquivos
            for arquivo in arquivos_versao:
                caminho = os.path.join(diretorio, arquivo)
                if os.path.exists(caminho):
                    try:
                        with open(caminho, 'r', encoding='latin1') as f:
                            conteudo = f.read()
                            
                        # Procura padrões de versão específicos
                        if '5.1.14' in conteudo:
                            return "5.1.14 ✅"
                        elif '5.1.13' in conteudo:
                            return "5.1.13"
                        elif '5.1.12' in conteudo:
                            return "5.1.12"
                        elif '5.1' in conteudo:
                            return "5.1.x"
                        elif any(v in conteudo for v in ['5.0', '4.9', '4.8']):
                            for linha in conteudo.split('\n'):
                                if any(v in linha for v in ['5.0', '4.9', '4.8', '5.1']):
                                    return linha.strip()[:50]
                    except:
                        continue
            
            # Verifica executáveis por tamanho/data (método alternativo)
            try:
                executaveis = [f for f in os.listdir(diretorio) if f.lower().endswith('.exe')]
                if executaveis:
                    exe_principal = executaveis[0]
                    caminho_exe = os.path.join(diretorio, exe_principal)
                    stat = os.stat(caminho_exe)
                    
                    # Tamanhos típicos do SIC 5.1.14
                    tamanho_mb = stat.st_size / (1024 * 1024)
                    
                    if 2 <= tamanho_mb <= 15:  # SIC 5.1.x geralmente entre 2-15MB
                        return f"5.1.x (exe {tamanho_mb:.1f}MB)"
            except:
                pass
            
            return "Versão não identificada"
            
        except Exception as e:
            return f"Erro: {e}"
    
    def buscar_arquivos_config(self):
        """Busca arquivos de configuração do SIC - INCLUINDO WINSRV"""
        try:
            # Locais comuns de arquivos de configuração - EXPANDIDO
            locais_busca = [
                "C:\\WinSRV",                           # ← ADICIONADO!
                "C:\\WINSRV",                           # ← ADICIONADO!
                "C:\\SIC",
                "C:\\SICNET", 
                "C:\\Windows",
                "C:\\",
                "D:\\WinSRV",                           # ← ADICIONADO!
                os.path.expanduser("~\\Documents"),
                os.path.expanduser("~\\AppData\\Local"),
                os.path.expanduser("~\\AppData\\Roaming")
            ]
            
            arquivos_config = [
                'sic.ini', 'sicnet.ini', 'config.ini', 'winsrv.ini',  # ← ADICIONADO winsrv.ini
                'database.ini', 'conexao.ini', 'bd.ini', 'srv.ini',
                'sistema.ini', 'configuracao.ini'
            ]
            
            configs_encontradas = []
            
            print("   🔍 Procurando em diretórios...")
            
            for local in locais_busca:
                print(f"      {local}...", end="")
                
                if not os.path.exists(local):
                    print(" ❌")
                    continue
                
                print(" ✅")
                    
                for arquivo in arquivos_config:
                    caminho_completo = os.path.join(local, arquivo)
                    
                    if os.path.exists(caminho_completo):
                        try:
                            config = configparser.ConfigParser()
                            config.read(caminho_completo, encoding='latin1')
                            
                            config_dict = {}
                            for secao in config.sections():
                                config_dict[secao] = dict(config[secao])
                            
                            if config_dict:
                                config_info = {
                                    'arquivo': caminho_completo,
                                    'configuracoes': config_dict
                                }
                                configs_encontradas.append(config_info)
                                
                                print(f"         ✅ {arquivo} encontrado!")
                                
                                # Mostra configurações relevantes
                                for secao, valores in config_dict.items():
                                    if any(key.lower() in ['server', 'database', 'usuario'] for key in valores.keys()):
                                        print(f"            [{secao}] - {len(valores)} configurações")
                        
                        except Exception as e:
                            print(f"         ⚠️ Erro ao ler {arquivo}: {e}")
            
            if not configs_encontradas:
                print("   ❌ Nenhum arquivo de configuração encontrado")
            
            return configs_encontradas
            
        except Exception as e:
            print(f"   ❌ Erro ao buscar arquivos: {e}")
            return []
    
    def escanear_rede_sql(self):
        """Escaneia a rede procurando servidores SQL"""
        try:
            # Faixas de IP comuns
            faixas_ip = [
                "192.168.1.{}", "192.168.0.{}", "192.168.2.{}",
                "10.0.0.{}", "10.0.1.{}", "172.16.0.{}"
            ]
            
            self.servidores_encontrados = []
            
            print("   🔍 Escaneando portas SQL (1433)...")
            print("      (Isso pode demorar alguns segundos...)")
            
            # Primeiro testa localhost
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('127.0.0.1', 1433))
                sock.close()
                
                if result == 0:
                    self.servidores_encontrados.append('127.0.0.1')
                    print(f"      ✅ SQL Server LOCAL encontrado: 127.0.0.1")
            except:
                pass
            
            # Depois testa IPs da rede
            for faixa in faixas_ip[:2]:  # Limita a 2 faixas para ser mais rápido
                print(f"      Testando faixa {faixa.format('x')}...")
                
                for i in [1, 100, 101, 102, 200, 254]:  # IPs mais comuns para servidores
                    ip = faixa.format(i)
                    
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex((ip, 1433))
                        sock.close()
                        
                        if result == 0:
                            self.servidores_encontrados.append(ip)
                            print(f"      ✅ Servidor SQL encontrado: {ip}")
                    except:
                        continue
            
            if not self.servidores_encontrados:
                print("   ❌ Nenhum servidor SQL encontrado na rede")
                print("   💡 Dica: O SQL Server pode estar em porta diferente ou firewall ativo")
            else:
                print(f"   ✅ Total: {len(self.servidores_encontrados)} servidores encontrados")
            
        except Exception as e:
            print(f"   ❌ Erro no escaneamento: {e}")
    
    def testar_conexoes_encontradas(self):
        """Testa conexões com as configurações encontradas"""
        conexoes_validas = []
        
        if not self.servidores_encontrados:
            print("   ⚠️ Nenhum servidor para testar")
            return conexoes_validas
        
        # Combinações comuns de usuário/senha para SIC 5.1.14
        credenciais_teste = [
            ('sa', ''),
            ('sa', 'sa'),
            ('sa', '123'),
            ('sa', 'sic'),
            ('sa', 'admin'),
            ('sic', 'sic'),
            ('admin', 'admin'),
            ('sicuser', 'sic123'),
            ('usuario', 'senha'),
            ('srv', 'srv')
        ]
        
        # Nomes de banco comuns para SIC 5.1.14
        bancos_teste = ['SIC', 'SICNET', 'SIC514', 'DADOS', 'SISTEMA', 'WINSRV']
        
        for servidor in self.servidores_encontrados:
            print(f"   🔗 Testando servidor: {servidor}")
            
            for usuario, senha in credenciais_teste:
                for banco in bancos_teste:
                    try:
                        # Tenta diferentes drivers
                        drivers = [
                            "SQL Server",
                            "ODBC Driver 17 for SQL Server",
                            "SQL Server Native Client 11.0"
                        ]
                        
                        for driver in drivers:
                            try:
                                conn_str = f"""
                                DRIVER={{{driver}}};
                                SERVER={servidor};
                                DATABASE={banco};
                                UID={usuario};
                                PWD={senha};
                                Connection Timeout=5;
                                """
                                
                                conn = pyodbc.connect(conn_str)
                                cursor = conn.cursor()
                                
                                # Verifica se tem tabelas do SIC
                                cursor.execute("""
                                    SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                                    WHERE TABLE_NAME LIKE '%PROD%' OR TABLE_NAME LIKE '%ITEM%'
                                """)
                                
                                tabelas_produtos = cursor.fetchone()[0]
                                
                                if tabelas_produtos > 0:
                                    # Detecta versão SIC
                                    versao_sic = self.detectar_versao_banco(cursor)
                                    
                                    # Lista algumas tabelas
                                    cursor.execute("""
                                        SELECT TOP 5 TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
                                        WHERE TABLE_TYPE = 'BASE TABLE'
                                        ORDER BY TABLE_NAME
                                    """)
                                    
                                    tabelas = [row[0] for row in cursor.fetchall()]
                                    
                                    conexao_valida = {
                                        'servidor': servidor,
                                        'banco': banco,
                                        'usuario': usuario,
                                        'senha': senha,
                                        'driver': driver,
                                        'tabelas_produtos': tabelas_produtos,
                                        'versao_sic': versao_sic,
                                        'tabelas_exemplo': tabelas
                                    }
                                    
                                    conexoes_validas.append(conexao_valida)
                                    
                                    print(f"      ✅ CONEXÃO VÁLIDA! 🎉")
                                    print(f"         Banco: {banco}")
                                    print(f"         Usuário: {usuario}")
                                    print(f"         Driver: {driver}")
                                    print(f"         Tabelas produtos: {tabelas_produtos}")
                                    print(f"         Versão SIC: {versao_sic}")
                                    print(f"         Tabelas: {', '.join(tabelas)}")
                                
                                conn.close()
                                break  # Se conectou, não testa outros drivers
                                
                            except pyodbc.Error:
                                continue
                        
                    except:
                        continue
        
        if not conexoes_validas:
            print("   ❌ Nenhuma conexão válida encontrada")
            print("   💡 Dicas:")
            print("      • Verifique se o SQL Server está rodando")
            print("      • Confirme usuário e senha")
            print("      • Teste autenticação Windows")
        
        return conexoes_validas
    
    def detectar_versao_banco(self, cursor):
        """Detecta versão do SIC pelo banco"""
        try:
            # Procura tabelas específicas do SIC 5.1.14
            tabelas_514 = ['VERSAO', 'VERSION', 'SISTEMA', 'CONFIG']
            
            for tabela in tabelas_514:
                try:
                    cursor.execute(f"SELECT TOP 1 * FROM {tabela}")
                    dados = cursor.fetchone()
                    if dados and '5.1.14' in str(dados):
                        return "5.1.14 ✅"
                    elif dados and '5.1' in str(dados):
                        return "5.1.x"
                except:
                    continue
            
            # Verifica estrutura típica do SIC 5.1.14
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'PRODUTOS' AND COLUMN_NAME IN ('CODIGO', 'DESCRICAO')
            """)
            
            colunas_produtos = cursor.fetchone()[0]
            
            if colunas_produtos >= 2:
                return "5.1.x (estrutura detectada)"
            
            return "Versão não identificada"
            
        except:
            return "Erro na detecção"
    
    def gerar_relatorio(self, instalacao_local, config_registro, config_arquivos, conexoes_validas):
        """Gera relatório final da detecção"""
        print("📋 RELATÓRIO DE DETECÇÃO SIC")
        print("=" * 60)
        
        if instalacao_local:
            print("✅ INSTALAÇÃO LOCAL DETECTADA:")
            for instalacao in instalacao_local:
                print(f"   📁 {instalacao['diretorio']}")
                print(f"      Versão: {instalacao['versao']}")
                if instalacao['executaveis']:
                    print(f"      Executáveis: {', '.join(instalacao['executaveis'])}")
                if instalacao['configuracoes']:
                    print(f"      Configs: {len(instalacao['configuracoes'])} arquivos")
        
        if conexoes_validas:
            print("\n✅ CONEXÕES SIC VÁLIDAS:")
            for i, conexao in enumerate(conexoes_validas, 1):
                print(f"   {i}. 🎯 RECOMENDADA:")
                print(f"      Servidor: {conexao['servidor']}")
                print(f"      Banco: {conexao['banco']}")
                print(f"      Usuário: {conexao['usuario']}")
                print(f"      Senha: {conexao['senha']}")
                print(f"      Versão: {conexao['versao_sic']}")
                print(f"      Produtos: {conexao['tabelas_produtos']} tabelas")
        
        if not instalacao_local and not conexoes_validas:
            print("❌ NENHUM SIC DETECTADO")
            print("   💡 Verificações:")
            print("   • SIC instalado em C:\\WinSRV ?")
            print("   • SQL Server rodando?")
            print("   • Firewall bloqueando porta 1433?")
        
        print("\n💡 PRÓXIMOS PASSOS:")
        if conexoes_validas:
            melhor_conexao = conexoes_validas[0]
            print("   ✅ Configure automaticamente:")
            print(f"      servidor = {melhor_conexao['servidor']}")
            print(f"      banco = {melhor_conexao['banco']}")
            print(f"      usuario = {melhor_conexao['usuario']}")
            print(f"      senha = {melhor_conexao['senha']}")
            
            # Salva configuração automaticamente
            self.salvar_configuracao_automatica(melhor_conexao)
        else:
            print("   1. Verifique pasta C:\\WinSRV")
            print("   2. Confirme se SQL Server está ativo")
            print("   3. Use importação por arquivo como alternativa")
    
    def salvar_configuracao_automatica(self, conexao):
        """Salva configuração detectada automaticamente"""
        try:
            config_content = f"""[SIC]
servidor = {conexao['servidor']}
porta = 1433
banco = {conexao['banco']}
usuario = {conexao['usuario']}
senha = {conexao['senha']}

[SIC_TABELAS]
produtos = PRODUTOS
estoque = ESTOQUE
categorias = CATEGORIAS
marcas = MARCAS
clientes = CLIENTES

[FRETE]
valor_por_kg = 3.50
frete_minimo = 15.00

[EMPRESA]
nome = SUA EMPRESA LTDA
endereco = Rua da Empresa, 123
cidade = Sua Cidade - SP
telefone = (11) 1234-5678
cnpj = 00.000.000/0001-00
"""
            
            os.makedirs('dados', exist_ok=True)
            
            with open('dados/config.ini', 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            print("   ✅ Configuração salva em: dados/config.ini")
            
        except Exception as e:
            print(f"   ⚠️ Erro ao salvar configuração: {e}")

def executar_deteccao_completa():
    """Executa detecção completa e salva configuração"""
    detector = DetectorSIC()
    return detector.detectar_sic_completo()

if __name__ == "__main__":
    print("🚀 DETECTOR AUTOMÁTICO SIC 5.1.14")
    print("👤 Matheus-TestUser1 - 2025-07-13 18:57:25")
    print("📁 Incluindo verificação em C:\\winsrv")
    print()
    
    resultado = executar_deteccao_completa()