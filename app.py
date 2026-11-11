"""MotoGest - sistema de gestão para loja de motos (Trabalho N2).

Como executar:
    1. Crie o banco com o script database/loja_motos.sql
    2. Ajuste usuário e senha do MySQL em DATABASE_URL (abaixo)
    3. pip install -r requirements.txt
    4. python app.py   ->  http://127.0.0.1:5000
"""
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import (FORMAS_PAGAMENTO, Cliente, ItemVenda, Marca, Moto, Venda,
                    Vendedor, db)

app = Flask(__name__)
app.config["SECRET_KEY"] = "troque-esta-chave"

# Formato: mysql+pymysql://USUARIO:SENHA@SERVIDOR/BANCO
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "mysql+pymysql://root:root@localhost/loja_motos?charset=utf8mb4"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


# ---------------------------------------------------------------- utilidades
@app.template_filter("moeda")
def moeda(valor):
    """Formata um número como R$ 12.345,67."""
    texto = f"{Decimal(valor or 0):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


@app.template_filter("data_br")
def data_br(valor):
    return valor.strftime("%d/%m/%Y") if valor else ""


def para_decimal(texto):
    """Aceita '18990,00', '18.990,00' ou '18990.00'. Retorna None se inválido."""
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def para_inteiro(texto):
    try:
        return int((texto or "").strip())
    except ValueError:
        return None


def para_data(texto):
    try:
        return datetime.strptime(texto or "", "%Y-%m-%d").date()
    except ValueError:
        return None


# -------------------------------------------------------------------- início
@app.route("/")
def index():
    faturamento = db.session.query(
        func.coalesce(func.sum(ItemVenda.quantidade * ItemVenda.preco_unitario), 0)
    ).scalar()
    resumo = {
        "modelos": Moto.query.count(),
        "estoque": db.session.query(func.coalesce(func.sum(Moto.estoque), 0)).scalar(),
        "clientes": Cliente.query.count(),
        "vendas": Venda.query.count(),
        "faturamento": faturamento,
    }
    ultimas_vendas = Venda.query.order_by(Venda.data_venda.desc(), Venda.id_venda.desc()).limit(5).all()
    estoque_baixo = Moto.query.filter(Moto.estoque <= 1).order_by(Moto.estoque, Moto.modelo).all()
    return render_template("index.html", resumo=resumo, ultimas_vendas=ultimas_vendas,
                           estoque_baixo=estoque_baixo)


# ------------------------------------------------- MOTOS (entidade principal)
@app.route("/motos")
def listar_motos():
    """READ + busca por filtros (modelo, marca, faixa de preço, estoque)."""
    modelo = request.args.get("modelo", "").strip()
    id_marca = para_inteiro(request.args.get("marca"))
    preco_min = para_decimal(request.args.get("preco_min"))
    preco_max = para_decimal(request.args.get("preco_max"))
    so_estoque = request.args.get("so_estoque") == "1"

    consulta = Moto.query.join(Marca)
    if modelo:
        consulta = consulta.filter(Moto.modelo.ilike(f"%{modelo}%"))
    if id_marca:
        consulta = consulta.filter(Moto.id_marca == id_marca)
    if preco_min is not None:
        consulta = consulta.filter(Moto.preco >= preco_min)
    if preco_max is not None:
        consulta = consulta.filter(Moto.preco <= preco_max)
    if so_estoque:
        consulta = consulta.filter(Moto.estoque > 0)

    motos = consulta.order_by(Marca.nome, Moto.modelo).all()
    marcas = Marca.query.order_by(Marca.nome).all()
    return render_template("listar.html", motos=motos, marcas=marcas)


