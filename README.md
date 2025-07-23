# Sistema PDV - Madeireira Maria Luiza

Sistema de PDV (Ponto de Venda) integrado ao SIC para gestão completa da Madeireira Maria Luiza.

## 🌟 Funcionalidades

### 🔌 Integração com SIC
- ✅ Conexão segura com SQL Server do SIC
- ✅ Sincronização automática de produtos
- ✅ Modo offline com cache local SQLite
- ✅ Pool de conexões e tratamento de erros

### 📦 Gestão de Produtos
- ✅ Classes para produtos e estoque
- ✅ Importação automática do SIC
- ✅ Cache local para funcionamento offline
- ✅ Sincronização bidirecional

### 📊 Sistema de Relatórios
- ✅ Geração de relatórios em Excel e TXT
- ✅ Relatórios de produtos, estoque e preços
- ✅ Análises de vendas e movimento
- ✅ Templates personalizáveis

### 🖨️ Geração de Talões
- ✅ Talões de balcão para clientes e loja
- ✅ Templates customizáveis HTML/CSS
- ✅ Formatação profissional
- ✅ Exportação em múltiplos formatos

### 💾 Banco de Dados Local
- ✅ SQLite para cache e modo offline
- ✅ Estrutura espelhada do SIC
- ✅ Sincronização inteligente
- ✅ Sistema de backup automático

### 🎨 Sistema de Templates
- ✅ Templates personalizáveis para relatórios
- ✅ Templates para talões e documentos
- ✅ Engine Jinja2 para máxima flexibilidade
- ✅ Templates responsivos

## 🚀 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- SQL Server com SIC instalado
- Driver ODBC para SQL Server

### Dependências
```bash
pip install -r requirements.txt
```

### Dependências Principais
- `pyodbc` - Conexão SQL Server
- `openpyxl` - Geração de relatórios Excel
- `jinja2` - Sistema de templates
- `pyyaml` - Configuração YAML
- `sqlalchemy` - ORM e abstração de banco

## ⚙️ Configuração

### 1. Configuração do Banco SIC
Edite o arquivo `config/database.yaml`:

```yaml
sic:
  servidor: "SEU_SERVIDOR\\SQLEXPRESS"
  banco: "SIC"
  usuario: "sa"
  senha: "SUA_SENHA"
  porta: 1433
```

### 2. Configuração da Empresa
Edite o arquivo `config/app_config.yaml`:

```yaml
business:
  nome_empresa: "SUA EMPRESA"
  endereco: "SEU ENDEREÇO"
  cidade: "SUA CIDADE"
  telefone: "SEU TELEFONE"
  cnpj: "SEU CNPJ"
```

### 3. Configuração de Interface
Edite o arquivo `config/ui_config.yaml` para personalizar a interface.

## 📁 Estrutura do Projeto

```
minisistema/
├── src/                     # Código fonte principal
│   ├── database/           # Módulos de banco de dados
│   │   ├── sic_connection.py    # Conexão com SIC
│   │   ├── local_db.py          # Banco local SQLite
│   │   └── models.py            # Modelos de dados
│   ├── products/           # Gestão de produtos
│   │   ├── product_manager.py   # Gerenciador de produtos
│   │   ├── sync_manager.py      # Sincronização
│   │   └── inventory.py         # Controle de estoque
│   ├── reports/            # Sistema de relatórios
│   │   ├── report_generator.py  # Gerador principal
│   │   ├── excel_reports.py     # Relatórios Excel
│   │   └── txt_reports.py       # Relatórios TXT
│   ├── receipts/           # Geração de talões
│   │   ├── receipt_generator.py # Gerador de talões
│   │   └── templates.py         # Gerenciador de templates
│   ├── templates/          # Sistema de templates
│   │   └── template_manager.py  # Gerenciador central
│   ├── ui/                 # Interface de usuário
│   └── utils/              # Utilitários
│       ├── config.py           # Gerenciador de configuração
│       ├── logger.py           # Sistema de logs
│       └── helpers.py          # Funções auxiliares
├── config/                 # Arquivos de configuração
├── dados/                  # Dados e cache local
├── logs/                   # Arquivos de log
├── output/                 # Relatórios e talões gerados
├── templates/              # Templates customizáveis
├── requirements.txt        # Dependências Python
├── main.py                # Arquivo principal
└── README.md              # Este arquivo
```

## 🔧 Uso do Sistema

### Iniciando o Sistema
```bash
python main.py
```

### Funcionalidades Principais

