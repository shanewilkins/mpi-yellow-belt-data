"""Explicit course discovery, evidence, experiments, workspaces, and backups."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from mpi_yellow_belt_data.catalog import (
    DATA_ROOT,
    CaseError,
    check_dataset,
    generation_config,
    list_cases,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mpi-yellow-belt-data")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    for name in ("check", "validate", "generate", "prepare"):
        p = commands.add_parser(name)
        p.add_argument("case_id", choices=["riverside"])
        p.add_argument("--dataset-version", choices=["1.0.0", "2.0.0"], default="1.0.0")
        p.add_argument("--data-root", type=Path)
        if name in ("generate", "prepare"):
            p.add_argument("--output", type=Path, required=True)
        if name == "generate":
            p.add_argument("--seed", type=int)
            p.add_argument("--sample", type=int)
        if name == "prepare":
            p.add_argument("--archive", type=Path)
            p.add_argument(
                "--release",
                choices=["initial", "investigation", "followup"],
                default="initial",
            )
    p = commands.add_parser("acquire")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--data-root", type=Path, default=DATA_ROOT)
    p = commands.add_parser("export-work")
    p.add_argument("workspace", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            print(json.dumps(list_cases(), indent=2))
        elif args.command == "acquire":
            from mpi_yellow_belt_data.acquisition import acquire

            print(acquire(args.source, args.data_root / "riverside/2.0.0"))
        elif args.command == "export-work":
            from mpi_yellow_belt_data.workspaces import export_work

            print(export_work(args.workspace, args.output))
        elif args.dataset_version == "2.0.0":
            from mpi_yellow_belt_data.cases.riverside.model import evidence, network
            from mpi_yellow_belt_data.resources import release_pin

            directory = (args.data_root or DATA_ROOT) / "riverside/2.0.0"
            if args.command == "prepare" and args.archive is not None:
                from mpi_yellow_belt_data.workspaces import prepare_archive

                print(prepare_archive(args.archive, args.output, release=args.release))
            elif args.command == "generate":
                print(network.generate(args.output, seed=args.seed, sample=args.sample))
            elif args.command == "prepare":
                print(
                    evidence.prepare(
                        directory, args.output, release=args.release, pin=release_pin()
                    )
                )
            elif args.command == "validate":
                from mpi_yellow_belt_data.table_validation_v2 import validate

                print(json.dumps(validate(directory, pin=release_pin()), indent=2))
            else:
                print(
                    json.dumps(evidence.check(directory, pin=release_pin()), indent=2)
                )
        elif args.command == "check":
            generation_config(args.case_id)
            print(
                f"Verified riverside: {len(check_dataset('riverside', root=args.data_root)['files'])} files"
            )
        elif args.command == "validate":
            from mpi_yellow_belt_data.table_validation import validate_release

            print(validate_release(root=args.data_root))
        elif args.command == "prepare":
            from mpi_yellow_belt_data.workspaces import prepare_v1

            if args.release != "initial":
                raise CaseError("Dated releases require dataset version 2.0.0")
            print(prepare_v1(output=args.output, root=args.data_root))
        else:
            from mpi_yellow_belt_data.generation import generate

            if args.sample is not None:
                raise CaseError("Samples require dataset version 2.0.0")
            print(generate("riverside", output=args.output, seed=args.seed))
    except ImportError as error:
        parser.exit(
            1,
            f"This operation requires its learner, validation, or generation extra: {error}\n",
        )
    except (ValueError, OSError) as error:
        parser.exit(1, f"Course operation failed: {error}\n")
    return 0
