import os

# === 目錄結構定義 ===（已經優化後命名）
folder_structure = {
    "01_癡情": {
        "Images": ["Dark", "Light"],
        "Others": [
            "Allen_Huang", "ED_MOSAIC", "NTR", "Somnus_Wu", "iBras_store",
            "好獵奇", "安佐江", "小籠包", "捷運站美魔女", "水波奶"
        ],
        "Videos": ["1080p", "720p", "SD"]
    },
    "02_廢北": {
        "Images": ["Dark", "Light"],
        "Main": ["Clair", "Cristine", "嘟嘟", "雅美蝶", "Nang"],
        "Videos": ["1080p", "720p"]
    },
    "03_小菲": {
        "小菲影片整理": {
            "L0_Video": [],
            "L1_精采": [],
            "L2_自慰": [],
            "L3_特別": ["VCS", "小孩與狗"],
            "L4_身材好但不精采": [],
            "L5_普通情侶": [],
            "PINAY_KIDS": ["Filter", "Good"],
            "PINAY_SCANDALS": []
        },
        "小菲網路": {
            "微信": [
                "Bbychloe_888", "PamAnderson", "akosichiiklet", "meimei_sb", "yeyefei667788",
                "哈尼/JTV", "哈尼/天秤座", "哈尼/獅子座"
            ],
            "臉書": [
                "Charmel_Kim", "Cutebabytey", "Cy_Cy", "Lovely_Angela_Ong",
                "Mitch_Cer", "Piyanut_Lidala", "SHAINE", "Venus_Aino"
            ]
        }
    }
}

# === 目標根目錄 ===
TARGET_ROOT = os.path.expanduser("~/Downloads/OptimizedStructure")

def create_structure(base, structure):
    for name, content in structure.items():
        current_path = os.path.join(base, name)
        os.makedirs(current_path, exist_ok=True)
        if isinstance(content, dict):
            create_structure(current_path, content)
        elif isinstance(content, list):
            for sub in content:
                sub_path = os.path.join(current_path, sub.replace("/", "_"))  # 防止非法名稱
                os.makedirs(sub_path, exist_ok=True)

if __name__ == "__main__":
    print(f"📁 建立優化後資料夾結構到：{TARGET_ROOT}")
    os.makedirs(TARGET_ROOT, exist_ok=True)
    create_structure(TARGET_ROOT, folder_structure)
    print("✅ 完成！優化結構已建立。")