def ler_formulario_moto(moto):
    """Copia os campos do formulário para o objeto e devolve a lista de erros."""
    erros = []
    moto.modelo = request.form.get("modelo", "").strip()
    moto.cor = request.form.get("cor", "").strip() or None
    moto.id_marca = para_inteiro(request.form.get("id_marca"))
    moto.ano = para_inteiro(request.form.get("ano"))
    moto.cilindrada = para_inteiro(request.form.get("cilindrada"))
    moto.preco = para_decimal(request.form.get("preco"))
    moto.estoque = para_inteiro(request.form.get("estoque"))

    if not moto.modelo:
        erros.append("Informe o modelo.")
    if not moto.id_marca or not db.session.get(Marca, moto.id_marca):
        erros.append("Escolha uma marca.")
    if moto.ano is None or not 1950 <= moto.ano <= date.today().year + 1:
        erros.append("Ano inválido.")
    if moto.cilindrada is None or moto.cilindrada <= 0:
        erros.append("A cilindrada deve ser maior que zero.")
    if moto.preco is None or moto.preco <= 0:
        erros.append("O preço deve ser maior que zero.")
    if moto.estoque is None or moto.estoque < 0:
        erros.append("O estoque não pode ser negativo.")
    return erros


@app.route("/motos/cadastrar", methods=["GET", "POST"])
def cadastrar_moto():
    """CREATE"""
    moto = Moto(estoque=0)
    if request.method == "POST":
        with db.session.no_autoflush:
            erros = ler_formulario_moto(moto)
        if not erros:
            db.session.add(moto)
            db.session.commit()
            flash(f"Moto {moto.modelo} cadastrada.", "success")
            return redirect(url_for("listar_motos"))
        for erro in erros:
            flash(erro, "danger")
    marcas = Marca.query.order_by(Marca.nome).all()
    return render_template("cadastrar.html", moto=moto, marcas=marcas, editando=False)


@app.route("/motos/<int:id_moto>/editar", methods=["GET", "POST"])
def editar_moto(id_moto):
    """UPDATE"""
    moto = db.get_or_404(Moto, id_moto)
    if request.method == "POST":
        with db.session.no_autoflush:
            erros = ler_formulario_moto(moto)
        if not erros:
            db.session.commit()
            flash(f"Moto {moto.modelo} alterada.", "success")
            return redirect(url_for("listar_motos"))
        dados = {c.name: getattr(moto, c.name) for c in Moto.__table__.columns}
        db.session.rollback()
        moto = Moto(**dados)          # reexibe o que foi digitado, sem gravar
        for erro in erros:
            flash(erro, "danger")
    marcas = Marca.query.order_by(Marca.nome).all()
    return render_template("cadastrar.html", moto=moto, marcas=marcas, editando=True)


@app.route("/motos/<int:id_moto>/excluir", methods=["POST"])
def excluir_moto(id_moto):
    """DELETE - a chave estrangeira impede excluir moto que já foi vendida."""
    moto = db.get_or_404(Moto, id_moto)
    try:
        db.session.delete(moto)
        db.session.commit()
        flash(f"Moto {moto.modelo} excluída.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Esta moto já aparece em vendas e não pode ser excluída. "
              "Zere o estoque se ela saiu de linha.", "danger")
    return redirect(url_for("listar_motos"))


# ------------------------------------------------------------------ CLIENTES
@app.route("/clientes")
def listar_clientes():
    busca = request.args.get("busca", "").strip()
    consulta = Cliente.query
    if busca:
        consulta = consulta.filter(
            Cliente.nome.ilike(f"%{busca}%") | Cliente.cpf.ilike(f"%{busca}%")
            | Cliente.cidade.ilike(f"%{busca}%"))
    return render_template("clientes.html", clientes=consulta.order_by(Cliente.nome).all())


