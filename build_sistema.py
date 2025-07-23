import os
import subprocess
import shutil
import sys
from datetime import datetime

def build_sistema_pdv():
    """Script completo para compilar Sistema PDV"""
    
    print("🚀 COMPILADOR SISTEMA PDV")
    print("=" * 50)
    
    # Verificar se main.py existe
    if not os.path.exists("main.py"):
        print("❌ main.py não encontrado!")
        return False
    
    # Criar ícone
    print("🎨 Criando ícone...")
    try:
        exec(open('criar_icone.py').read())
    except:
        print("⚠️ Ícone padrão será usado")
    
    # Verificar dependências
    print("\n📦 Verificando dependências...")
    dependencias = ['pyinstaller', 'pyodbc', 'pandas', 'openpyxl', 'pillow']
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - Instalando...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep])
    
    # Limpar builds anteriores
    print("\n🧹 Limpando builds anteriores...")
    for pasta in ['build', 'dist', '__pycache__']:
        if os.path.exists(pasta):
            shutil.rmtree(pasta)
            print(f"🗑️ Removido: {pasta}")
    
    # Comandos de compilação
    print("\n🔨 Compilando aplicação...")
    
    cmd_basico = [
        'pyinstaller',
        '--onefile',           # Um arquivo só
        '--windowed',          # Sem console
        '--name', 'SistemaPDV', # Nome do EXE
        '--distpath', 'dist',   # Pasta de saída
        '--workpath', 'build',  # Pasta temporária
        'main.py'
    ]
    
    # Adicionar ícone se existir
    if os.path.exists('icone.ico'):
        cmd_basico.extend(['--icon', 'icone.ico'])
    
    # Executar compilação
    try:
        resultado = subprocess.run(cmd_basico, capture_output=True, text=True)
        
        if resultado.returncode == 0:
            print("✅ Compilação bem-sucedida!")
            
            # Verificar se EXE foi criado
            exe_path = os.path.join('dist', 'SistemaPDV.exe')
            if os.path.exists(exe_path):
                tamanho = os.path.getsize(exe_path) / (1024*1024)  # MB
                print(f"📁 EXE criado: {exe_path}")
                print(f"📏 Tamanho: {tamanho:.1f} MB")
                
                # Criar pasta distribuição
                print("\n📦 Criando pacote distribuição...")
                criar_pacote_distribuicao()
                
                return True
            else:
                print("❌ EXE não foi criado!")
                return False
        else:
            print("❌ Erro na compilação:")
            print(resultado.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro durante compilação: {e}")
        return False

def criar_pacote_distribuicao():
    """Criar pacote completo para distribuição"""
    try:
        # Criar pasta SistemaPDV_v1.0
        versao = datetime.now().strftime("%Y%m%d")
        pasta_dist = f"SistemaPDV_v{versao}"
        
        if os.path.exists(pasta_dist):
            shutil.rmtree(pasta_dist)
        
        os.makedirs(pasta_dist)
        
        # Copiar EXE
        shutil.copy2('dist/SistemaPDV.exe', pasta_dist)
        
        # Criar pastas necessárias
        os.makedirs(f"{pasta_dist}/dados", exist_ok=True)
        os.makedirs(f"{pasta_dist}/relatorios", exist_ok=True)
        os.makedirs(f"{pasta_dist}/templates", exist_ok=True)
        
        # Criar README
        readme_content = f"""
🌲 MADEIREIRA MARIA LUIZA - SISTEMA PDV
======================================

📦 Versão: {versao}
🐍 Python: {sys.version.split()[0]}
📅 Compilado: {datetime.now().strftime('%d/%m/%Y %H:%M')}

🏪 EMPRESA: MADEIREIRA MARIA LUIZA
📍 Endereço: Rua das Madeiras, 456
📞 Telefone: (11) 9999-8888

🚀 INSTALAÇÃO:
1. Extrair pasta para local desejado
2. Executar SistemaPDV.exe
3. Configurar conexão SIC na aba "Configurações"
4. Testar conexão
5. Sincronizar dados

🔧 SUPORTE:
Sistema desenvolvido para MADEIREIRA MARIA LUIZA
Integração com SIC - Gestão de Produtos
    """
        
        with open(f"{pasta_dist}/README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Criar arquivo de configuração exemplo
        config_exemplo = """{
    "servidor": "localhost\\\\SQLEXPRESS",
    "database": "SIC", 
    "usuario": "sa",
    "senha": ""
}"""
        
        with open(f"{pasta_dist}/dados/config_exemplo.json", 'w') as f:
            f.write(config_exemplo)
        
        print(f"📦 Pacote criado: {pasta_dist}/")
        print("✅ Pronto para distribuição!")
        
    except Exception as e:
        print(f"❌ Erro criar pacote: {e}")

if __name__ == "__main__":
    sucesso = build_sistema_pdv()
    
    if sucesso:
        print("\n" + "="*50)
        print("🎉 COMPILAÇÃO CONCLUÍDA COM SUCESSO!")
        print("📂 Verificar pasta 'SistemaPDV_v[data]'")
        print("🚀 Sistema pronto para distribuição!")
    else:
        print("\n❌ Falha na compilação!")
    
    input("\nPressione Enter para sair...")