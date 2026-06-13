path = r'C:\Users\popoz\Documents\赚钱项目咸鱼\极简办公\license.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add multi-device save/load functions AFTER save_license
old_save = '''def save_license(machine_code, license_code):
    """保存授权信息到本地"""
    lic_file = _get_license_path()
    try:
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump({
                "machine_code": machine_code,
                "license_code": license_code,
                "activate_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f)
        return True
    except:
        return False'''

new_save = '''def save_license(machine_code, license_code):
    """保存授权信息到本地（支持多设备）"""
    lic_file = _get_license_path()
    try:
        data = {"devices": [], "activate_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if os.path.exists(lic_file):
            try:
                with open(lic_file, "r", encoding="utf-8") as f:
                    old = json.load(f)
                if "devices" in old:
                    data["devices"] = old["devices"]
            except:
                pass
        data["license_code"] = license_code
        # 添加或更新当前设备
        current_mc = machine_code
        found = False
        for d in data["devices"]:
            if d.get("machine_code") == current_mc:
                d["bind_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break
        if not found:
            data["devices"].append({
                "machine_code": current_mc,
                "bind_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def get_device_count():
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            devices = data.get("devices", [])
            return len(devices)
        except:
            pass
    return 0


def add_device_license(machine_code, license_code):
    """将新设备绑定到已有授权
    返回：(成功, 消息)
    """
    lic_file = _get_license_path()
    if not os.path.exists(lic_file):
        return False, "请先在主设备上激活"
    try:
        with open(lic_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing_code = data.get("license_code", "")
        if not existing_code:
            return False, "未检测到授权信息"
        # 验证机器码与现存授权是否匹配
        valid, msg = verify_license(machine_code, existing_code)
        if not valid:
            return False, "授权码与此设备不匹配"
        # 检查是否已绑定
        for d in data.get("devices", []):
            if d.get("machine_code") == machine_code:
                d["bind_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(lic_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True, "设备已重新绑定"
        data["devices"].append({
            "machine_code": machine_code,
            "bind_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"已绑定新设备（共 {len(data['devices'])} 台）"
    except Exception as e:
        return False, f"绑定失败: {str(e)[:50]}"'''

content = content.replace(old_save, new_save)

# 2. Update is_activated to check multi-device
old_activated = '''def is_activated():
    """检查当前电脑是否已激活"""
    mcode, lcode = load_license_file()
    if mcode and lcode:
        valid, _ = verify_license(mcode, lcode)
        if valid and mcode == get_machine_code():
            return True
    return False'''

new_activated = '''def is_activated():
    """检查当前电脑是否已激活（支持多设备）"""
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            lcode = data.get("license_code", "")
            current_mc = get_machine_code()
            # 1. 检查单设备旧格式
            old_mc = data.get("machine_code", "")
            if old_mc and old_mc == current_mc and lcode:
                valid, _ = verify_license(old_mc, lcode)
                if valid:
                    return True
            # 2. 检查多设备格式
            devices = data.get("devices", [])
            for d in devices:
                if d.get("machine_code") == current_mc and lcode:
                    valid, _ = verify_license(current_mc, lcode)
                    if valid:
                        return True
        except:
            pass
    return False'''

content = content.replace(old_activated, new_activated)

# 3. Update load_license_file for backward compat
old_load = '''def load_license_file():
    """从本地加载已保存的授权信息"""
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("machine_code", ""), data.get("license_code", "")
        except:
            pass
    return "", ""'''

new_load = '''def load_license_file():
    """从本地加载已保存的授权信息（兼容新旧格式）"""
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            mc = data.get("machine_code", "")
            lc = data.get("license_code", "")
            # 新格式：从 devices 取当前机器码
            if not mc:
                current = get_machine_code()
                for d in data.get("devices", []):
                    if d.get("machine_code") == current:
                        mc = current
                        break
            return mc, lc
        except:
            pass
    return "", ""'''

content = content.replace(old_load, new_load)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('license.py updated OK')
