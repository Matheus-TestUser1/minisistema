"""
Data Models for PDV System
Defines product, movement and other data structures
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

@dataclass
class Product:
    """Product data model"""
    codigo: str
    descricao: str
    preco_venda: Decimal
    estoque_atual: int = 0
    categoria: Optional[str] = None
    marca: Optional[str] = None
    unidade: Optional[str] = 'UN'
    peso: Optional[Decimal] = None
    data_atualizacao: Optional[datetime] = None
    sincronizado: bool = True
    criado_em: Optional[datetime] = field(default_factory=datetime.now)
    atualizado_em: Optional[datetime] = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'codigo': self.codigo,
            'descricao': self.descricao,
            'preco_venda': float(self.preco_venda),
            'estoque_atual': self.estoque_atual,
            'categoria': self.categoria,
            'marca': self.marca,
            'unidade': self.unidade,
            'peso': float(self.peso) if self.peso else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            'sincronizado': self.sincronizado,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create from dictionary"""
        return cls(
            codigo=data['codigo'],
            descricao=data['descricao'],
            preco_venda=Decimal(str(data['preco_venda'])),
            estoque_atual=data.get('estoque_atual', 0),
            categoria=data.get('categoria'),
            marca=data.get('marca'),
            unidade=data.get('unidade', 'UN'),
            peso=Decimal(str(data['peso'])) if data.get('peso') else None,
            data_atualizacao=datetime.fromisoformat(data['data_atualizacao']) if data.get('data_atualizacao') else None,
            sincronizado=data.get('sincronizado', True),
            criado_em=datetime.fromisoformat(data['criado_em']) if data.get('criado_em') else datetime.now(),
            atualizado_em=datetime.fromisoformat(data['atualizado_em']) if data.get('atualizado_em') else datetime.now()
        )

@dataclass
class Movement:
    """Product movement data model"""
    tipo: str  # 'venda', 'entrada', 'saida'
    produto_codigo: str
    quantidade: int
    preco: Optional[Decimal] = None
    data_movimento: Optional[datetime] = field(default_factory=datetime.now)
    sincronizado: bool = False
    dados_extras: Optional[Dict[str, Any]] = None
    id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'tipo': self.tipo,
            'produto_codigo': self.produto_codigo,
            'quantidade': self.quantidade,
            'preco': float(self.preco) if self.preco else None,
            'data_movimento': self.data_movimento.isoformat() if self.data_movimento else None,
            'sincronizado': self.sincronizado,
            'dados_extras': self.dados_extras
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Movement':
        """Create from dictionary"""
        return cls(
            id=data.get('id'),
            tipo=data['tipo'],
            produto_codigo=data['produto_codigo'],
            quantidade=data['quantidade'],
            preco=Decimal(str(data['preco'])) if data.get('preco') else None,
            data_movimento=datetime.fromisoformat(data['data_movimento']) if data.get('data_movimento') else datetime.now(),
            sincronizado=data.get('sincronizado', False),
            dados_extras=data.get('dados_extras')
        )

@dataclass
class SyncStatus:
    """Synchronization status model"""
    ultima_sincronizacao: Optional[datetime] = None
    total_produtos: int = 0
    status: str = 'offline'  # 'online', 'offline', 'error', 'syncing'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ultima_sincronizacao': self.ultima_sincronizacao.isoformat() if self.ultima_sincronizacao else None,
            'total_produtos': self.total_produtos,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncStatus':
        """Create from dictionary"""
        return cls(
            ultima_sincronizacao=datetime.fromisoformat(data['ultima_sincronizacao']) if data.get('ultima_sincronizacao') else None,
            total_produtos=data.get('total_produtos', 0),
            status=data.get('status', 'offline')
        )

@dataclass
class ReceiptItem:
    """Receipt/Talao item model"""
    produto_codigo: str
    descricao: str
    quantidade: int
    preco_unitario: Decimal
    subtotal: Decimal
    peso: Optional[Decimal] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'produto_codigo': self.produto_codigo,
            'descricao': self.descricao,
            'quantidade': self.quantidade,
            'preco_unitario': float(self.preco_unitario),
            'subtotal': float(self.subtotal),
            'peso': float(self.peso) if self.peso else None
        }

@dataclass
class Receipt:
    """Receipt/Talao model"""
    cliente_nome: str
    items: list[ReceiptItem]
    subtotal: Decimal
    frete: Decimal
    total: Decimal
    data_emissao: Optional[datetime] = field(default_factory=datetime.now)
    numero: Optional[str] = None
    observacoes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'numero': self.numero,
            'cliente_nome': self.cliente_nome,
            'items': [item.to_dict() for item in self.items],
            'subtotal': float(self.subtotal),
            'frete': float(self.frete),
            'total': float(self.total),
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'observacoes': self.observacoes
        }

@dataclass
class ReportConfig:
    """Report configuration model"""
    tipo: str  # 'excel', 'txt', 'pdf'
    titulo: str
    filtros: Optional[Dict[str, Any]] = None
    template: Optional[str] = None
    campos: Optional[list[str]] = None
    formato_data: str = '%d/%m/%Y %H:%M'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'tipo': self.tipo,
            'titulo': self.titulo,
            'filtros': self.filtros,
            'template': self.template,
            'campos': self.campos,
            'formato_data': self.formato_data
        }