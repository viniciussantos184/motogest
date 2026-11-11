-- ============================================================
--  MotoGest - Sistema de gestão para loja de motos
--  Trabalho N2 - Projeto de Banco de Dados e Aplicações
--  Script de criação do banco (MySQL 8)
--  Uso:  mysql -u root -p < database/loja_motos.sql
-- ============================================================

SET NAMES utf8mb4;

DROP DATABASE IF EXISTS loja_motos;
CREATE DATABASE loja_motos CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE loja_motos;

-- ------------------------------------------------------------
-- Tabelas
-- ------------------------------------------------------------
CREATE TABLE marcas (
    id_marca     INT AUTO_INCREMENT PRIMARY KEY,
    nome         VARCHAR(50) NOT NULL,
    pais_origem  VARCHAR(50),
    CONSTRAINT uq_marca_nome UNIQUE (nome)
) ENGINE=InnoDB;

CREATE TABLE motos (
    id_moto     INT AUTO_INCREMENT PRIMARY KEY,
    id_marca    INT NOT NULL,
    modelo      VARCHAR(80) NOT NULL,
    ano         INT NOT NULL,
    cilindrada  INT NOT NULL,
    cor         VARCHAR(30),
    preco       DECIMAL(10,2) NOT NULL,
    estoque     INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_moto_marca FOREIGN KEY (id_marca) REFERENCES marcas (id_marca)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_moto_preco      CHECK (preco > 0),
    CONSTRAINT chk_moto_estoque    CHECK (estoque >= 0),
    CONSTRAINT chk_moto_cilindrada CHECK (cilindrada > 0)
) ENGINE=InnoDB;

CREATE TABLE clientes (
    id_cliente  INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    cpf         VARCHAR(14) NOT NULL,
    telefone    VARCHAR(20),
    email       VARCHAR(100),
    cidade      VARCHAR(60),
    CONSTRAINT uq_cliente_cpf UNIQUE (cpf)
) ENGINE=InnoDB;

CREATE TABLE vendedores (
    id_vendedor   INT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100) NOT NULL,
    email         VARCHAR(100),
    comissao_pct  DECIMAL(5,2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_vendedor_email UNIQUE (email),
    CONSTRAINT chk_vendedor_comissao CHECK (comissao_pct >= 0 AND comissao_pct <= 100)
) ENGINE=InnoDB;

