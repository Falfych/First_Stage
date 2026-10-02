import os
import sys

def expand_env_variables(text: str) -> str:
    return os.path.expandvars(text)

def main():
    vfs_name = "MyVFS"
    
    while True:
        try:
            prompt = f"{vfs_name} > "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
              
            user_input = expand_env_variables(user_input)
            
            parts = user_input.split()
            command = parts[0]
            args = parts[1:]
            
            if command == "exit":
                print("Завершение работы эмулятора.")
                break
                
            elif command in ["ls", "cd"]:
                print(f"Вызвана команда-заглушка: {command}")
                print(f"Аргументы: {args if args else 'нет'}")
                
            else:
                print(f"Ошибка: команда '{command}' не найдена.")
                
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение работы эмулятора.")
            break
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()
