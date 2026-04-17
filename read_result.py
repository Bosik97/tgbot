try:
    with open(r"C:\Users\Бейбарыс\Desktop\football-bot\import_result.txt","r") as f:
        print(f.read())
except Exception as e:
    print("File error:", e)
