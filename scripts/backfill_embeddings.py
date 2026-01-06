import argparse
import asyncio

from opus_blocks.tools.embeddings_backfill import run_backfill


async def _run(owner_id: str | None, limit: int | None) -> None:
    processed = await run_backfill(owner_id=owner_id, limit=limit)
    print(f"Backfilled embeddings for {processed} facts.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill fact embeddings into vector store.")
    parser.add_argument("--owner-id", default=None, help="Limit to a specific owner UUID.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of facts.")
    args = parser.parse_args()
    asyncio.run(_run(args.owner_id, args.limit))


if __name__ == "__main__":
    main()
