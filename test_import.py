import sys
sys.path.append(r"C:\Users\Бейбарыс\Desktop\football-bot")
try:
    import database
    print("database OK")
except Exception as e:
    import traceback
    traceback.print_exc()
