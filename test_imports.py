#!/usr/bin/env python
import sys
sys.path.append(r"C:\Users\Бейбарыс\Desktop\football-bot")
try:
    import utils
    print("utils OK")
    import handlers
    print("handlers OK")
    import notifications
    print("notifications OK")
    import database
    print("database OK")
except Exception as e:
    import traceback
    traceback.print_exc()
