"""
Protocolo do servico de leitura de arquivo.

Formato (texto, linha-orientado, UTF-8):

  Requisicao:
    GET <n>\n          -> retorna a linha n (1-indexada) do arquivo
    COUNT\n            -> retorna a quantidade total de linhas

  Resposta:
    OK <conteudo>\n
    ERR <mensagem>\n

O arquivo eh lido a cada requisicao (de proposito): isso simula o custo
real de I/O de disco e torna mais visivel a diferenca entre os modelos
de concorrencia.
"""

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5050
DEFAULT_DATA_FILE = "data/dados.txt"


def handle_request(request: str, data_file: str) -> str:
    """Processa uma requisicao em texto e devolve a resposta em texto."""
    request = request.strip()
    if not request:
        return "ERR requisicao vazia\n"

    parts = request.split()
    cmd = parts[0].upper()

    if cmd == "GET":
        if len(parts) < 2:
            return "ERR uso: GET <numero_linha>\n"
        try:
            n = int(parts[1])
        except ValueError:
            return "ERR numero de linha invalido\n"
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            return f"ERR falha ao ler arquivo: {e}\n"
        if n < 1 or n > len(lines):
            return f"ERR linha {n} fora do intervalo (1..{len(lines)})\n"
        return f"OK {lines[n - 1].rstrip()}\n"

    if cmd == "COUNT":
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                count = sum(1 for _ in f)
            return f"OK {count}\n"
        except OSError as e:
            return f"ERR falha ao ler arquivo: {e}\n"

    return f"ERR comando desconhecido '{cmd}'\n"


def recv_line(conn) -> bytes:
    """Le bytes do socket ate encontrar '\\n' (ou conexao fechar)."""
    buf = b""
    while b"\n" not in buf:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf += chunk
    return buf


def handle_connection(conn, data_file: str) -> None:
    """Le uma requisicao da conexao, processa e responde. Fecha a conexao."""
    try:
        raw = recv_line(conn)
        if not raw:
            return
        response = handle_request(raw.decode("utf-8", errors="replace"), data_file)
        conn.sendall(response.encode("utf-8"))
    finally:
        try:
            conn.shutdown(__import__("socket").SHUT_RDWR)
        except OSError:
            pass
        conn.close()
