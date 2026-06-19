"""
Servidor v3: POOL DE THREADS (modelo do Slide 35 - Slides 05.2).

Um pool de tamanho fixo eh criado no startup. A thread principal aceita
conexoes e submete cada uma como tarefa ao pool, que mantem um conjunto
limitado de threads reutilizadas atraves de uma fila de trabalho interna.

Vantagem em relacao a v2: nao paga o custo de criar/destruir thread por
requisicao e protege o servidor contra explosao de threads sob carga.
"""

import argparse
import socket
from concurrent.futures import ThreadPoolExecutor

from protocol import (
    DEFAULT_DATA_FILE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    handle_connection,
)

DEFAULT_WORKERS = 16


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="tamanho fixo do pool de threads",
    )
    args = parser.parse_args()

    pool = ThreadPoolExecutor(
        max_workers=args.workers, thread_name_prefix="worker"
    )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.host, args.port))
        srv.listen(128)
        print(
            f"[thread-pool workers={args.workers}] "
            f"ouvindo em {args.host}:{args.port}"
        )
        try:
            while True:
                conn, _addr = srv.accept()
                pool.submit(handle_connection, conn, args.data_file)
        except KeyboardInterrupt:
            print("\n[thread-pool] encerrando")
        finally:
            pool.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    main()
