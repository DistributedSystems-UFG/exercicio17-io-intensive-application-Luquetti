"""
Servidor v2: THREAD POR REQUISICAO.

A cada conexao aceita, cria uma nova thread (daemon) para tratar a
requisicao. A thread principal volta imediatamente ao accept().
Sem limite de threads concorrentes: cresce com a demanda.
"""

import argparse
import socket
import threading

from protocol import (
    DEFAULT_DATA_FILE,
    DEFAULT_HOST,
    DEFAULT_PORT,
    handle_connection,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-file", default=DEFAULT_DATA_FILE)
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((args.host, args.port))
        srv.listen(128)
        print(f"[thread-per-request] ouvindo em {args.host}:{args.port}")
        try:
            while True:
                conn, _addr = srv.accept()
                t = threading.Thread(
                    target=handle_connection,
                    args=(conn, args.data_file),
                    daemon=True,
                )
                t.start()
        except KeyboardInterrupt:
            print("\n[thread-per-request] encerrando")


if __name__ == "__main__":
    main()
