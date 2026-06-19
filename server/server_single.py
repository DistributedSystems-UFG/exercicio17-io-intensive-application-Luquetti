"""
Servidor v1: SINGLE-THREADED.

Aceita uma conexao por vez. Processa, responde, fecha, e so entao
volta a aceitar a proxima. Qualquer cliente que chegue durante o
processamento fica enfileirado no backlog do socket.
"""

import argparse
import socket

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
        print(f"[single] ouvindo em {args.host}:{args.port}")
        try:
            while True:
                conn, _addr = srv.accept()
                # tudo na thread principal, sequencialmente
                handle_connection(conn, args.data_file)
        except KeyboardInterrupt:
            print("\n[single] encerrando")


if __name__ == "__main__":
    main()
