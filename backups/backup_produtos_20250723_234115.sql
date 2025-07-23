-- Backup Sistema PDV - 23/07/2025 23:41:15
-- Madeireira Maria Luiza

BEGIN TRANSACTION;
CREATE TABLE cache_info (
                    tipo TEXT PRIMARY KEY,
                    ultimo_update TIMESTAMP,
                    total_registros INTEGER
                );
CREATE TABLE produtos (
                    codigo TEXT PRIMARY KEY,
                    descricao TEXT,
                    preco_venda REAL,
                    preco_custo REAL,
                    estoque INTEGER,
                    categoria TEXT,
                    ativo INTEGER DEFAULT 1,
                    ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
INSERT INTO "produtos" VALUES('UI001','Produto Teste UI',25.5,15.0,5,'Teste UI',1,'2025-07-23 23:39:40');
COMMIT;
