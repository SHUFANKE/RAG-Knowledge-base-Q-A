from app.utils import add, clean_text

def main():
    result = add(10,20)
    cleaned = clean_text(" Hello LLM World! ")
    print(f"Add Result:{result}")
    print(f"Cleaned Text:{cleaned}")

if __name__ =="__main__":
    main()
