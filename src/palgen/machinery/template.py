import traceback


def get_caller() -> traceback.FrameSummary:
    return traceback.extract_stack(limit=3)[-3]
