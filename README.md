# Sistema PDV

Este repositório já contém as alterações recentes na busca rápida do PDV (navegação por setas, Enter e tecla Escape para fechar sugestões). Use as instruções abaixo para rodar e testar.

## Requisitos
- Python 3.11+.
- Dependências listadas em `meu_sistema_pdv/requirements.txt`.

## Baixar o código
Você pode usar qualquer IDE ou apenas o terminal. Basta ter o código localmente:

- **Git:** `git clone <url-do-repositorio>` e depois `cd sistema_01.2`.
- **ZIP:** baixe o arquivo compactado, extraia e abra a pasta `sistema_01.2` no terminal ou na IDE.

## Instalação das dependências
Com a pasta do projeto aberta (via terminal ou IDE), execute:

```bash
pip install -r meu_sistema_pdv/requirements.txt
```

## Como executar
No mesmo diretório do projeto, inicie o PDV em modo navegador (padrão do Flet):

```bash
python meu_sistema_pdv/main.py
```

A aplicação abrirá no navegador padrão. Se preferir janela nativa, altere o parâmetro `view` do `ft.app` em `meu_sistema_pdv/main.py` conforme a documentação do Flet.

## Onde validar as mudanças
- A caixa de captura rápida no PDV agora responde às setas para navegar nas sugestões e à tecla Escape para fechá-las rapidamente (`meu_sistema_pdv/APP/ui/vendas_ui.py`).
- Execute o fluxo de venda e digite no campo de busca rápida para verificar a navegação por teclado.