CREATE TABLE vendas (
    id_venda         INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente       INT NOT NULL,
    id_vendedor      INT NOT NULL,
    data_venda       DATE NOT NULL,
    forma_pagamento  ENUM('Dinheiro','Pix','Cartão','Financiamento','Consórcio') NOT NULL,
    CONSTRAINT fk_venda_cliente  FOREIGN KEY (id_cliente)  REFERENCES clientes (id_cliente)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_venda_vendedor FOREIGN KEY (id_vendedor) REFERENCES vendedores (id_vendedor)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE itens_venda (
    id_item         INT AUTO_INCREMENT PRIMARY KEY,
    id_venda        INT NOT NULL,
    id_moto         INT NOT NULL,
    quantidade      INT NOT NULL DEFAULT 1,
    preco_unitario  DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_item_venda FOREIGN KEY (id_venda) REFERENCES vendas (id_venda)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_item_moto  FOREIGN KEY (id_moto)  REFERENCES motos (id_moto)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT chk_item_quantidade CHECK (quantidade > 0),
    CONSTRAINT chk_item_preco      CHECK (preco_unitario > 0)
) ENGINE=InnoDB;

CREATE INDEX idx_moto_modelo ON motos (modelo);
CREATE INDEX idx_venda_data  ON vendas (data_venda);

-- ------------------------------------------------------------
-- Dados de exemplo
-- ------------------------------------------------------------
INSERT INTO marcas (nome, pais_origem) VALUES
    ('Honda', 'Japão'),
    ('Yamaha', 'Japão'),
    ('Suzuki', 'Japão'),
    ('Kawasaki', 'Japão'),
    ('BMW', 'Alemanha'),
    ('Royal Enfield', 'Índia');

INSERT INTO motos (id_marca, modelo, ano, cilindrada, cor, preco, estoque) VALUES
    (1, 'CG 160 Titan',      2026, 160, 'Vermelha', 18990.00, 7),
    (1, 'Biz 125',           2026, 125, 'Branca',   14590.00, 5),
    (1, 'CB 500F',           2025, 500, 'Preta',    43900.00, 2),
    (1, 'XRE 300 Sahara',    2026, 300, 'Cinza',    29990.00, 3),
    (2, 'Fazer FZ25',        2026, 250, 'Azul',     24690.00, 4),
    (2, 'MT-03',             2025, 321, 'Preta',    34990.00, 1),
    (2, 'NMax 160',          2026, 160, 'Cinza',    19990.00, 6),
    (3, 'V-Strom 650',       2025, 650, 'Amarela',  58900.00, 1),
    (4, 'Ninja 400',         2025, 400, 'Verde',    38990.00, 2),
    (4, 'Z900',              2026, 900, 'Preta',    62490.00, 0),
    (5, 'G 310 GS',          2025, 310, 'Branca',   37500.00, 2),
    (6, 'Meteor 350',        2026, 350, 'Azul',     23990.00, 3);

INSERT INTO clientes (nome, cpf, telefone, email, cidade) VALUES
    ('Carlos Eduardo Lima',   '123.456.789-01', '(19) 99811-2030', 'carlos.lima@email.com',   'Indaiatuba'),
    ('Fernanda Souza Alves',  '234.567.890-12', '(19) 99722-4151', 'fernanda.alves@email.com','Campinas'),
    ('João Pedro Martins',    '345.678.901-23', '(11) 98633-5262', 'joao.martins@email.com',  'Itu'),
    ('Mariana Costa Ribeiro', '456.789.012-34', '(19) 99544-6373', 'mariana.cr@email.com',    'Salto'),
    ('Rafael Oliveira Nunes', '567.890.123-45', '(19) 99455-7484', 'rafael.nunes@email.com',  'Indaiatuba'),
    ('Beatriz Santos Rocha',  '678.901.234-56', '(15) 99366-8595', 'bia.rocha@email.com',     'Sorocaba');

INSERT INTO vendedores (nome, email, comissao_pct) VALUES
    ('Anderson Pereira', 'anderson@motogest.com', 2.00),
    ('Luciana Teixeira', 'luciana@motogest.com',  2.50),
    ('Marcos Vinícius',  'marcos@motogest.com',   1.50);

INSERT INTO vendas (id_cliente, id_vendedor, data_venda, forma_pagamento) VALUES
    (1, 1, '2026-08-14', 'Financiamento'),
    (2, 2, '2026-08-29', 'Pix'),
    (3, 1, '2026-09-05', 'Cartão'),
    (4, 3, '2026-09-20', 'Consórcio'),
    (5, 2, '2026-10-03', 'Financiamento'),
    (1, 2, '2026-10-18', 'Pix'),
    (6, 1, '2026-10-27', 'Dinheiro'),
    (2, 3, '2026-11-06', 'Financiamento');

INSERT INTO itens_venda (id_venda, id_moto, quantidade, preco_unitario) VALUES
    (1, 1, 1, 18990.00),
    (2, 7, 1, 19990.00),
    (3, 5, 1, 24690.00),
    (4, 2, 2, 14590.00),
    (5, 9, 1, 38990.00),
    (6, 1, 1, 18990.00),
    (6, 2, 1, 14590.00),
    (7, 12, 1, 23990.00),
    (8, 3, 1, 43900.00);

-- ------------------------------------------------------------
-- Consultas de exemplo (as mesmas usadas na tela Relatórios)
-- ------------------------------------------------------------
-- Vendas detalhadas (JOIN entre as 6 tabelas)
-- SELECT v.id_venda, v.data_venda, c.nome AS cliente, ve.nome AS vendedor,
--        ma.nome AS marca, m.modelo, i.quantidade, i.preco_unitario,
--        i.quantidade * i.preco_unitario AS subtotal
--   FROM vendas v
--   JOIN clientes c     ON c.id_cliente   = v.id_cliente
--   JOIN vendedores ve  ON ve.id_vendedor = v.id_vendedor
--   JOIN itens_venda i  ON i.id_venda     = v.id_venda
--   JOIN motos m        ON m.id_moto      = i.id_moto
--   JOIN marcas ma      ON ma.id_marca    = m.id_marca
--  ORDER BY v.data_venda DESC;

-- Motos mais vendidas
-- SELECT ma.nome AS marca, m.modelo, SUM(i.quantidade) AS unidades,
--        SUM(i.quantidade * i.preco_unitario) AS total
--   FROM itens_venda i
--   JOIN motos m   ON m.id_moto   = i.id_moto
--   JOIN marcas ma ON ma.id_marca = m.id_marca
--  GROUP BY m.id_moto, ma.nome, m.modelo
--  ORDER BY unidades DESC;
