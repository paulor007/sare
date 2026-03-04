"""
Modelos do banco de dados — SQLAlchemy ORM.

Tabelas: Vendedor, Produto, Venda
Empresa fictícia: TechNova Soluções
"""

from sqlalchemy import (create_engine, Column, Integer, String, Float, Date, ForeignKey)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from src.config import DB_URL

# ── Engine e Session ──
engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# ══════════════════════════════════════════
# MODELOS (cada classe = 1 tabela)
# ══════════════════════════════════════════

class Vendedor(Base):
    """Vendedores da empresa."""
    __tablename__ = "vendedores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False)
    departamento = Column(String(50), nullable=False)

    # Relacionamento: um vendedor tem muitas vendas
    vendas = relationship("Venda", back_populates="vendedor")

    def __repr__(self):
        return f"<Vendedor(id={self.id}, nome='{self.nome}')>"
    
class Produto(Base):
    """Produtos/serviços oferecidos."""
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    categoria = Column(String(50), nullable=False)
    preco = Column(Float, nullable=False)

    # Relacionamento
    vendas = relationship("Venda", back_populates="produto")

    def __repr__(self):
        return f"<Produto(id={self.id}, nome='{self.nome}', preco={self.preco})>"
    
class Venda(Base):
    """Registro de vendas."""
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    data = Column(Date, nullable=False)
    vendedor_id = Column(Integer, ForeignKey("vendedores.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False, default=1)
    valor_unitario = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)
    status = Column(String(20), nullable=False, default="concluida")

    # Relacionamentos
    vendedor = relationship("Vendedor", back_populates="vendas")
    produto = relationship("Produto", back_populates="vendas")

    def __repr__(self):
        return f"<Venda(id={self.id}, valor_total={self.valor_total})>"
    
def criar_tabelas():
    """Cria todas as tabelas no banco."""
    Base.metadata.create_all(engine)

def get_session():
    """Retorna uma nova sessão do banco."""
    return Session()