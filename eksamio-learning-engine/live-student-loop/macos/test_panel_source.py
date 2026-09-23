from pathlib import Path
s=Path(__file__).with_name('EksamioStudentStaging.swift').read_text()
for token in ['kSecClassGenericPassword','%02x','--owner-marker=','verifiedOwner()','healthy(),verifiedOwner()','Date().addingTimeInterval(8)','порт занят неизвестным процессом']:
    assert token in s, token
assert s.index('kill(o.pid,SIGTERM)') < s.index('removeItem(at:ownerFile)')
print('PASS macOS panel source safety')
