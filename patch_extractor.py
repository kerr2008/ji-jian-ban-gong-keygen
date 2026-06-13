import re
import os
os.chdir("C:/Users/popoz/Documents/赚钱项目咸鱼")

with open("极简办公/extractor.py", "r", encoding="utf-8") as f:
    t = f.read()

# 在手机号提取后面插入联系人提取
target = 'results["手机号"] = list(dict.fromkeys(p.strip() for p in phones if p.strip()))'
insert = '''
        # 提取手机号对应的联系人信息
        contacts = []
        lines = text.split("\\n")
        for line in lines:
            pm = re.search(PAT_手机号, line)
            if pm:
                phone = pm.group()
                before = line[:pm.start()].strip()
                after_t = line[pm.end():].strip()
                nm = re.search(r"[\\u4e00-\\u9fff]{2,10}$", before)
                name = nm.group() if nm else ""
                pos = re.search(r"^[\\u4e00-\\u9fff]{2,8}", after_t)
                position = pos.group() if pos else ""
                if name or position:
                    contacts.append(phone + " | " + name + (" | " + position if position else ""))
        if contacts:
            results["联系人信息"] = list(dict.fromkeys(contacts))
'''

pos = t.find(target)
if pos >= 0:
    end_pos = pos + len(target)
    t = t[:end_pos] + insert + t[end_pos:]
    with open("极简办公/extractor.py", "w", encoding="utf-8") as f:
        f.write(t)
    print("联系人提取已添加")
else:
    # 找类似内容
    idx = t.find('手机号')
    print(f"手机号位置: {idx}")
    print(t[idx:idx+200])