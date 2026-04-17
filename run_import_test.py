import sys, traceback
sys.path.append(r"C:\Users\Бейбарыс\Desktop\football-bot")
try:
    import utils
    import database
    import handlers
    import notifications
    with open("import_result.txt","w") as f:
        f.write("SUCCESS\n")
except Exception as e:
    with open("import_result.txt","w") as f:
        f.write("ERROR: "+str(e)+"\n")
        traceback.print_exc(file=f)
