"""Interactive launcher; stores no machine-specific root in the code repository."""
import sys
import research_library as lib


def main():
    print('Local research library - version '+lib.VERSION)
    print('This program does not connect ChatGPT remotely or upload files.')
    value=input('Paste your existing library folder path, then Enter: ').strip().strip('"')
    if not value: return 1
    while True:
        print('\n1 Check access  2 Setup folders + index  3 Preview classification')
        print('4 Copy/classify Inbox  5 Refresh index  6 Search filename  0 Exit')
        choice=input('Choose: ').strip()
        if choice=='0': return 0
        commands={'1':['check'],'2':['setup'],'3':['organize'],'4':['organize','--apply'],'5':['index']}
        if choice=='6': commands['6']=['search',input('Filename keyword: ')]
        if choice not in commands: continue
        code=lib.main(['--root',value,*commands[choice]])
        print('Completed.' if code==0 else 'FAILED: read the error above; success was not verified.')


if __name__=='__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    raise SystemExit(main())
