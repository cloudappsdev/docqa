import argparse

from .pipeline import ingest_directory, ingest_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the vector store")
    parser.add_argument("path", help="file or directory")
    parser.add_argument("--force", action="store_true", help="re-ingest even if unchanged")
    args = parser.parse_args()

    from pathlib import Path

    p = Path(args.path)
    results = ingest_directory(p, args.force) if p.is_dir() else [ingest_file(p, force=args.force)]
    for r in results:
        print(f"{r['status']:<28} {r['chunks']:>4} chunks  {r['filename']}")


if __name__ == "__main__":
    main()
