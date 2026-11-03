"""Interactive Windows-friendly academic research launcher; local operations only."""
import sys
import research_library as lib


def main():
    print('本地学术研究资料库 / Local research library - '+lib.VERSION)
    print('文献、教材、阅读笔记、写作分析与研究项目；不会自动远程连接或上传。')
    value=input('粘贴现有资料库文件夹路径，然后 Enter: ').strip().strip('"')
    if not value: return 1
    while True:
        print('\n1 检查访问    2 创建/补充目录 + 文件索引    3 预览分类')
        print('4 分类复制Inbox（保留原件）    5 更新文件索引    6 搜文件名')
        print('7 建立PDF/TXT/MD全文索引    8 全文关键词检索（带页码）')
        print('9 创建阅读/写作分析卡    10 创建研究项目    11 读取指定原文页    0 退出')
        choice=input('选择 / Choose: ').strip()
        if choice=='0': return 0
        commands={'1':['check'],'2':['setup'],'3':['organize'],'4':['organize','--apply'],
                  '5':['index'],'7':['text-index']}
        if choice=='6': commands['6']=['search',input('文件名关键词: ')]
        elif choice=='8': commands['8']=['find',input('正文关键词（按字面匹配）: ')]
        elif choice in {'9','11'}:
            path=input('资料库内相对路径，例如 07_Textbooks/book.pdf: ').strip().strip('"')
            page=input('PDF页序（从1起；非PDF直接Enter）: ').strip() or '1'
            if not page.isdigit() or int(page)<1:
                print('请输入从1起的整数页序。'); continue
            commands[choice]=['note' if choice=='9' else 'read',path,'--page',page]
        elif choice=='10': commands['10']=['project',input('新项目名称，例如 Conversion_battery: ').strip()]
        if choice not in commands: continue
        code=lib.main(['--root',value,*commands[choice]])
        print('完成；请检查报告中的warnings/限制。' if code==0 else '存在错误：请查看上方报告，不能视为完整成功。')


if __name__=='__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    raise SystemExit(main())
