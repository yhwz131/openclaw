#!/usr/bin/env python3
"""R-EXC 实等探针：睡 1900 秒。须经 bash scripts/recruitment-run.sh python3 调用以命中 exec 白名单。"""
import os
import time
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))
print(f"R-EXC-PROBE start {datetime.now(TZ).isoformat()} pid={os.getpid()}", flush=True)
time.sleep(1900)
print(
    f"R-EXC-PROBE done {datetime.now(TZ).isoformat()} (unexpected: should have been killed at 1800s)",
    flush=True,
)
