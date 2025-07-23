import subprocess
import sys
import os

def debug_compilacao():
    """Debug da compilação PyInstaller"""
    
    print("🔍 DIAGNÓSTICO COMPILAÇÃO")
    print("=" * 40)
    
    # Verificar main.py
    if not os.path.exists("main.py"):
        print("❌ main.py não encontrado!")
        return False
    
    print("✅ main.py encontrado")
    
    # Verificar PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller não instalado!")
        print("💡 Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    # Limpar builds anteriores
    print("\n🧹 Limpando builds anteriores...")
    for pasta in ["build", "dist"]:
        if os.path.exists(pasta):
            import shutil
            shutil.rmtree(pasta)
            print(f"🗑️ Removido: {pasta}")
    
    # Remover .spec antigos
    for arquivo in os.listdir("."):
        if arquivo.endswith(".spec"):
            os.remove(arquivo)
            print(f"🗑️ Removido: {arquivo}")
    
    print("\n🔨 Tentativa 1: Compilação básica...")
    try:
        resultado = subprocess.run([
            "pyinstaller", 
            "--onefile", 
            "main.py"
        ], capture_output=True, text=True, timeout=300)
        
        print("STDOUT:", resultado.stdout)
        if resultado.stderr:
            print("STDERR:", resultado.stderr)
        
        if os.path.exists("dist/main.exe"):
            print("✅ Sucesso! EXE criado em dist/main.exe")
            tamanho = os.path.getsize("dist/main.exe") / (1024*1024)
            print(f"📏 Tamanho: {tamanho:.1f} MB")
            return True
        else:
            print("❌ EXE não foi criado")
            
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout na compilação")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n🔨 Tentativa 2: Com console (debug)...")
    try:
        resultado = subprocess.run([
            "pyinstaller", 
            "--onefile", 
            "--console",
            "main.py"
        ], capture_output=True, text=True, timeout=300)
        
        print("STDOUT:", resultado.stdout)
        if resultado.stderr:
            print("STDERR:", resultado.stderr)
            
        if os.path.exists("dist/main.exe"):
            print("✅ Sucesso com console! Teste o EXE")
            return True
            
    except Exception as e:
        print(f"❌ Erro tentativa 2: {e}")
    
    print("\n💡 POSSÍVEIS SOLUÇÕES:")
    print("1. Verificar se Python está no PATH")
    print("2. Executar como administrador")
    print("3. Instalar Visual C++ Redistributable")
    print("4. Tentar compilação manual passo a passo")
    
    return False

if __name__ == "__main__":
    debug_compilacao()
    input("\nPressione Enter para sair...")