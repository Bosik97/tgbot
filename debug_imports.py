import sys, traceback
out = open("import_debug.txt", "w", encoding="utf-8")
try:
    import utils
    out.write("utils OK\n")
    import handlers
    out.write("handlers OK\n")
    import notifications
    out.write("notifications OK\n")
    import database
    out.write("database OK\n")
except Exception as e:
    out.write("ERROR: " + str(e) + "\n")
    traceback.print_exc(file=out)
out.close()
print("Done check file")
