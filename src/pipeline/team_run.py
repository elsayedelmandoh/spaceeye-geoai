"""One current delivery command; --full first rebuilds/fits Track A from source caches."""

import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Also run the full Track A activity pipeline")
    args = parser.parse_args()
    if args.full:
        from src.pipeline.run_all import main as track_a
        if track_a() != 0:
            raise RuntimeError("Track A quality STOP")
    from src.pipeline.complete_data import main as prepare
    prepare()
    from src.pipeline.component_data import main as components
    components()
    from src.analysis.current_evaluation import run as evaluate
    evaluate()
    from src.pipeline.partial_exports import main as exports
    exports()
    from src.pipeline.quality_report import main as quality
    quality()
    from src.pipeline.source_catalog import main as sources
    sources()
    print("Current team delivery complete; read missing-class and review limitations before use")


if __name__ == "__main__":
    main()
