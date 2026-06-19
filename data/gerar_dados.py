"""Gera um arquivo de dados de teste com N linhas."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/dados.txt")
    parser.add_argument("--lines", type=int, default=1000)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for i in range(1, args.lines + 1):
            f.write(f"linha {i:05d}: registro de teste do servico SCD\n")
    print(f"gerado: {out_path} ({args.lines} linhas)")


if __name__ == "__main__":
    main()
