#!/usr/bin/env bash
# Roda o benchmark contra cada uma das 3 versoes do servidor.
# Uso: ./run_benchmark.sh [clientes] [requisicoes_por_cliente]

set -e

CLIENTS=${1:-20}
REQUESTS=${2:-50}
PORT=5050
DATA=../data/dados.txt
TOTAL=$((CLIENTS * REQUESTS))

cd "$(dirname "$0")/server"

run_one() {
    local script=$1
    local label=$2
    local extra=$3

    python3 "$script" --port $PORT --data-file $DATA $extra &
    local pid=$!
    sleep 0.6   # tempo do socket entrar em listen

    # warm-up curto pra estabilizar o disk cache do arquivo
    python3 ../client/benchmark.py --port $PORT --clients 2 --requests 10 \
        --max-line 1000 --label "warmup-$label" >/dev/null 2>&1 || true

    python3 ../client/benchmark.py --port $PORT \
        --clients $CLIENTS --requests $REQUESTS \
        --max-line 1000 --label "$label"

    kill $pid 2>/dev/null || true
    wait $pid 2>/dev/null || true
    echo ""
}

echo "==========================================================="
echo "Benchmark: $CLIENTS clientes x $REQUESTS reqs = $TOTAL total"
echo "==========================================================="
echo ""

run_one server_single.py            "single"
run_one server_thread_per_request.py "thread-per-request"
run_one server_thread_pool.py        "thread-pool-w16"  "--workers 16"
