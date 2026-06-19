# Serviço de leitura de arquivo via rede — 3 versões

Trabalho de SCD (UFG) — três versões de um serviço acessível via rede que lê
dados de um arquivo no servidor, comparando vazão entre os modelos de
concorrência.

## Arquitetura

```
servico-arquivo/
├── data/
│   ├── dados.txt          # arquivo lido pelo servidor
│   └── gerar_dados.py     # gera o arquivo de teste
├── server/
│   ├── protocol.py                     # protocolo + handler comum às 3 versões
│   ├── server_single.py                # v1: single-threaded
│   ├── server_thread_per_request.py    # v2: thread criada por requisição
│   └── server_thread_pool.py           # v3: pool de threads (Slide 35)
├── client/
│   └── benchmark.py       # cliente de benchmark (mede req/s)
└── run_benchmark.sh       # roda as 3 versões em sequência
```

## Protocolo

TCP, texto, linha-orientado, UTF-8. Uma requisição por conexão.

| Requisição          | Resposta                                  |
| ------------------- | ----------------------------------------- |
| `GET <n>\n`         | `OK <conteúdo-da-linha-n>\n`              |
| `COUNT\n`           | `OK <total-de-linhas>\n`                  |
| inválida            | `ERR <mensagem>\n`                        |

O arquivo é lido a cada requisição **de propósito**: simula o custo real de
I/O e torna a comparação entre os modelos de concorrência mais visível.

## Como executar

```bash
# 1. gerar dados
python3 data/gerar_dados.py --out data/dados.txt --lines 50000

# 2. subir um dos servidores
python3 server/server_single.py            --port 5050 --data-file data/dados.txt
python3 server/server_thread_per_request.py --port 5050 --data-file data/dados.txt
python3 server/server_thread_pool.py        --port 5050 --data-file data/dados.txt --workers 16

# 3. rodar o benchmark em outro terminal
python3 client/benchmark.py --port 5050 --clients 50 --requests 40 --max-line 50000

# ou rodar tudo de uma vez:
./run_benchmark.sh 50 40
```

## Comparação de vazão

Arquivo de dados: 50.000 linhas (2,2 MB). Localhost. Pool com 16 workers.
Vazão em req/s (maior = melhor).

| Carga (clientes × reqs = total) | Single             | Thread/req | Thread-pool (16) |
| ------------------------------- | ------------------ | ---------- | ---------------- |
| 10 × 100 = 1.000                | 244,18             | 296,98     | **333,11**       |
| 50 × 40 = 2.000                 | 261,48             | 294,29     | **330,49**       |
| 200 × 30 = 6.000                | 53,40 *(24 erros)* | 304,80     | **324,01**       |

### Análise

**Single-threaded.** Aceita uma conexão de cada vez e só volta ao `accept()`
depois que terminou a anterior. Sob baixa carga ainda funciona porque o
serviço por requisição é curto, mas quando muitos clientes chegam ao mesmo
tempo todos vão para o backlog do socket. Com 200 clientes concorrentes a
vazão **caiu de ~260 para ~53 req/s** e 24 conexões foram **rejeitadas**
(backlog esgotado / `connection refused`). É a versão menos confiável: não
falha só em desempenho, falha em disponibilidade.

**Thread por requisição.** Resolve o problema do single — a thread principal
volta imediatamente ao `accept()` e cada conexão é tratada em paralelo.
Resultado: vazão estável (~300 req/s) e zero erros mesmo com 200 clientes.
O custo escondido é que toda conexão paga *criação + destruição de thread*,
e nada limita quantas threads existem ao mesmo tempo. Sob carga real isso
pode levar à explosão de threads e degradação severa do escalonador.

**Pool de threads.** Mesmo benefício de paralelismo do anterior, sem os dois
custos: o pool é criado uma única vez no startup e mantém um número fixo de
threads reutilizadas via fila interna. O resultado é a maior vazão em todos
os cenários (~325–333 req/s) e proteção natural contra explosão de threads
— se a carga ultrapassar o pool, requisições enfileiram em vez de criar
threads sem limite. É o modelo recomendado para serviços de produção.

### Observações sobre o ambiente

- Os testes rodam em loopback (`127.0.0.1`), então a latência de rede é
  desprezível. Em rede real, a diferença entre as versões com threads
  tende a aumentar (mais tempo bloqueado em I/O de socket).
- O CPython tem GIL, mas o gargalo aqui é I/O de arquivo, que libera o GIL
  durante a syscall de leitura. Por isso threads ainda ajudam.
- O tamanho ótimo do pool depende do hardware; 16 é um chute razoável para
  CPUs modernas com carga mista de I/O. Para encontrar o ideal, varie
  `--workers` e re-execute o benchmark.
