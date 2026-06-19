"""
Cliente de benchmark.

Dispara C clientes concorrentes (cada um em uma thread). Cada cliente
abre uma conexao TCP, envia 'GET <n>' com n aleatorio, le a resposta
e fecha a conexao -- repetindo isso R vezes.

Ao final, calcula:
  - tempo total (s)
  - vazao (req/s)
  - latencia media (ms/req)
"""

import argparse
import random
import socket
import threading
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050


def do_request(host: str, port: int, line_number: int) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(f"GET {line_number}\n".encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        return buf


def worker(
    host: str,
    port: int,
    n_requests: int,
    max_line: int,
    errors: list,
) -> None:
    for _ in range(n_requests):
        line = random.randint(1, max_line)
        try:
            do_request(host, port, line)
        except OSError as e:
            errors.append(str(e))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--clients", type=int, default=10, help="clientes concorrentes"
    )
    parser.add_argument(
        "--requests", type=int, default=100, help="requisicoes por cliente"
    )
    parser.add_argument(
        "--max-line",
        type=int,
        default=100,
        help="limite superior do numero de linha sorteado",
    )
    parser.add_argument(
        "--label", default="", help="rotulo para identificar a corrida"
    )
    args = parser.parse_args()

    total = args.clients * args.requests
    label = f"[{args.label}] " if args.label else ""
    print(
        f"{label}disparando {args.clients} clientes x "
        f"{args.requests} reqs = {total} total"
    )

    errors: list = []
    threads = []
    start = time.perf_counter()
    for _ in range(args.clients):
        t = threading.Thread(
            target=worker,
            args=(args.host, args.port, args.requests, args.max_line, errors),
        )
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    ok = total - len(errors)
    print(f"{label}tempo total:      {elapsed:.3f} s")
    print(f"{label}vazao:            {ok / elapsed:.2f} req/s")
    print(f"{label}latencia media:   {elapsed * 1000 / total:.2f} ms/req")
    print(f"{label}erros:            {len(errors)}")
    if errors[:3]:
        print(f"{label}exemplos de erro: {errors[:3]}")


if __name__ == "__main__":
    main()
