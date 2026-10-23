import os
import sys
import argparse
import base64
from datetime import datetime
import xml.etree.ElementTree as xml_et

REQUIRED_CP_ARGS = 2
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


def check_node_by_path(path_list):
    node = vfs_root
    for dir_name in path_list:
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


def get_current_node():
    return check_node_by_path(current_path)


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


def process_cd_parts(parts: list, temp_path: list) -> bool:
    for part in parts:
        if not part or part == ".":
            continue
        if part == "..":
            if temp_path:
                temp_path.pop()
            continue
        temp_path.append(part)
        if check_node_by_path(temp_path) is None:
            return False
    return True


def run_cd_cmd(args: list) -> bool:
    global current_path
    if not args:
        current_path = []
        return True

    raw_target = args[0]
    if raw_target == "/":
        current_path = []
        return True

    temp_path = [] if raw_target.startswith("/") else list(current_path)
    parts = raw_target.split("/")

    if not process_cd_parts(parts, temp_path):
        print(f"Ошибка cd: Папка '{raw_target}' не найдена.")
        return False

    current_path = temp_path
    return True


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


def run_pwd_cmd() -> bool:
    path_str = "/" + "/".join(current_path)
    print(path_str)
    return True


def calculate_node_size(node) -> int:
    total_size = 0
    for child_file in node.findall("file"):
        content_b64 = child_file.get("content", "")
        try:
            total_size += len(base64.b64decode(content_b64))
        except Exception:
            total_size += len(content_b64)
    for child_dir in node.findall("dir"):
        total_size += calculate_node_size(child_dir)
    return total_size


def get_item_size(child) -> int:
    content_b64 = child.get("content", "")
    try:
        return len(base64.b64decode(content_b64))
    except Exception:
        return len(content_b64)


def print_target_size(node, target) -> bool:
    for child in node.findall("file"):
        if child.get("name") == target:
            print(f"{get_item_size(child)}\t{target}")
            return True
    for child in node.findall("dir"):
        if child.get("name") == target:
            print(f"{calculate_node_size(child)}\t{target}")
            return True
    print(f"Ошибка du: '{target}' не найден.")
    return False


def run_du_cmd(args: list) -> bool:
    node = get_current_node()
    if node is None:
        return False
    if args:
        return print_target_size(node, args[0])
    for child in node.findall("dir"):
        print(f"{calculate_node_size(child)}\t{child.get('name')}")
    for child in node.findall("file"):
        print(f"{get_item_size(child)}\t{child.get('name')}")
    return True


def find_file_node(node, name):
    for child in node.findall("file"):
        if child.get("name") == name:
            return child
    return None


def execute_cp(node, src, dest) -> bool:
    src_file = find_file_node(node, src)
    if src_file is None:
        print(f"Ошибка cp: Файл '{src}' не найден.")
        return False

    for child_dir in node.findall("dir"):
        if child_dir.get("name") == dest:
            new_file = xml_et.SubElement(child_dir, "file")
            new_file.set("name", src)
            new_file.set("content", src_file.get("content", ""))
            return True

    new_file = xml_et.SubElement(node, "file")
    new_file.set("name", dest)
    new_file.set("content", src_file.get("content", ""))
    return True


def run_cp_cmd(args: list) -> bool:
    if len(args) < REQUIRED_CP_ARGS:
        print("Ошибка cp: Нужно указать источник и приемник.")
        return False
    node = get_current_node()
    if node is None:
        return False
    return execute_cp(node, args[0], args[1])


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
    if command == "ls":
        return run_ls_cmd()
    if command == "cd":
        return run_cd_cmd(args)
    if command == "cat":
        return run_cat_cmd(args)
    if command == "pwd":
        return run_pwd_cmd()
    if command == "du":
        return run_du_cmd(args)
    if command == "cp":
        return run_cp_cmd(args)

    print(f"Ошибка: команда '{command}' не найдена.")
    return False


def create_parser():
    parser = argparse.ArgumentParser(
        description="Эмулятор оболочки ОС. Этап 5."
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