@app.route("/clientes/cadastrar", methods=["GET", "POST"])
@app.route("/clientes/<int:id_cliente>/editar", methods=["GET", "POST"])
def formulario_cliente(id_cliente=None):
    cliente = db.get_or_404(Cliente, id_cliente) if id_cliente else Cliente()
    if request.method == "POST":
        dados = {campo: request.form.get(campo, "").strip() or None
                 for campo in ("nome", "cpf", "telefone", "email", "cidade")}
        if not dados["nome"] or not dados["cpf"]:
            flash("Nome e CPF são obrigatórios.", "danger")
            return render_template("cliente_form.html", cliente=dados, editando=bool(id_cliente),
                                   id_cliente=id_cliente)
        for campo, valor in dados.items():
            setattr(cliente, campo, valor)
        try:
            db.session.add(cliente)
            db.session.commit()
            flash(f"Cliente {cliente.nome} salvo.", "success")
            return redirect(url_for("listar_clientes"))
        except IntegrityError:
            db.session.rollback()
            flash("Já existe um cliente com este CPF.", "danger")
            return render_template("cliente_form.html", cliente=dados, editando=bool(id_cliente),
                                   id_cliente=id_cliente)
    return render_template("cliente_form.html", cliente=cliente, editando=bool(id_cliente),
                           id_cliente=id_cliente)


@app.route("/clientes/<int:id_cliente>/excluir", methods=["POST"])
def excluir_cliente(id_cliente):
    cliente = db.get_or_404(Cliente, id_cliente)
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash(f"Cliente {cliente.nome} excluído.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Este cliente tem vendas registradas e não pode ser excluído.", "danger")
    return redirect(url_for("listar_clientes"))


# -------------------------------------------------------------------- VENDAS
@app.route("/vendas")
def listar_vendas():
    vendas = Venda.query.order_by(Venda.data_venda.desc(), Venda.id_venda.desc()).all()
    return render_template("vendas.html", vendas=vendas)


@app.route("/vendas/registrar", methods=["GET", "POST"])
def registrar_venda():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    vendedores = Vendedor.query.order_by(Vendedor.nome).all()
    motos = Moto.query.join(Marca).filter(Moto.estoque > 0).order_by(Marca.nome, Moto.modelo).all()

    if request.method == "POST":
        erros = []
        cliente = db.session.get(Cliente, para_inteiro(request.form.get("id_cliente")) or 0)
        vendedor = db.session.get(Vendedor, para_inteiro(request.form.get("id_vendedor")) or 0)
        forma = request.form.get("forma_pagamento")
        data_venda = para_data(request.form.get("data_venda"))
        if not cliente:
            erros.append("Escolha o cliente.")
        if not vendedor:
            erros.append("Escolha o vendedor.")
        if forma not in FORMAS_PAGAMENTO:
            erros.append("Escolha a forma de pagamento.")
        if not data_venda:
            erros.append("Informe a data da venda.")

        # soma as quantidades por moto (a mesma moto pode vir em duas linhas)
        pedido = {}
        for id_txt, qtd_txt in zip(request.form.getlist("id_moto"), request.form.getlist("quantidade")):
            id_moto = para_inteiro(id_txt)
            if not id_moto:
                continue
            qtd = para_inteiro(qtd_txt)
            if not qtd or qtd <= 0:
                erros.append("A quantidade deve ser pelo menos 1.")
                continue
            pedido[id_moto] = pedido.get(id_moto, 0) + qtd
        if not pedido:
            erros.append("Inclua pelo menos uma moto na venda.")

        itens = []
        for id_moto, qtd in pedido.items():
            moto = db.session.get(Moto, id_moto)
            if not moto:
                erros.append("Moto não encontrada.")
            elif qtd > moto.estoque:
                erros.append(f"Só há {moto.estoque} unidade(s) de {moto.modelo} em estoque.")
            else:
                itens.append((moto, qtd))

        if not erros:
            venda = Venda(cliente=cliente, vendedor=vendedor, forma_pagamento=forma,
                          data_venda=data_venda)
            for moto, qtd in itens:
                venda.itens.append(ItemVenda(moto=moto, quantidade=qtd, preco_unitario=moto.preco))
                moto.estoque -= qtd          # baixa no estoque
            db.session.add(venda)
            db.session.commit()
            flash(f"Venda nº {venda.id_venda} registrada.", "success")
            return redirect(url_for("listar_vendas"))
        for erro in erros:
            flash(erro, "danger")

    return render_template("venda_form.html", clientes=clientes, vendedores=vendedores,
                           motos=motos, formas=FORMAS_PAGAMENTO, hoje=date.today().isoformat())


