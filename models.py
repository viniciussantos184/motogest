"""Modelos (tabelas) do sistema MotoGest, mapeados com SQLAlchemy."""
from datetime import date

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

db = SQLAlchemy()

FORMAS_PAGAMENTO = ["Dinheiro", "Pix", "Cartão", "Financiamento", "Consórcio"]


class Marca(db.Model):
    __tablename__ = "marcas"

    id_marca = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    pais_origem = db.Column(db.String(50))

    motos = db.relationship("Moto", back_populates="marca")


class Moto(db.Model):
    """Entidade principal do sistema (CRUD completo)."""
    __tablename__ = "motos"
    __table_args__ = (
        CheckConstraint("preco > 0", name="chk_moto_preco"),
        CheckConstraint("estoque >= 0", name="chk_moto_estoque"),
        CheckConstraint("cilindrada > 0", name="chk_moto_cilindrada"),
    )

    id_moto = db.Column(db.Integer, primary_key=True)
    id_marca = db.Column(db.Integer, db.ForeignKey("marcas.id_marca"), nullable=False)
    modelo = db.Column(db.String(80), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    cilindrada = db.Column(db.Integer, nullable=False)
    cor = db.Column(db.String(30))
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=0)

    marca = db.relationship("Marca", back_populates="motos")
    itens = db.relationship("ItemVenda", back_populates="moto")


class Cliente(db.Model):
    __tablename__ = "clientes"

    id_cliente = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, unique=True)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cidade = db.Column(db.String(60))

    vendas = db.relationship("Venda", back_populates="cliente")


class Vendedor(db.Model):
    __tablename__ = "vendedores"
    __table_args__ = (
        CheckConstraint("comissao_pct >= 0 AND comissao_pct <= 100", name="chk_vendedor_comissao"),
    )

    id_vendedor = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    comissao_pct = db.Column(db.Numeric(5, 2), nullable=False, default=0)

    vendas = db.relationship("Venda", back_populates="vendedor")


class Venda(db.Model):
    __tablename__ = "vendas"

    id_venda = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey("clientes.id_cliente"), nullable=False)
    id_vendedor = db.Column(db.Integer, db.ForeignKey("vendedores.id_vendedor"), nullable=False)
    data_venda = db.Column(db.Date, nullable=False, default=date.today)
    forma_pagamento = db.Column(db.Enum(*FORMAS_PAGAMENTO, name="forma_pagamento"), nullable=False)

    cliente = db.relationship("Cliente", back_populates="vendas")
    vendedor = db.relationship("Vendedor", back_populates="vendas")
    itens = db.relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(item.subtotal for item in self.itens)


class ItemVenda(db.Model):
    __tablename__ = "itens_venda"
    __table_args__ = (
        CheckConstraint("quantidade > 0", name="chk_item_quantidade"),
        CheckConstraint("preco_unitario > 0", name="chk_item_preco"),
    )

    id_item = db.Column(db.Integer, primary_key=True)
    id_venda = db.Column(db.Integer, db.ForeignKey("vendas.id_venda", ondelete="CASCADE"), nullable=False)
    id_moto = db.Column(db.Integer, db.ForeignKey("motos.id_moto"), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)

    venda = db.relationship("Venda", back_populates="itens")
    moto = db.relationship("Moto", back_populates="itens")

    @property
    def subtotal(self):
        return self.quantidade * self.preco_unitario
