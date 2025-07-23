# scripts/gerar_talao.py
import sqlite3
from datetime import datetime
import os
import subprocess

def gerar_talao_libreoffice():
    """Gera talão usando LibreOffice Calc"""
    
    # Dados do talão (vem da interface)
    cliente = "NOME DO CLIENTE"
    produtos = [
        {"codigo": "001", "descricao": "Produto 1", "qtd": 2, "valor": 50.00},
        {"codigo": "002", "descricao": "Produto 2", "qtd": 1, "valor": 100.00}
    ]
    
    # Calcula totais
    subtotal = sum(p["qtd"] * p["valor"] for p in produtos)
    frete = calcular_frete(produtos)
    total = subtotal + frete
    
    # Gera arquivo temporário para LibreOffice
    template_path = "templates/talao_cliente.ods"
    output_path = f"output/talao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ods"
    
    # Copia template e preenche dados
    # (implementar preenchimento via macro LibreOffice Basic)
    
    # Abre LibreOffice para edição/impressão
    subprocess.run([
        "C:\\Program Files\\LibreOffice\\program\\scalc.exe", 
        output_path
    ])

def calcular_frete(produtos):
    """Calcula frete baseado no peso total"""
    peso_total = sum(p.get("peso", 0) * p["qtd"] for p in produtos)
    # Lógica de cálculo de frete
    return peso_total * 2.5  # R$ 2,50 por kg

if __name__ == "__main__":
    gerar_talao_libreoffice()