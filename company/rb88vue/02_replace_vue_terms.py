import os

# === 配置 ===
TARGET_DIR = '/Users/oncechen/IdeaProjects/rb88_web_vue'  # <-- 替换为你的 Vue 项目路径
ALLOWED_EXT = {'.vue', '.js', '.ts', '.html', '.css', '.scss'}

# 替换规则（顺序重要）
REPLACE_MAP = {
    "吉祥坊": "走地皇",
    "吉祥": "RB88走地皇",
    "jxfvue.nntitestserver": "rb88vue.nntitestserver",
    "jxfvue.itomtest.com": "rb88vue.itomtest.com",
    "jxvue": "rb88vue"
}


def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    for old, new in REPLACE_MAP.items():
        content = content.replace(old, new)

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 替换完成: {file_path}")


def walk_and_replace(target_dir):
    for root, _, files in os.walk(target_dir):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.splitext(filename)[1] in ALLOWED_EXT:
                try:
                    replace_in_file(filepath)
                except Exception as e:
                    print(f"⚠️ 错误：{filepath} - {e}")


if __name__ == '__main__':
    if not os.path.isdir(TARGET_DIR):
        print(f"❌ 目录不存在，请确认路径是否正确: {TARGET_DIR}")
    else:
        walk_and_replace(TARGET_DIR)
        print("\n🎉 全部替换完成！")
