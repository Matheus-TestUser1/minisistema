# 🌲 Sistema PDV - Madeireira Maria Luiza

## 🚀 Guia de Início Rápido

### 1. **Instalação**
```bash
# Clone o repositório
git clone https://github.com/Matheus-TestUser1/minisistema.git
cd minisistema

# Instale as dependências
pip install -r requirements.txt
```

### 2. **Primeira Execução**
```bash
# Teste o sistema
python test_system.py

# Execute o sistema principal
python main.py
```

### 3. **Configuração Inicial**
1. **Abra o sistema** e clique em "⚙️ Config"
2. **Configure a conexão SIC**:
   - Servidor: `SEU_SERVIDOR\SQLEXPRESS`
   - Banco: `SIC` (ou seu nome)
   - Usuário/Senha conforme seu ambiente
3. **Configure os dados da empresa**
4. **Teste a conexão** com o botão "🧪 Testar Conexão"
5. **Salve as configurações**

### 4. **Funcionalidades Principais**

#### 📊 **Dashboard**
- Visão geral do sistema
- Status de sincronização
- Estatísticas rápidas
- Ações rápidas

#### 📦 **Gestão de Produtos**
- Busca e listagem de produtos
- Sincronização com SIC
- Atualização automática

#### 📋 **Relatórios**
- **6 tipos de relatórios disponíveis**:
  - Relatório de Produtos
  - Relatório de Estoque
  - Produtos em Falta
  - Lista de Preços
  - Relatório por Categoria
  - Sugestões de Reposição
- **Formatos**: Excel e TXT
- **Salvos em**: pasta `output/`

#### 🧾 **Talões**
- Talão do Cliente (via do cliente)
- Talão da Loja (controle interno)
- Templates HTML profissionais
- Cálculo automático de frete

#### 📊 **Controle de Estoque**
- Resumo detalhado
- Alertas de produtos em falta
- Exportação para CSV
- Análise por categoria

### 5. **Modo Offline**
- ✅ **Funciona sem conexão com SIC**
- ✅ **Cache local automático**
- ✅ **Sincronização quando reconectar**
- ✅ **Controle de movimentos pendentes**

### 6. **Arquivos e Pastas**

```
minisistema/
├── 📁 config/          # Configurações YAML
├── 📁 dados/           # Banco local e cache
├── 📁 logs/            # Logs do sistema
├── 📁 output/          # Relatórios e talões
├── 📁 src/             # Código fonte
├── 📄 main.py          # Executável principal
├── 📄 test_system.py   # Testes do sistema
└── 📄 README.md        # Documentação
```

### 7. **Problemas Comuns**

#### ❌ **Erro de Conexão SIC**
1. Verifique se o SQL Server está rodando
2. Confirme servidor/banco/credenciais
3. Teste conectividade de rede
4. Use modo offline temporariamente

#### ❌ **Erro de Dependências**
```bash
pip install --upgrade -r requirements.txt
```

#### ❌ **Interface não abre**
```bash
# Verifique se tem tkinter instalado
python -c "import tkinter"

# No Ubuntu/Debian
sudo apt-get install python3-tk
```

### 8. **Recursos Avançados**

#### 🎨 **Templates Personalizados**
- Templates em `src/receipts/templates/`
- Use Jinja2 para customização
- CSS integrado para estilos

#### 📊 **Logs Detalhados**
- Logs em `logs/pdv_system_YYYYMMDD.log`
- Erros em `logs/pdv_system_errors_YYYYMMDD.log`
- Rotação automática

#### ⚙️ **Configuração Avançada**
- Edite arquivos YAML em `config/`
- Configure frete, sincronização, UI
- Backup automático de configurações

### 9. **Suporte**
- 📧 Email: suporte@madeireiramariluiza.com.br
- 📞 Telefone: (81) 3011-5515
- 📝 Logs: Verifique pasta `logs/` para diagnóstico

---

## ✨ **Desenvolvido para Madeireira Maria Luiza**
*Sistema completo de PDV integrado ao SIC*