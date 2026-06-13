path = r'C:\Users\popoz\Documents\赚钱项目咸鱼\极简办公\keygen.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update title
content = content.replace(
    'tk.Label(main, text="🔑 极简办公 · 解锁码生成器"',
    'tk.Label(main, text="🔑 极简办公 · 解锁码生成器(多设备)"'
)

# Update instruction text
content = content.replace(
    '"提示：将生成的解锁码发给用户即可，输入到极简办公解锁窗口"',
    '"提示：一个解锁码可绑定多台设备，用户在不同电脑输入同一解锁码即可"'
)

# Update pricing info
content = content.replace(
    'text=\"7天体验 9.9元 | 30天 29.9元 | 永久 99元\\n付款后发机器码，秒回解锁码\"',
    'text=\"永久授权 199元（重装可再次申领）\\n一个授权码可绑定多台设备\"'
)

# Update result output to include multi-device note
content = content.replace(
    '说明: 永久有效，不限使用时间',
    '说明: 永久有效，重装系统可再次申领\n一个授权码可绑定多台设备'
)

# Update 30-day result
content = content.replace(
    'self.result_text.insert("end", "说明: 自激活之日起{}内有效\\n".format(label))',
    'self.result_text.insert("end", "说明: 自激活之日起{}内有效\\n".format(label))\n        self.result_text.insert("end", "说明: 一个授权码可绑定多台设备\\n")'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('keygen.py updated OK')