@app.route("/vendas/<int:id_venda>/excluir", methods=["POST"])
def excluir_venda(id_venda):
    """Cancela a venda e devolve as motos ao estoque."""
    venda = db.get_or_404(Venda, id_venda)
    for item in venda.itens:
        item.moto.estoque += item.quantidade
    db.session.delete(venda)
    db.session.commit()
    flash(f"Venda nº {id_venda} cancelada e estoque devolvido.", "success")
    return redirect(url_for("listar_vendas"))


# ---------------------------------------------------------------- RELATÓRIOS
@app.route("/relatorios")
def relatorios():
    """Consultas com JOIN, filtradas por período."""
    inicio = para_data(request.args.get("inicio"))
    fim = para_data(request.args.get("fim"))
    valor_item = ItemVenda.quantidade * ItemVenda.preco_unitario

    def no_periodo(consulta):
        if inicio:
            consulta = consulta.filter(Venda.data_venda >= inicio)
        if fim:
            consulta = consulta.filter(Venda.data_venda <= fim)
        return consulta

    # 1) Vendas detalhadas: vendas + clientes + vendedores + itens_venda + motos + marcas
    detalhado = no_periodo(
        db.session.query(Venda.id_venda, Venda.data_venda, Cliente.nome.label("cliente"),
                         Vendedor.nome.label("vendedor"), Marca.nome.label("marca"),
                         Moto.modelo, ItemVenda.quantidade, ItemVenda.preco_unitario,
                         valor_item.label("subtotal"), Venda.forma_pagamento)
        .join(Cliente, Venda.id_cliente == Cliente.id_cliente)
        .join(Vendedor, Venda.id_vendedor == Vendedor.id_vendedor)
        .join(ItemVenda, ItemVenda.id_venda == Venda.id_venda)
        .join(Moto, ItemVenda.id_moto == Moto.id_moto)
        .join(Marca, Moto.id_marca == Marca.id_marca)
    ).order_by(Venda.data_venda.desc(), Venda.id_venda.desc()).all()

    # 2) Motos mais vendidas
    mais_vendidas = no_periodo(
        db.session.query(Marca.nome.label("marca"), Moto.modelo,
                         func.sum(ItemVenda.quantidade).label("unidades"),
                         func.sum(valor_item).label("total"))
        .join(Moto, ItemVenda.id_moto == Moto.id_moto)
        .join(Marca, Moto.id_marca == Marca.id_marca)
        .join(Venda, ItemVenda.id_venda == Venda.id_venda)
    ).group_by(Moto.id_moto, Marca.nome, Moto.modelo) \
     .order_by(func.sum(ItemVenda.quantidade).desc(), func.sum(valor_item).desc()).all()

    # 3) Vendas por vendedor (com comissão)
    por_vendedor = no_periodo(
        db.session.query(Vendedor.nome, Vendedor.comissao_pct,
                         func.count(func.distinct(Venda.id_venda)).label("vendas"),
                         func.sum(valor_item).label("total"))
        .join(Venda, Venda.id_vendedor == Vendedor.id_vendedor)
        .join(ItemVenda, ItemVenda.id_venda == Venda.id_venda)
    ).group_by(Vendedor.id_vendedor, Vendedor.nome, Vendedor.comissao_pct) \
     .order_by(func.sum(valor_item).desc()).all()

    total_geral = sum((linha.subtotal for linha in detalhado), Decimal(0))
    return render_template("relatorios.html", detalhado=detalhado, mais_vendidas=mais_vendidas,
                           por_vendedor=por_vendedor, total_geral=total_geral)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()      # cria as tabelas caso o script SQL ainda não tenha sido executado
    app.run(debug=True)
