import os
import sys
import argparse
from datetime import datetime
import xml.etree.ElementTree as xml_et


def expand_env_variables(text: str) -> str:
    return os.path.expandvars(text)


def load_log_tree(log_path: str):
    if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
        try:
            tree = xml_et.parse(log_path)
            return tree, tree.getroot()
        except Exception:
            pass
    root = xml_et.Element("history")
    return xml_et.ElementTree(root), root


def log_event(log_path: str, command: str, args: list):
    if not log_path:
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    args_str = " ".join(args)

    tree, root = load_log_tree(log_path)

    event = xml_et.SubElement(root, "event")
    xml_et.SubElement(event, "datetime").text = timestamp
    xml_et.SubElement(event, "command").text = command
    xml_et.SubElement(event, "arguments").text = args_str

    xml_et.indent(tree, space="    ", level=0)
    tree.write(log_path, encoding="utf-8", xml_declaration=True)


def run_builtin_cmd(command: str, args: list) -> bool:
    if command in ["ls", "cd"]:
        print(f"Вызвана команда-заглушка: {command}")
        print(f"Аргументы: {args if args else 'нет'}")
        return True
    return False


def execute_command(user_input: str, log_path: str) -> bool:
    if not user_input:
        return True

    user_input = expand_env_variables(user_input)
    parts = user_input.split()
    command = parts[0]
    args = parts[1:]

    log_event(log_path, command, args)

    if command == "exit":
        print("Завершение работы эмулятора.")
        return False

    if run_builtin_cmd(command, args):
        return True

    print(f"Ошибка: команда '{command}' не найдена.")
    return False


def create_parser():
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки ОС. Этап 2."
    )
    parser.add_argument(
        "--vfs", required=True, help="Путь к физическому расположению VFS"
    )
    parser.add_argument(
        "--log", required=True, help="Путь к лог-файлу XML"
    )
    parser.add_argument(
        "--script", required=False, help="Путь к стартовому скрипту"
    )
    return parser


def run_startup_script(script_path: str, log_path: str, vfs_name: str):
    if not os.path.exists(script_path):
        print(f"Ошибка: Стартовый скрипт '{script_path}' не найден.")
        sys.exit(1)

    print(f"--- Выполнение стартового скрипта: {script_path} ---")
    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            print(f"{vfs_name} > {line}")

            if not execute_command(line, log_path):
                print("Запуск прерван: Ошибка во время скрипта.")
                sys.exit(1)
    print("--- Стартовый скрипт успешно выполнен ---\n")


def main():
    parser = create_parser()
    args = parser.parse_args()

    print("=== Отладочный вывод конфигурации ===")
    print(f"VFS Path:   {args.vfs}")
    print(f"Log Path:   {args.log}")
    script_status = args.script if args.script else "Не задан"
    print(f"Script OS:  {script_status}")
    print("=====================================\n")

    vfs_clean = args.vfs.strip("/\\")
    vfs_name = os.path.basename(vfs_clean) or "MyVFS"

    if args.script:
        run_startup_script(args.script, args.log, vfs_name)

    while True:
        try:
            user_input = input(f"{vfs_name} > ").strip()
            if not user_input:
                continue
            success = execute_command(user_input, args.log)
            if not success and user_input.split()[0] == "exit":
                break
        except (KeyboardInterrupt, EOFError):
            print("\nЗавершение работы эмулятора.")
            break
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()

