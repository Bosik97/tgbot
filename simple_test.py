import sys
print("Python:", sys.version)
try:
    import utils
    print("utils imported successfully")
except Exception as e:
    print("utils error:", e)
try:
    import database
    print("database imported successfully")
except Exception as e:
    print("database error:", e)
try:
    import handlers
    print("handlers imported successfully")
except Exception as e:
    print("handlers error:", e)
try:
    import notifications
    print("notifications imported successfully")
except Exception as e:
    print("notifications error:", e)
