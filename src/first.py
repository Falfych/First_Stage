import os
import sys
import argparse
import base64
from datetime import datetime
import xml.etree.ElementTree as xml_et

current_path = []
vfs_root = None


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


def get_current_node():
    node = vfs_root
    for dir_name in current_path:
        found = None
        for child in node.findall("dir"):
            if child.get("name") == dir_name:
                found = child
                break
        if found is not None:
            node = found
        else:
            return None
    return node


def run_ls_cmd() -> bool:
    node = get_current_node()
    if node is None:
        print("Ошибка: текущая директория не найдена.")
        return False
    for child in node.findall("dir"):
        print(f"[DIR]  {child.get('name')}")
    for child in node.findall("file"):
        print(f"[FILE] {child.get('name')}")
    return True


def run_cd_cmd(args: list) -> bool:
    global current_path
    if not args or args[0] == "/":
        current_path = []
        return True
    target = args[0]
    if target == "..":
        if current_path:
            current_path.pop()
        return True
    node = get_current_node()
    if node is None:
        print("Ошибка: текущая директория не найдена.")
        return False
    for child in node.findall("dir"):
        if child.get("name") == target:
            current_path.append(target)
            return True
    print(f"Ошибка cd: Папка '{target}' не найдена.")
    return False


def run_cat_cmd(args: list) -> bool:
    if not args:
        print("Ошибка cat: не указан файл.")
        return False
    filename = args[0]
    node = get_current_node()
    if node is None:
        return False
    for child in node.findall("file"):
        if child.get("name") == filename:
            content_b64 = child.get("content", "")
            try:
                decoded = base64.b64decode(content_b64).decode("utf-8")
                print(decoded)
            except Exception:
                print(content_b64)
            return True
    print(f"Ошибка cat: Файл '{filename}' не найден.")
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
    elif command == "ls":
        return run_ls_cmd()
    elif command == "cd":
        return run_cd_cmd(args)
    elif command == "cat":
        return run_cat_cmd(args)

    print(f"Ошибка: команда '{command}' не найдена.")
    return False


def create_parser():
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки ОС. Этап 3."
    )
    parser.add_argument(
        "--vfs", required=True, help="Путь к XML файлу VFS"
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

            path_str = "/" + "/".join(current_path)
            print(f"{vfs_name}:{path_str} > {line}")

            if not execute_command(line, log_path):
                print("Запуск прерван: Ошибка во время скрипта.")
                sys.exit(1)
    print("--- Стартовый скрипт успешно выполнен ---\n")


def load_vfs(vfs_path: str):
    global vfs_root
    if not os.path.exists(vfs_path):
        print(f"Критическая ошибка: Файл VFS '{vfs_path}' не найден.")
        sys.exit(1)
    try:
        tree = xml_et.parse(vfs_path)
        vfs_root = tree.getroot()
        if vfs_root.tag != "vfs":
            raise ValueError("Корневой тег должен быть <vfs>")
    except Exception as e:
        print(f"Критическая ошибка: Неверный формат VFS XML. Ошибка: {e}")
        sys.exit(1)


def main():
    parser = create_parser()
    args = parser.parse_args()

    load_vfs(args.vfs)

    print("=== Отладочный вывод конфигурации ===")
    print(f"VFS Path:   {args.vfs}")
    print(f"Log Path:   {args.log}")
    script_status = args.script if args.script else "Не задан"
    print(f"Script OS:  {script_status}")
    print("=====================================\n")

    vfs_name = vfs_root.get("name", "MyVFS")

    if args.script:
        run_startup_script(args.script, args.log, vfs_name)

    while True:
        try:
            path_str = "/" + "/".join(current_path)
            user_input = input(f"{vfs_name}:{path_str} > ").strip()
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
