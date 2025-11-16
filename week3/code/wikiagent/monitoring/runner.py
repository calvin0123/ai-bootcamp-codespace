from dataclasses import dataclass
from parser import parse_log_file
from evaluator import LLMEvaluator
from sources import LocalDirectorySource
from config import get_settings
from db import Database
import asyncio

def process_file(db, evaluator, source, path, debug):
    
    rec = parse_log_file(str(path))

    # insert the rec into the db
    log_id = db.insert_log(rec)

    # evaluate the rec
    checks = asyncio.run(evaluator.evaluate(log_id, rec))
    print(checks)

    # insert the checks into db
    db.insert_checks(checks)

    source.mark_processed(path)

def run_once(debug: bool = False):
    
    settings = get_settings()

    source = LocalDirectorySource(settings.logs_dir, pattern=settings.file_glob, processed_prefix=settings.processed_prefix)

    db = Database(settings.database_url)
    
    evaluator = LLMEvaluator()

    for path in source.iter_files():
        process_file(db, evaluator, source, path, debug=debug or settings.debug)

    

    # count = 0
    # for path in source.iter_files():
    #     if process_file(db, evaluator, source, path, debug=debug or settings.debug) is not None:
    #         count += 1

if __name__ == "__main__":
    
    run_once()