#### 1. Gestão de Produtos
```python
from src.products import ProductManager

# Inicializar gerenciador
product_manager = ProductManager()

# Obter todos os produtos
produtos = product_manager.get_all_products()

# Buscar produto específico
produto = product_manager.get_product_by_code("001")

# Atualizar preço
product_manager.update_product_price("001", 25.50)
```

#### 2. Geração de Relatórios
```python
from src.reports import ReportGenerator
from src.database import ReportConfig

# Configurar relatório
config = ReportConfig(
    tipo='excel',
    titulo='Relatório de Produtos',
    filtros={'categoria': 'Madeiras'}
)

# Gerar relatório
report_gen = ReportGenerator(product_manager)
resultado = report_gen.generate_products_report(config)
```

#### 3. Geração de Talões
```python
from src.receipts import ReceiptGenerator

# Criar talão
receipt_gen = ReceiptGenerator()

items = [
    {
        'codigo': '001',
        'descricao': 'Madeira Peroba',
        'quantidade': 10,
        'preco_unitario': 25.50,
        'peso': 15.0
    }
]

# Gerar talão
receipt_data = receipt_gen.create_receipt(
    cliente_nome='João Silva',
    items=items,
    observacoes='Entrega em 2 dias'
)

# Gerar HTML
html_result = receipt_gen.generate_receipt_html(
    receipt_data['receipt'], 
    tipo='cliente'
)
```

#### 4. Sincronização
```python
from src.products import SyncManager

# Inicializar sincronização
sync_manager = SyncManager(product_manager)

# Iniciar sincronização automática
sync_manager.start_auto_sync()

# Forçar sincronização manual
resultado = sync_manager.force_sync()
```

## 📊 Tipos de Relatórios Disponíveis

1. **Relatório de Produtos** - Lista completa com preços e estoque
2. **Relatório de Estoque** - Análise detalhada do estoque
3. **Produtos em Falta** - Alertas de estoque baixo
4. **Lista de Preços** - Para clientes
5. **Relatório por Categoria** - Agrupado por categorias
6. **Sugestões de Reposição** - Baseado em movimento

## 🎨 Personalização de Templates

### Templates de Talões
Os templates estão em `src/receipts/templates/` e usam Jinja2:

```html
<!-- talao_cliente.html -->
<div class="receipt-container">
    <h1>{{ empresa.nome }}</h1>
    <p>Cliente: {{ receipt.cliente_nome }}</p>
    
    {% for item in receipt.items %}
    <div class="item">
        {{ item.descricao }} - R$ {{ item.subtotal }}
    </div>
    {% endfor %}
    
    <div class="total">
        Total: R$ {{ receipt.total }}
    </div>
</div>
```

### Templates de Relatórios
Personalizáveis via `src/templates/template_manager.py`

## 🔒 Segurança

- Conexões criptografadas com SQL Server
- Validação de entrada de dados
- Sistema de logs detalhado
- Backup automático do banco local

## 📝 Logs

Os logs são armazenados em `logs/` com rotação automática:
- `pdv_system_YYYYMMDD.log` - Logs gerais
- `pdv_system_errors_YYYYMMDD.log` - Apenas erros

## 🔄 Modo Offline

O sistema funciona offline quando o SIC não está disponível:
- Cache local em SQLite
- Sincronização automática quando reconectado
- Controle de movimentos pendentes

## 🆘 Solução de Problemas

### Erro de Conexão com SIC
1. Verifique se o SQL Server está rodando
2. Confirme as credenciais em `config/database.yaml`
3. Teste a conectividade de rede

### Erro de Dependências
```bash
pip install --upgrade -r requirements.txt
```

### Problemas de Performance
- Ajuste `sync_interval_minutes` em `config/app_config.yaml`
- Considere aumentar `timeout_seconds`

## 📞 Suporte

Para suporte técnico:
- Email: suporte@madeireiramariluiza.com.br
- Telefone: (81) 3011-5515

## 📄 Licença

Este sistema foi desenvolvido especificamente para a Madeireira Maria Luiza.

## 🔄 Atualizações

### Versão 1.0.0 (Atual)
- ✅ Sistema completo implementado
- ✅ Integração com SIC
- ✅ Relatórios profissionais
- ✅ Geração de talões
- ✅ Modo offline
- ✅ Sistema de templates

### Próximas Funcionalidades
- Interface gráfica completa
- Módulo de vendas
- Controle de clientes
- Dashboard analítico
- Integração com impressoras térmicas
- App mobile para consultas