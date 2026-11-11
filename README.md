# MotoGest

Sistema web de gestão para uma loja de motos (Trabalho N2 de Projeto de Banco de Dados e Aplicações).
Tecnologias: MySQL, Python 3, Flask, SQLAlchemy, HTML/CSS com Bootstrap.

## Como executar

1. Crie o banco e os dados de exemplo (MySQL 8):

       mysql -u root -p < database/loja_motos.sql

   No MySQL Workbench: File > Open SQL Script, escolha `database/loja_motos.sql` e execute tudo (raio).

2. Instale as dependências (de preferência em um ambiente virtual):

       python -m venv venv
       venv\Scripts\activate          (Windows)   |   source venv/bin/activate   (Linux/Mac)
       pip install -r requirements.txt

3. Informe o usuário e a senha do seu MySQL. No `app.py`, altere a linha:

       "mysql+pymysql://root:root@localhost/loja_motos?charset=utf8mb4"
                        ^^^^ ^^^^
                     usuário senha

4. Rode a aplicação e abra http://127.0.0.1:5000

       python app.py

## Estrutura

    projeto/
    ├── app.py              rotas (CRUD, busca, vendas, relatórios)
    ├── models.py           tabelas mapeadas com SQLAlchemy
    ├── requirements.txt
    ├── database/
    │   ├── loja_motos.sql  script de criação do banco + dados de exemplo
    │   └── DER.png         diagrama entidade-relacionamento
    ├── templates/
    │   ├── base.html       layout comum (menu e mensagens)
    │   ├── index.html      painel inicial
    │   ├── listar.html     lista de motos + busca por filtros
    │   ├── cadastrar.html  formulário de moto (cadastrar e editar)
    │   ├── clientes.html, cliente_form.html
    │   ├── vendas.html, venda_form.html
    │   └── relatorios.html consultas com JOIN
    └── static/css/         Bootstrap (cópia local, funciona sem internet) e estilo.css

## Onde está cada requisito

| Requisito | Onde |
|---|---|
| 4+ tabelas relacionadas, PK, FK, restrições | `database/loja_motos.sql` e `models.py` (6 tabelas) |
| Flask + SQLAlchemy + templates | `app.py`, `models.py`, `templates/` |
| CRUD da entidade principal (motos) | rotas `/motos`, `/motos/cadastrar`, `/motos/<id>/editar`, `/motos/<id>/excluir` |
| Busca por filtros | `/motos` (modelo, marca, faixa de preço, só com estoque) |
| Relatório com JOIN | `/relatorios` (vendas detalhadas, motos mais vendidas, vendas por vendedor) |
