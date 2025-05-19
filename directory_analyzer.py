import os

def get_directory_structure(startpath):
    """
    生成仅包含目录结构的文本表示
    """
    structure = []
    for root, dirs, _ in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = '│   ' * (level - 1) + '├── ' if level > 0 else ''
        structure.append(f"{indent}{os.path.basename(root)}/")
    return '\n'.join(structure)

def save_structure_to_clipboard(structure):
    """
    尝试将结构保存到剪贴板
    """
    try:
        import pyperclip
        pyperclip.copy(structure)
        print("\n✅ 目录结构已复制到剪贴板！")
    except ImportError:
        print("\n⚠️ pyperclip未安装，请手动复制以下结构：\n")
        print(structure)
    except Exception as e:
        print(f"\n⚠️ 无法访问剪贴板：{str(e)}")
        print("请手动复制以下结构：\n")
        print(structure)

if __name__ == "__main__":
    print("=== 目录结构收集工具 ===")
    target_dir = input("请输入目标目录路径（留空为当前目录）: ").strip() or "."

    if not os.path.isdir(target_dir):
        print(f"\n错误：路径 '{target_dir}' 不是有效目录！")
    else:
        abs_path = os.path.abspath(target_dir)
        print(f"\n正在分析目录结构: {abs_path}")

        dir_structure = f"目录结构: {abs_path}/\n" + get_directory_structure(abs_path)
        save_structure_to_clipboard(dir_structure)

    input("\n按Enter键退出...")