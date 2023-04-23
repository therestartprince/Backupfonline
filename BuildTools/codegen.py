#!/usr/bin/python3

print('[CodeGen]', 'Start code generation')

import os
import sys
import argparse
import time
import uuid

startTime = time.time()

parser = argparse.ArgumentParser(description='FOnline code generator', fromfile_prefix_chars='@')
parser.add_argument('-buildhash', dest='buildhash', required=True, help='build hash')
parser.add_argument('-devname', dest='devname', required=True, help='dev game name and version')
parser.add_argument('-gamename', dest='gamename', required=True, help='game name and version')
parser.add_argument('-gameversion', dest='gameversion', required=True, help='game version')
parser.add_argument('-meta', dest='meta', required=True, action='append', help='path to script api metadata (///@ tags)')
parser.add_argument('-multiplayer', dest='multiplayer', action='store_true', help='generate multiplayer api')
parser.add_argument('-singleplayer', dest='singleplayer', action='store_true', help='generate singleplayer api')
parser.add_argument('-markdown', dest='markdown', action='store_true', help='generate api in markdown format')
parser.add_argument('-mdpath', dest='mdpath', default=None, help='path for markdown output')
parser.add_argument('-native', dest='native', action='store_true', help='generate native api')
parser.add_argument('-angelscript', dest='angelscript', action='store_true', help='generate angelscript api')
parser.add_argument('-csharp', dest='csharp', action='store_true', help='generate csharp api')
parser.add_argument('-monoassembly', dest='monoassembly', action='append', default=[], help='assembly name')
parser.add_argument('-monoserverref', dest='monoserverref', action='append', default=[], help='mono assembly server reference')
parser.add_argument('-monoclientref', dest='monoclientref', action='append', default=[], help='mono assembly client reference')
parser.add_argument('-monosingleref', dest='monosingleref', action='append', default=[], help='mono assembly singleplayer reference')
parser.add_argument('-monomapperref', dest='monomapperref', action='append', default=[], help='mono assembly mapper reference')
parser.add_argument('-monoserversource', dest='monoserversource', action='append', default=[], help='csharp server file path')
parser.add_argument('-monoclientsource', dest='monoclientsource', action='append', default=[], help='csharp client file path')
parser.add_argument('-monosinglesource', dest='monosinglesource', action='append', default=[], help='csharp sp file path')
parser.add_argument('-monomappersource', dest='monomappersource', action='append', default=[], help='csharp mapper file path')
parser.add_argument('-content', dest='content', action='append', default=[], help='content file path')
parser.add_argument('-resource', dest='resource', action='append', default=[], help='resource file path')
parser.add_argument('-config', dest='config', action='append', default=[], help='debugging config')
parser.add_argument('-genoutput', dest='genoutput', required=True, help='generated code output dir')
parser.add_argument('-ascontentoutput', dest='ascontentoutput', help='generated angel script content script output dir')
parser.add_argument('-verbose', dest='verbose', action='store_true', help='verbose mode')
args = parser.parse_args()

assert (args.singleplayer or args.multiplayer) and not (args.singleplayer and args.multiplayer), 'Singleplayer/Multiplayer mismatch'

def getGuid(name):
    return '{' + str(uuid.uuid3(uuid.NAMESPACE_OID, name)).upper() + '}'

def getHash(input, seed=0):
    input = input.encode()

    def intTo4Bytes(i):
        return i & 0xffffffff

    m = 0x5bd1e995
    r = 24

    length = len(input)
    h = seed ^ length

    round = 0
    while length >= (round * 4) + 4:
        k = input[round * 4]
        k |= input[(round * 4) + 1] << 8
        k |= input[(round * 4) + 2] << 16
        k |= input[(round * 4) + 3] << 24
        k = intTo4Bytes(k)
        k = intTo4Bytes(k * m)
        k ^= k >> r
        k = intTo4Bytes(k * m)
        h = intTo4Bytes(h * m)
        h ^= k
        round += 1

    lengthDiff = length - (round * 4)

    if lengthDiff == 1:
        h ^= input[-1]
        h = intTo4Bytes(h * m)
    elif lengthDiff == 2:
        h ^= intTo4Bytes(input[-1] << 8)
        h ^= input[-2]
        h = intTo4Bytes(h * m)
    elif lengthDiff == 3:
        h ^= intTo4Bytes(input[-1] << 16)
        h ^= intTo4Bytes(input[-2] << 8)
        h ^= input[-3]
        h = intTo4Bytes(h * m)

    h ^= h >> 13
    h = intTo4Bytes(h * m)
    h ^= h >> 15

    assert h <= 0xffffffff
    if h & 0x80000000 == 0:
        return str(h)
    else:
        return str(-((h ^ 0xFFFFFFFF) + 1))

assert getHash('abcd') == '646393889'
assert getHash('abcde') == '1594468574'
assert getHash('abcdef') == '1271458169'
assert getHash('abcdefg') == '-106836237'

# Generated file list
genFileList = ['EmbeddedResources-Include.h',
        'Version-Include.h',
        'DebugSettings-Include.h',
        'GenericCode-Common.cpp',
        'DataRegistration-Server.cpp',
        'DataRegistration-Client.cpp',
        'DataRegistration-Mapper.cpp',
        'DataRegistration-Single.cpp',
        'DataRegistration-Baker.cpp',
        'DataRegistration-ServerCompiler.cpp',
        'DataRegistration-ClientCompiler.cpp',
        'DataRegistration-MapperCompiler.cpp',
        'DataRegistration-SingleCompiler.cpp',
        'AngelScriptScripting-Server.cpp',
        'AngelScriptScripting-Client.cpp',
        'AngelScriptScripting-Mapper.cpp',
        'AngelScriptScripting-Single.cpp',
        'AngelScriptScripting-ServerCompiler.cpp',
        'AngelScriptScripting-ServerCompilerValidation.cpp',
        'AngelScriptScripting-ClientCompiler.cpp',
        'AngelScriptScripting-MapperCompiler.cpp',
        'AngelScriptScripting-SingleCompiler.cpp',
        'AngelScriptScripting-SingleCompilerValidation.cpp',
        'MonoScripting-Server.cpp',
        'MonoScripting-Client.cpp',
        'MonoScripting-Mapper.cpp',
        'MonoScripting-Single.cpp',
        'NativeScripting-Server.cpp',
        'NativeScripting-Client.cpp',
        'NativeScripting-Mapper.cpp',
        'NativeScripting-Single.cpp']

# Parse meta information
codeGenTags = {
        'ExportEnum': [], # (group name, underlying type, [(key, value, [comment])], [flags], [comment])
        'ExportType': [], # (name, underlying type, representation type, [flags], [comment])
        'ExportProperty': [], # (entity, access, type, name, [flags], [comment])
        'ExportMethod': [], # (target, entity, name, ret, [(type, name)], [flags], [comment])
        'ExportEvent': [], # (target, entity, name, [(type, name)], [flags], [comment])
        'ExportObject': [], # (target, name, [(type, name, [comment])], [(name, ret, [(type, name)], [comment])], [flags], [comment])
        'ExportEntity': [], # (name, serverClassName, clientClassName, [flags], [comment])
        'ExportSettings': [], #(group name, target, [(fixOrVar, keyType, keyName, [initValues], [comment])], [flags], [comment])
        'Entity': [], # (target, name, [flags], [comment])
        'Enum': [], # (group name, underlying type, [(key, value, [comment])], [flags], [comment])
        'PropertyComponent': [], # (entity, name, [flags], [comment])
        'Property': [], # (entity, access, type, name, [flags], [comment])
        'Event': [], # (target, entity, name, [(type, name)], [flags], [comment])
        'RemoteCall': [], # (target, subsystem, ns, name, [(type, name)], [flags], [comment])
        'Setting': [], #(target, type, name, init value, [flags], [comment])
        'EngineHook': [], #(name, [flags], [comment])
        'CodeGen': [] } # (templateType, absPath, entry, line, padding, [flags], [comment])

def verbosePrint(*str):
    if args.verbose:
        print('[CodeGen]', *str)

errors = []

def showError(*messages):
    global errors
    errors.append(messages)
    print('[CodeGen]', str(messages[0]))
    for m in messages[1:]:
        print('[CodeGen]', '-', str(m))

def checkErrors():
    if errors:
        try:
            errorLines = []
            errorLines.append('')
            errorLines.append('#error Code generation failed')
            errorLines.append('')
            errorLines.append('//  Stub generated due to code generation error')
            errorLines.append('//')
            for messages in errors:
                errorLines.append('//  ' + messages[0])
                for m in messages:
                    errorLines.append('//  - ' + str(m))
            errorLines.append('//')
            
            def writeStub(fname):
                with open(args.genoutput.rstrip('/') + '/' + fname, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(errorLines))
            
            for fname in genFileList:
                writeStub(fname)
            
        except Exception as ex:
            showError('Can\'t write stubs', ex)
        
        for e in errors[0]:
            if isinstance(e, BaseException):
                print('[CodeGen]', 'Most recent exception:')
                raise e
        
        sys.exit(1)

# Parse tags
tagsMetas = {}
for k in codeGenTags.keys():
    tagsMetas[k] = []

def parseMetaFile(absPath):
    global tagsMetas
    
    try:
        with open(absPath, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
    except Exception as ex:
        showError('Can\'t read file', absPath, ex)
        return
        
    lastComment = []
    
    for lineIndex in range(len(lines)):
        line = lines[lineIndex]
        lineLen = len(line)
        
        if lineLen < 5:
            continue
        
        try:
            tagPos = -1
            for startPos in range(lineLen):
                if line[startPos] != ' ' and line[startPos] != '\t':
                    tagPos = startPos
                    break
            if tagPos == -1 or lineLen - tagPos < 5 or line[tagPos] != '/' or line[tagPos + 1] != '/' or line[tagPos + 2] != '/':
                continue
            
            tagType = line[tagPos + 3]
            
            if tagType == '#':
                lastComment.append(line[tagPos + 4:].strip())
                
            elif tagType == '@':
                tagStr = line[tagPos + 4:].strip()
                
                commentPos = tagStr.find('//')
                if commentPos != -1:
                    lastComment = [tagStr[commentPos + 2:].strip()]
                    tagStr = tagStr[:commentPos].rstrip()
                
                comment = lastComment if lastComment else []
                
                tagSplit = tagStr.split(' ', 1)
                tagName = tagSplit[0]
                
                if tagName not in tagsMetas:
                    showError('Invalid tag ' + tagName, absPath + ' (' + str(lineIndex + 1) + ')', line.strip())
                    continue
                
                tagInfo = tagSplit[1] if len(tagSplit) > 1 else None
                
                tagContext = None
                if tagName.startswith('Export'):
                    if tagName == 'ExportEnum':
                        for i in range(lineIndex + 1, len(lines)):
                            if lines[i].lstrip().startswith('};'):
                                tagContext = [l.strip() for l in lines[lineIndex + 1 : i] if l.strip()]
                                break
                    elif tagName == 'ExportType':
                        tagContext = True
                    elif tagName == 'ExportProperty':
                        tagContext = lines[lineIndex + 1].strip()
                        for i in range(lineIndex, 0, -1):
                            if lines[i].startswith('class '):
                                propPos = lines[i].find('Properties')
                                assert propPos != -1
                                tagContext = lines[i][6:propPos] + ' ' + lines[lineIndex + 1].strip()
                                break
                    elif tagName == 'ExportMethod':
                        tagContext = lines[lineIndex + 1].strip()
                    elif tagName == 'ExportEvent':
                        for i in range(lineIndex, 0, -1):
                            if lines[i].startswith('class '):
                                className = lines[i][6:lines[i].find(' ', 6)]
                                tagContext = className + ' ' + lines[lineIndex + 1].strip()
                                break
                    elif tagName == 'ExportObject':
                        for i in range(lineIndex + 1, len(lines)):
                            if lines[i].startswith('};'):
                                tagContext = [l.strip() for l in lines[lineIndex + 1 : i] if l.strip()]
                                break
                    elif tagName == 'ExportEntity':
                        tagContext = True
                    elif tagName == 'ExportSettings':
                        for i in range(lineIndex + 1, len(lines)):
                            if lines[i].startswith('SETTING_GROUP_END'):
                                tagContext = [l.strip() for l in lines[lineIndex + 1 : i] if l.strip()]
                                break
                    assert 'Invalid tag context', absPath
                elif tagName == 'EngineHook':
                    tagContext = lines[lineIndex + 1].strip()
                elif tagName == 'CodeGen':
                    tagContext = tagPos
                
                tagsMetas[tagName].append((absPath, lineIndex, tagInfo, tagContext, comment))
                lastComment = []
                
        except Exception as ex:
            showError('Invalid tag format', absPath + ' (' + str(lineIndex + 1) + ')', line.strip(), ex)

metaFiles = []
for path in args.meta:
    absPath = os.path.abspath(path)
    if absPath not in metaFiles and 'GeneratedSource' not in absPath:
        assert os.path.isfile(absPath), 'Invalid meta file path ' + path
        metaFiles.append(absPath)
metaFiles.sort()

for absPath in metaFiles:
    parseMetaFile(absPath)

checkErrors()

userObjects = set()
scriptEnums = set()
engineEnums = set()
customTypes = set()
gameEntities = []
gameEntitiesInfo = {}
entityRelatives = set()
genericFuncdefs = set()
propertyComponents = set()

symTok = set('`~!@#$%^&*()+-=|\\/.,\';][]}{:><"')
def tokenize(text, specialBehForProp=False):
    if text is None:
        return []
    text = text.strip()
    result = []
    curTok = ''
    def flushTok():
        if curTok:
            result.append(curTok)
        return ''
    for ch in text:
        if ch in symTok:
            if specialBehForProp and len(result) in [2, 3]:
                curTok += ch
                continue
            curTok = flushTok()
            curTok = ch
            curTok = flushTok()
        elif ch in ' \t':
            curTok = flushTok()
        else:
            curTok += ch
    curTok = flushTok()
    return result

def parseTags():
    validTypes = set()
    validTypes.update(['int8', 'uint8', 'int16', 'uint16', 'int', 'uint', 'int64', 'uint64',
            'float', 'double', 'string', 'bool', 'Entity', 'void', 'hstring', 'any'])
    
    def unifiedTypeToMetaType(t):
        if t.startswith('init-'):
            return 'init.' + unifiedTypeToMetaType(t[5:])
        if t.startswith('predicate-'):
            return 'predicate.' + unifiedTypeToMetaType(t[10:])
        if t.startswith('callback-'):
            return 'callback.' + unifiedTypeToMetaType(t[9:])
        if t.startswith('ObjInfo-'):
            return t.replace('-', '.')
        if t.startswith('ScriptFunc-'):
            fd = [unifiedTypeToMetaType(a) for a in t[len('ScriptFunc-'):].split('|') if a]
            genericFuncdefs.add('|'.join(fd))
            return 'ScriptFunc.' + '|'.join(fd) + '|'
        if t.endswith('&'):
            return unifiedTypeToMetaType(t[:-1]) + '.ref'
        if '=>' in t:
            tt = t.split('=>')
            return 'dict.' + unifiedTypeToMetaType(tt[0]) + '.' + unifiedTypeToMetaType(tt[1])
        if t.endswith('[]'):
            return 'arr.' + unifiedTypeToMetaType(t[:-2])
        assert t in validTypes, 'Invalid type ' + t
        return t

    def engineTypeToUnifiedType(t):
        typeMap = {'int8': 'int8', 'uint8': 'uint8', 'int16': 'int16', 'uint16': 'uint16',
            'int': 'int', 'uint': 'uint', 'int64': 'int64', 'uint64': 'uint64',
            'int8&': 'int8&', 'uint8&': 'uint8&', 'int16&': 'int16&', 'uint16&': 'uint16&',
            'int&': 'int&', 'uint&': 'uint&', 'int64&': 'int64&', 'uint64&': 'uint64&',
            'float': 'float', 'double': 'double', 'float&': 'float&', 'double&': 'double&',
            'bool': 'bool', 'bool&': 'bool&', 'void': 'void',
            'string&': 'string&', 'const string&': 'string', 'string_view': 'string', 'string': 'string',
            'int8*': 'int8&', 'uint8*': 'uint8&', 'int16*': 'int16&', 'uint16*': 'uint16&',
            'int*': 'int&', 'uint*': 'uint&', 'int64*': 'int64&', 'uint64*': 'uint64&',
            'float*': 'float&', 'double*': 'double&', 'bool*': 'bool&', 'string*': 'string&',
            'hstring': 'hstring', 'hstring&': 'hstring&', 'hstring*': 'hstring&',
            'any_t': 'any', 'any_t&': 'any&', 'any_t*': 'any*'}
        if t.startswith('InitFunc<'):
            r = engineTypeToUnifiedType(t[t.find('<') + 1:t.rfind('>')])
            return 'init-' + r
        elif t.startswith('CallbackFunc<'):
            r = engineTypeToUnifiedType(t[t.find('<') + 1:t.rfind('>')])
            return 'callback-' + r
        elif t.startswith('PredicateFunc<'):
            r = engineTypeToUnifiedType(t[t.find('<') + 1:t.rfind('>')])
            return 'predicate-' + r
        elif t.startswith('ObjInfo<'):
            return 'ObjInfo-' + t[t.find('<') + 1:t.rfind('>')]
        elif t.startswith('ScriptFunc<'):
            fargs = splitEngineArgs(t[t.find('<') + 1:t.rfind('>')])
            return 'ScriptFunc-' + '|'.join([engineTypeToUnifiedType(a.strip()) for a in fargs]) + '|'
        elif t.find('map<') != -1:
            tt = t[t.find('<') + 1:t.rfind('>')].split(',', 1)
            r = engineTypeToUnifiedType(tt[0].strip()) + '=>' + engineTypeToUnifiedType(tt[1].strip())
            if not t.startswith('const') and t.endswith('&'):
                r += '&'
            return r
        elif t.find('vector<') != -1:
            r = engineTypeToUnifiedType(t[t.find('<') + 1:t.rfind('>')]) + '[]'
            if not t.startswith('const') and t.endswith('&'):
                r += '&'
            return r
        elif t[-1] in ['&', '*'] and t[:-1] in customTypes:
            return t
        elif t in validTypes:
            return t
        elif t[-1] == '*' and t not in typeMap:
            tt = t[:-1]
            if tt in userObjects or tt in entityRelatives:
                return tt
            for ename, einfo in gameEntitiesInfo.items():
                if tt == einfo['Server'] or tt == einfo['Client']:
                    return ename
            if tt in ['ServerEntity', 'ClientEntity', 'Entity']:
                return 'Entity'
            assert False, tt
        else:
            assert t in typeMap, 'Invalid engine type ' + t
            return typeMap[t]

    def engineTypeToMetaType(t):
        ut = engineTypeToUnifiedType(t)
        return unifiedTypeToMetaType(ut)

    def splitEngineArgs(fargs):
        result = []
        braces = 0
        r = ''
        for c in fargs:
            if c == ',' and braces == 0:
                result.append(r.strip())
                r = ''
            else:
                r += c
                if c == '<':
                    braces += 1
                elif c == '>':
                    braces -= 1
        assert r.strip()
        result.append(r.strip())
        return result

    def parseTypeTags():
        global codeGenTags
        
        for tagMeta in tagsMetas['ExportEnum']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                exportFlags = tokenize(tagInfo)
                
                firstLine = tagContext[0]
                assert firstLine.startswith('enum class ')
                sep = firstLine.find(':')
                grname = firstLine[len('enum class '):sep if sep != -1 else len(firstLine)].strip()
                utype = engineTypeToMetaType('int' if sep == -1 else firstLine[sep + 1:].strip())
                
                keyValues = []
                assert tagContext[1].startswith('{')
                for l in tagContext[2:]:
                    sep = l.find('=')
                    if sep == -1:
                        keyValues.append((l.rstrip(','), str(int(keyValues[-1][1], 0) + 1) if len(keyValues) else '0', []))
                    else:
                        keyValues.append((l[:sep].rstrip(), l[sep + 1:].lstrip().rstrip(','), []))
                
                codeGenTags['ExportEnum'].append((grname, utype, keyValues, exportFlags, comment))
                assert grname not in validTypes, 'Enum already in valid types'
                validTypes.add(grname)
                assert grname not in engineEnums, 'Enum already in engine enums'
                engineEnums.add(grname)
                
            except Exception as ex:
                showError('Invalid tag ExportEnum', absPath + ' (' + str(lineIndex + 1) + ')', tagContext[0] if tagContext else '(empty)', ex)

        for tagMeta in tagsMetas['ExportType']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                
                name = tok[0]
                utype = tok[1]
                rtype = tok[2]
                exportFlags = tok[3:]
                
                assert rtype in ['RelaxedStrong', 'HardStrong'], 'Wrong type type'
                
                codeGenTags['ExportType'].append((name, utype, rtype, exportFlags, comment))
                assert name not in validTypes, 'Type already in valid types'
                validTypes.add(name)
                assert name not in customTypes, 'Type already in custom types'
                customTypes.add(name)
                
            except Exception as ex:
                showError('Invalid tag ExportType', absPath + ' (' + str(lineIndex + 1) + ')', tagContext[0] if tagContext else '(empty)', ex)

        for tagMeta in tagsMetas['Enum']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                grname = tok[0]
                key = tok[1] if len(tok) > 1 else None
                value = tok[3] if len(tok) > 3 and tok[2] == '=' else None
                flags = tok[2 if len(tok) < 3 or tok[2] != '=' else 4:]
                
                def calcUnderlyingMetaType(kv):
                    if kv:
                        minValue = 0xFFFFFFFF
                        maxValue = -0xFFFFFFFF
                        for i in kv:
                            v = int(i[1], 0)
                            minValue = v if v < minValue else minValue
                            maxValue = v if v > maxValue else maxValue
                        if minValue < 0:
                            return 'int'
                        else:
                            assert maxValue <= 0xFFFFFFFF
                            if maxValue <= 0xFF:
                                return 'uint8'
                            if maxValue <= 0xFFFF:
                                return 'uint16'
                            if maxValue <= 0x7FFFFFFF:
                                return 'int'
                            if maxValue <= 0xFFFFFFFF:
                                return 'uint'
                        assert False, 'Can\'t deduce enum underlying type (' + minValue + ', ' + maxValue + ')'
                    else:
                        return 'uint8'
                
                for g in codeGenTags['Enum']:
                    if g[0] == grname:
                        g[2].append((key, value if value is not None else str(int(g[2][-1][1], 0) + 1), []))
                        g[1] = calcUnderlyingMetaType(g[2])
                        break
                else:
                    keyValues = [(key, value if value is not None else '0', [])]
                    codeGenTags['Enum'].append([grname, calcUnderlyingMetaType(keyValues), keyValues, flags, comment])
                
                    assert grname not in validTypes, 'Enum already in valid types'
                    validTypes.add(grname)
                    assert grname not in scriptEnums, 'Enum already added'
                    scriptEnums.add(grname)
                
            except Exception as ex:
                showError('Invalid tag Enum', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)

        for tagMeta in tagsMetas['ExportObject']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                exportFlags = tokenize(tagInfo)
                assert exportFlags and exportFlags[0] in ['Server', 'Client', 'Mapper', 'Common'], 'Expected target in tag info'
                target = exportFlags[0]
                exportFlags = exportFlags[1:]
                
                firstLine = tagContext[0]
                firstLineTok = tokenize(firstLine)
                assert len(firstLineTok) >= 2, 'Expected 4 or more tokens in first line'
                assert firstLineTok[0] in ['class', 'struct'], 'Expected class/struct'
                
                objName = firstLineTok[1]
                assert objName not in validTypes
                
                assert tagContext[1].startswith('{')
                
                thirdLine = tagContext[2].strip()
                assert thirdLine.startswith('SCRIPTABLE_OBJECT('), 'Expected SCRIPTABLE_OBJECT as first line inside class definition'
                
                publicLines = firstLineTok[0] == 'struct'
                
                fields = []
                methods = []
                for line in tagContext[3:]:
                    line = line.lstrip()
                    if 'private:' in line or 'protected:' in line:
                        publicLines = False
                    elif 'public:' in line in line:
                        publicLines = True
                    elif publicLines:
                        commPos = line.find('//')
                        if commPos != -1:
                            line = line[:commPos]
                        if not line:
                            continue
                        sep = line.find(' ')
                        assert sep != -1
                        lTok = tokenize(line)
                        assert len(lTok) >= 2
                        if lTok[0] != 'void':
                            fields.append((engineTypeToMetaType(lTok[0]), lTok[1], []))
                        else:
                            methods.append((lTok[1], 'void', [], []))
                
                codeGenTags['ExportObject'].append((target, objName, fields, methods, exportFlags, comment))
                
                validTypes.add(objName)
                userObjects.add(objName)
                
            except Exception as ex:
                showError('Invalid tag ExportObject', absPath + ' (' + str(lineIndex + 1) + ')', tagContext[0] if tagContext else '(empty)', ex)
        
        for tagMeta in tagsMetas['ExportEntity']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta

            try:
                exportFlags = tokenize(tagInfo)
                
                name = exportFlags[0]
                serverClassName = exportFlags[1]
                clientClassName = exportFlags[2]
                exportFlags = exportFlags[3:]
                
                codeGenTags['ExportEntity'].append((name, serverClassName, clientClassName, exportFlags, comment))

                assert name not in validTypes           
                validTypes.add(name)
                assert name not in gameEntities
                gameEntities.append(name)
                gameEntitiesInfo[name] = {'Server': serverClassName, 'Client': clientClassName, 'IsGlobal': 'Global' in exportFlags,
                        'HasProto': 'HasProto' in exportFlags, 'HasStatics': 'HasStatics' in exportFlags,
                        'HasAbstract': 'HasAbstract' in exportFlags, 'Exported': True, 'Comment': comment}
                
                assert name + 'Component' not in validTypes, name + 'Property component already in valid types'
                validTypes.add(name + 'Component')
                assert name + 'Component' not in scriptEnums, 'Property component enum already added'
                scriptEnums.add(name + 'Component')
                
                assert name + 'Property' not in validTypes, name + 'Property already in valid types'
                validTypes.add(name + 'Property')
                assert name + 'Property' not in scriptEnums, 'Property enum already added'
                scriptEnums.add(name + 'Property')
                
                if gameEntitiesInfo[name]['HasAbstract']:
                    assert 'Abstract' + name not in validTypes
                    validTypes.add('Abstract' + name)
                    assert 'Abstract' + name not in entityRelatives
                    entityRelatives.add('Abstract' + name)
                
                if gameEntitiesInfo[name]['HasProto']:
                    assert 'Proto' + name not in validTypes
                    validTypes.add('Proto' + name)
                    assert 'Proto' + name not in entityRelatives
                    entityRelatives.add('Proto' + name)
                
                if gameEntitiesInfo[name]['HasStatics']:
                    assert 'Static' + name not in validTypes
                    validTypes.add('Static' + name)
                    assert 'Static' + name not in entityRelatives
                    entityRelatives.add('Static' + name)
                
            except Exception as ex:
                showError('Invalid tag ExportEntity', absPath + ' (' + str(lineIndex + 1) + ')', ex)
        
        for tagMeta in tagsMetas['Entity']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta

            try:
                tok = tokenize(tagInfo)
                target = tok[0]
                name = tok[1]
                flags = tok[2:]
                
                codeGenTags['Entity'].append((target, name, flags, comment))
                
                assert name not in validTypes           
                validTypes.add(name)
                assert name not in gameEntities
                gameEntities.append(name)
                gameEntitiesInfo[name] = {'Server': 'ServerEntity' if target in ['Common', 'Server'] else None,
                        'Client': 'ClientEntity' if target in ['Common', 'Client'] else None,
                        'IsGlobal': 'Global' in flags, 'HasProto': 'HasProto' in flags, 'HasStatics': 'HasStatics' in flags,
                        'HasAbstract': 'HasAbstract' in flags, 'Exported': False, 'Comment': comment}
                
                assert name + 'Component' not in validTypes, name + 'Property component already in valid types'
                validTypes.add(name + 'Component')
                assert name + 'Component' not in scriptEnums, 'Property component enum already added'
                scriptEnums.add(name + 'Component')
                
                assert name + 'Property' not in validTypes, name + 'Property already in valid types'
                validTypes.add(name + 'Property')
                assert name + 'Property' not in scriptEnums, 'Property enum already added'
                scriptEnums.add(name + 'Property')
                
                assert target in ['Server', 'Client']
                assert not gameEntitiesInfo[name]['IsGlobal'], 'Not implemented'
                assert not gameEntitiesInfo[name]['HasProto'], 'Not implemented'
                assert not gameEntitiesInfo[name]['HasStatics'], 'Not implemented'
                assert not gameEntitiesInfo[name]['HasAbstract'], 'Not implemented'
                
                if gameEntitiesInfo[name]['HasAbstract']:
                    assert 'Abstract' + name not in validTypes
                    validTypes.add('Abstract' + name)
                    assert 'Abstract' + name not in entityRelatives
                    entityRelatives.add('Abstract' + name)
                
                if gameEntitiesInfo[name]['HasProto']:
                    assert 'Proto' + name not in validTypes
                    validTypes.add('Proto' + name)
                    assert 'Proto' + name not in entityRelatives
                    entityRelatives.add('Proto' + name)
                
                if gameEntitiesInfo[name]['HasStatics']:
                    assert 'Static' + name not in validTypes
                    validTypes.add('Static' + name)
                    assert 'Static' + name not in entityRelatives
                    entityRelatives.add('Static' + name)
                
            except Exception as ex:
                showError('Invalid tag Entity', absPath + ' (' + str(lineIndex + 1) + ')', ex)
                
    def parseOtherTags():
        global codeGenTags
        
        for tagMeta in tagsMetas['ExportProperty']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
                
            try:    
                exportFlags = tokenize(tagInfo)
                
                entity = tagContext[:tagContext.find(' ')]
                assert entity in gameEntities, entity
                toks = [t.strip() for t in tagContext[tagContext.find('(') + 1:tagContext.find(')')].split(',')]
                access = toks[0]
                assert access in ['PrivateCommon', 'PrivateClient', 'PrivateServer', 'Public', 'PublicModifiable',
                        'PublicFullModifiable', 'Protected', 'ProtectedModifiable', 'VirtualPrivateCommon',
                        'VirtualPrivateClient', 'VirtualPrivateServer', 'VirtualPublic', 'VirtualProtected'], 'Invalid export property access ' + access
                ptype = engineTypeToMetaType(toks[1])
                name = toks[2]
                
                codeGenTags['ExportProperty'].append((entity, access, ptype, name, exportFlags, comment))
                
            except Exception as ex:
                showError('Invalid tag ExportProperty', absPath + ' (' + str(lineIndex + 1) + ')', tagContext, ex)
                
        for tagMeta in tagsMetas['ExportMethod']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                exportFlags = tokenize(tagInfo)
                
                braceOpenPos = tagContext.find('(')
                braceClosePos = tagContext.rfind(')')
                retSpace = tagContext.rfind(' ', 0, braceOpenPos)
                funcName = tagContext[retSpace:braceOpenPos]
                funcArgs = tagContext[braceOpenPos + 1:braceClosePos]
                
                funcTok = funcName.split('_')
                assert len(funcTok) == 3, funcName
                
                target = funcTok[0].strip()
                assert target in ['Server', 'Client', 'Mapper', 'Common'], target
                entity = funcTok[1]
                assert entity in gameEntities, entity
                name = funcTok[2]
                ret = engineTypeToMetaType(tagContext[tagContext.rfind(' ', 0, retSpace - 1):retSpace].strip())
                
                resultArgs = []
                for arg in splitEngineArgs(funcArgs)[1 if entity != 'Global' else 1:]:
                    arg = arg.strip()
                    sep = arg.rfind(' ')
                    argType = engineTypeToMetaType(arg[:sep].rstrip())
                    argName = arg[sep + 1:]
                    resultArgs.append((argType, argName))
                
                codeGenTags['ExportMethod'].append((target, entity, name, ret, resultArgs, exportFlags, comment))
                
            except Exception as ex:
                showError('Invalid tag ExportMethod', absPath + ' (' + str(lineIndex + 1) + ')', tagContext, ex)
                
        for tagMeta in tagsMetas['ExportEvent']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                exportFlags = tokenize(tagInfo)
                
                target = None
                entity = None
                className = tagContext[:tagContext.find(' ')].strip()
                for ename, einfo in gameEntitiesInfo.items():
                    if className == einfo['Server'] or className == einfo['Client']:
                        target, entity = ('Server' if className == einfo['Server'] else 'Client'), ename
                        break
                if className == 'FOMapper':
                    target, entity = 'Mapper', 'Game'
                assert target in ['Server', 'Client', 'Mapper'], target
                
                braceOpenPos = tagContext.find('(')
                braceClosePos = tagContext.rfind(')')
                firstCommaPos = tagContext.find(',', braceOpenPos)
                eventName = tagContext[braceOpenPos + 1:firstCommaPos if firstCommaPos != -1 else braceClosePos].strip()
                
                eventArgs = []
                if firstCommaPos != -1:
                    argsStr = tagContext[firstCommaPos + 1:braceClosePos].strip()
                    if len(argsStr):
                        for arg in splitEngineArgs(argsStr):
                            arg = arg.strip()
                            sep = arg.find('/')
                            argType = engineTypeToMetaType(arg[:sep - 1].rstrip())
                            argName = arg[sep + 2:-2]
                            eventArgs.append((argType, argName))
                
                codeGenTags['ExportEvent'].append((target, entity, eventName, eventArgs, exportFlags, comment))
            
            except Exception as ex:
                showError('Invalid tag ExportEvent', absPath + ' (' + str(lineIndex + 1) + ')', tagContext, ex)

        for tagMeta in tagsMetas['PropertyComponent']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                entity = tok[0]
                assert entity in gameEntities, entity
                
                name = tok[1]
                assert (entity, name) not in propertyComponents, entity + ' component ' + name + ' already added'
                propertyComponents.add((entity, name))
                
                flags = tok[2:]
                
                codeGenTags['PropertyComponent'].append((entity, name, flags, comment))
                
            except Exception as ex:
                showError('Invalid tag PropertyComponent', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
        
        for tagMeta in tagsMetas['Property']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo, True)
                entity = tok[0]
                assert entity in gameEntities, entity
                access = tok[1]
                assert access in ['PrivateCommon', 'PrivateClient', 'PrivateServer', 'Public', 'PublicModifiable',
                        'PublicFullModifiable', 'Protected', 'ProtectedModifiable', 'VirtualPrivateCommon',
                        'VirtualPrivateClient', 'VirtualPrivateServer', 'VirtualPublic', 'VirtualProtected'], 'Invalid property access ' + access
                if tok[2] == 'const':
                    ptype = unifiedTypeToMetaType(tok[3])
                    if len(tok) > 5 and tok[5] == '.':
                        comp = tok[4]
                        name = comp + '.' + tok[6]
                        flags = ['ReadOnly'] + tok[7:]
                    else:
                        comp = None
                        name = tok[4]
                        flags = ['ReadOnly'] + tok[5:]
                else:
                    ptype = unifiedTypeToMetaType(tok[2])
                    if len(tok) > 4 and tok[4] == '.':
                        comp = tok[3]
                        name = comp + '.' + tok[5]
                        flags = tok[6:]
                    else:
                        comp = None
                        name = tok[3]
                        flags = tok[4:]
                
                if comp:
                    assert (entity, comp) in propertyComponents, 'Entity ' + entity + ' does not has component ' + comp
                
                codeGenTags['Property'].append((entity, access, ptype, name, flags, comment))
                
            except Exception as ex:
                showError('Invalid tag Property', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
                
        for tagMeta in tagsMetas['Event']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                
                target = tok[0]
                assert target in ['Server', 'Client', 'Mapper', 'Common'], target
                entity = tok[1]
                assert entity in gameEntities, 'Wrong event entity ' + entity
                eventName = tok[2]
                
                braceOpenPos = tagInfo.find('(')
                braceClosePos = tagInfo.rfind(')')
                eventArgsStr = tagInfo[braceOpenPos + 1:braceClosePos].strip()
                
                eventArgs = []
                if eventArgsStr:
                    for arg in eventArgsStr.split(','):
                        arg = arg.strip()
                        sep = arg.rfind(' ')
                        assert sep != -1, 'No argaument name in event'
                        argType = unifiedTypeToMetaType(arg[:sep].strip())
                        argName = arg[sep + 1:].strip()
                        eventArgs.append((argType, argName))
                
                flags = tokenize(tagInfo[braceClosePos + 1:])
                
                assert not [1 for tag in codeGenTags['Event'] + codeGenTags['ExportEvent'] if tag[0] == target and tag[1] == entity and tag[2] == eventName], \
                        'Event ' + target + ' ' + entity + ' ' + eventName + ' already added'
                
                codeGenTags['Event'].append((target, entity, eventName, eventArgs, flags, comment))
                
            except Exception as ex:
                showError('Invalid tag Event', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
                
        for tagMeta in tagsMetas['RemoteCall']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                target = tok[0]
                assert target in ['Server', 'Client'], target
                funcName = tok[1]
                
                if absPath.endswith('.fos'):
                    subsystem = 'AngelScript'
                elif absPath.endswith('.cs'):
                    subsystem = 'Mono'
                else:
                    assert False, absPath
                
                ns = os.path.splitext(os.path.basename(absPath))[0]
                
                braceOpenPos = tagInfo.find('(')
                braceClosePos = tagInfo.rfind(')')
                funcArgsStr = tagInfo[braceOpenPos + 1:braceClosePos].strip()
                
                funcArgs = []
                if funcArgsStr:
                    for arg in funcArgsStr.split(','):
                        arg = arg.strip()
                        sep = arg.rfind(' ')
                        assert sep != -1, 'Name missed in remote call parameter'
                        argType = unifiedTypeToMetaType(arg[:sep].strip())
                        argName = arg[sep + 1:].strip()
                        funcArgs.append((argType, argName))
                
                flags = tokenize(tagInfo[braceClosePos + 1:])

                codeGenTags['RemoteCall'].append((target, subsystem, ns, funcName, funcArgs, flags, comment))
            
            except Exception as ex:
                showError('Invalid tag RemoteCall', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
        
        for tagMeta in tagsMetas['ExportSettings']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                exportFlags = tokenize(tagInfo)
                assert exportFlags and exportFlags[0] in ['Server', 'Client', 'Mapper', 'Common'], 'Expected target in tag info'
                target = exportFlags[0]
                exportFlags = exportFlags[1:]
                
                firstLine = tagContext[0]
                assert firstLine.startswith('SETTING_GROUP'), 'Invalid start macro'
                grName = firstLine[firstLine.find('(') + 1:firstLine.find(',')]
                assert grName.endswith('Settings'), 'Invalid group ending ' + grName
                grName = grName[:-len('Settings')]
                
                settings = []
                for l in tagContext[1:]:
                    settComment = [l[l.find('//') + 2:].strip()] if l.find('//') != -1 else []
                    settType = l[:l.find('(')]
                    assert settType in ['FIXED_SETTING', 'VARIABLE_SETTING'], 'Invalid setting type ' + settType
                    settArgs = [t.strip().strip('"') for t in l[l.find('(') + 1:l.find(')')].split(',')]
                    settings.append(('fix' if settType == 'FIXED_SETTING' else 'var', engineTypeToMetaType(settArgs[0]), settArgs[1], settArgs[2:], settComment))
                
                codeGenTags['ExportSettings'].append((grName, target, settings, exportFlags, comment))
                
            except Exception as ex:
                showError('Invalid tag ExportSettings', absPath + ' (' + str(lineIndex + 1) + ')', tagContext, ex)
        
        for tagMeta in tagsMetas['Setting']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                tok = tokenize(tagInfo)
                target = tok[0]
                assert target in ['Server', 'Client', 'Common'], 'Invalid target ' + target
                stype = unifiedTypeToMetaType(tok[1])
                isArr = tok[2] == '[' and tok[3] == ']'
                assert stype in ['int', 'uint', 'int8', 'uint8', 'int16', 'uint16', 'int64', 'uint64', 'float', 'double', 'bool', 'string', 'any'] + list(scriptEnums) + list(engineEnums), 'Invalid setting type ' + stype
                if isArr:
                    assert False, 'Arrays not implemented yet'
                    stype = 'arr.' + stype
                    tok = tok[:1] + [stype] + tok[4:]
                name = tok[2]
                value = tok[4] if len(tok) > 4 and tok[3] == '=' else None
                flags = tok[3 if len(tok) < 4 or tok[3] != '=' else 5:]
                
                assert not [1 for tag in codeGenTags['Setting'] if tag[2] == name], 'Setting ' + name + ' already added'
                assert not [1 for tag in codeGenTags['ExportSettings'] if [1 for sett in tag[2] if sett[2] == name]], 'Setting ' + name + ' already added'
                
                codeGenTags['Setting'].append((target, stype, name, value, flags, comment))
                
            except Exception as ex:
                showError('Invalid tag Setting', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
                
        for tagMeta in tagsMetas['EngineHook']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                name = tokenize(tagContext)[1]
                assert name in ['ConfigSectionParseHook', 'ConfigEntryParseHook'], 'Invalid engine hook ' + name
                
                codeGenTags['EngineHook'].append((name, [], comment))
            
            except Exception as ex:
                showError('Invalid tag EngineHook', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
                
        for tagMeta in tagsMetas['CodeGen']:
            absPath, lineIndex, tagInfo, tagContext, comment = tagMeta
            
            try:
                fname = os.path.basename(absPath)
                if fname == 'AngelScriptScripting-Template.cpp':
                    templateType = 'AngelScript'
                elif fname == 'MonoScripting-Template.cpp':
                    templateType = 'Mono'
                elif fname == 'NativeScripting-Template.cpp':
                    templateType = 'Native'
                elif fname == 'DataRegistration-Template.cpp':
                    templateType = 'DataRegistration'
                elif fname == 'GenericCode-Template.cpp':
                    templateType = 'GenericCode'
                else:
                    assert False, fname
                
                flags = tokenize(tagInfo)
                assert len(flags) >= 1, 'Invalid CodeGen entry'
                
                codeGenTags['CodeGen'].append((templateType, absPath, flags[0], lineIndex, tagContext, flags[1:], comment))
            
            except Exception as ex:
                showError('Invalid tag CodeGen', absPath + ' (' + str(lineIndex + 1) + ')', tagInfo, ex)
    
    def postprocessTags():
        # Generate entity property components enums
        for entity in gameEntities:
            keyValues = [('Invalid', '0', [])]
            for propCompTag in codeGenTags['PropertyComponent']:
                ent, name, flags, _ = propCompTag
                if ent == entity:
                    keyValues.append((name, getHash(name), []))
            codeGenTags['Enum'].append([entity + 'Component', 'int', keyValues, [], []])
        
        # Generate entity properties enums
        for entity in gameEntities:
            keyValues = [('Invalid', '0xFFFF', [])]
            index = 0
            for propTag in codeGenTags['ExportProperty'] + codeGenTags['Property']:
                ent, _, _, name, _, _ = propTag
                if ent == entity:
                    name = name.replace('.', '_')
                    keyValues.append((name, str(index), []))
                    index += 1
            codeGenTags['Enum'].append([entity + 'Property', 'uint16', keyValues, [], []])
        
        # Check for zero key entry in enums
        for e in codeGenTags['ExportEnum'] + codeGenTags['Enum']:
            gname, _, keyValues, _, _ = e
            if not [1 for kv in keyValues if int(kv[1], 0) == 0]:
                showError('Zero entry not found in enum group ' + gname)
        
        # Check uniquiness of enums
        for e in codeGenTags['ExportEnum'] + codeGenTags['Enum']:
            gname, _, keyValues, _, _ = e
            keys = set()
            values = set()
            for kv in keyValues:
                if kv[0] in keys:
                    showError('Detected collision in enum group ' + gname + ' key ' + kv[0])
                if int(kv[1], 0) in values:
                    showError('Detected collision in enum group ' + gname + ' value ' + kv[1] + (' (evaluated to ' + str(int(kv[1], 0)) + ')' if str(int(kv[1], 0)) != kv[1] else ''))
                keys.add(kv[0])
                values.add(int(kv[1], 0))
    
    parseTypeTags()
    parseOtherTags()
    postprocessTags()

parseTags()
checkErrors()
tagsMetas = {} # Cleanup memory

# Parse content
content = { 'fos': [], 'foitem': [], 'focr': [], 'fomap': [], 'foloc': [], 'fodlg': [], 'fotxt': [] }

for contentDir in args.content:
    try:
        def collectFiles(dir):
            result = []
            for file in os.listdir(dir):
                fileParts = os.path.splitext(file)
                if len(fileParts) > 1 and fileParts[1][1:] in content:
                    result.append(dir + '/' + file)
            return result
        
        for file in collectFiles(contentDir):
            def getPidNames(file):
                baseName, ext = os.path.splitext(os.path.basename(file))
                result = [baseName]
                if ext in ['.foitem', '.focr']:
                    verbosePrint('getPidNames', file)
                    with open(file, 'r', encoding='utf-8-sig') as f:
                        try:
                            fileLines = f.readlines()
                        except Exception as ex:
                            print('[CodeGen]', 'Bad file', file)
                            raise
                    for fileLine in fileLines:
                        if fileLine.startswith('$Name'):
                            innerName = fileLine[fileLine.find('=') + 1:].strip(' \r\n')
                            if innerName != baseName:
                                result.append(innerName)
                return result
            
            ext = os.path.splitext(os.path.basename(file))[1]
            content[ext[1:]].extend(getPidNames(file))
    
    except Exception as ex:
        showError('Can\'t process content dir ' + contentDir, ex)

for key in content.keys():
    content[key].sort()

checkErrors()

# Parse resources
resources = {}

"""
for resourceEntry in args.resource:
    try:
        def collectFiles(dir, arcDir):
            result = []
            for entry in os.listdir(dir):
                entryPath = os.path.abspath(os.path.join(dir, entry))
                if os.path.isdir(entryPath):
                    result.extend(collectFiles(entryPath, arcDir + '/' + entry))
                elif os.path.isfile(entryPath):
                    result.append(((arcDir + '/' + entry).lstrip('/'), entryPath))
            return result        
        
        resType, resDir = resourceEntry.split(',', 1)
        resDir = os.path.abspath(resDir)
        
        if resType not in resources:
            resources[resType] = []
        
        if os.path.isdir(resDir):
            resources[resType].extend(collectFiles(resDir, ''))
        elif os.path.isfile(resDir):
            resources[resType].extend(resDir)
    
    except Exception as ex:
        showError('Can\'t process resources entry ' + resourceEntry, ex)

for key in resources.keys():
    resources[key].sort(key=lambda x: x[0])

checkErrors()
"""

# Generate API
files = {}
lastFile = None
genFileNames = []

def createFile(name, output):
    assert output
    path = os.path.join(output, name)
    genFileNames.append(name)
    
    global lastFile
    lastFile = []
    files[path] = lastFile

def writeFile(line):
    lastFile.append(line)

def insertFileLines(lines, lineIndex):
    assert lineIndex <= len(lastFile), 'Invalid line index'
    lastFileCopy = lastFile[:]
    lastFileCopy = lastFileCopy[:lineIndex] + lines + lastFileCopy[lineIndex:]
    lastFile.clear()
    lastFile.extend(lastFileCopy)

def flushFiles():
    # Generate stubs missed files
    for fname in genFileList:
        if fname not in genFileNames:
            createFile(fname, args.genoutput)
            writeFile('// Empty file')
            verbosePrint('flushFiles', 'empty', fname)
    
    # Write if content changed
    for path, lines in files.items():
        pathDir = os.path.dirname(path)
        if not os.path.isdir(pathDir):
            os.makedirs(pathDir)
        
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8-sig') as f:
                curLines = f.readlines()
            newLinesStr = ''.join([l.rstrip('\r\n') for l in curLines]).rstrip()
            curLinesStr = ''.join(lines).rstrip()
            if newLinesStr == curLinesStr:
                verbosePrint('flushFiles', 'skip', path)
                continue
            else:
                verbosePrint('flushFiles', 'diff found', path, len(newLinesStr), len(curLinesStr))
        else:
            verbosePrint('flushFiles', 'no file', path)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines).rstrip('\n') + '\n')
        verbosePrint('flushFiles', 'write', path)

# Code
curCodeGenTemplateType = None

def writeCodeGenTemplate(templateType):
    global curCodeGenTemplateType
    curCodeGenTemplateType = templateType
    
    templatePath = None
    for genTag in codeGenTags['CodeGen']:
        if curCodeGenTemplateType == genTag[0]:
            templatePath = genTag[1]
            break
    assert templatePath, 'Code gen template not found'
    
    with open(templatePath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    insertFileLines([l.rstrip('\r\n') for l in lines], 0)

def insertCodeGenLines(lines, entryName):
    def findTag():
        for genTag in codeGenTags['CodeGen']:
            if curCodeGenTemplateType == genTag[0] and entryName == genTag[2]:
                return genTag[3] + 1, genTag[4]
        assert False, 'Code gen entry ' + entryName + ' in ' + curCodeGenTemplateType + ' not found'
    lineIndex, padding = findTag()
    
    if padding:
        lines = [''.center(padding) + l for l in lines]
    
    insertFileLines(lines, lineIndex)

def getEntityFromTarget(target):
    if target == 'Server':
        return 'ServerEntity*'
    if target in ['Client', 'Mapper']:
        return 'ClientEntity*'
    return 'Entity*'

def metaTypeToUnifiedType(t):
    tt = t.split('.')
    if tt[0] == 'dict':
        d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
        r = metaTypeToUnifiedType(tt[1]) + '=>' + metaTypeToUnifiedType(d2)
    elif tt[0] == 'arr':
        r = '' + metaTypeToUnifiedType(tt[1]) + '[]'
    elif tt[0] == 'init':
        r = 'init-' + metaTypeToUnifiedType(tt[1])
    elif tt[0] == 'callback':
        r = 'callback-' + metaTypeToUnifiedType(tt[1])
    elif tt[0] == 'predicate':
        r = 'predicate-' + metaTypeToUnifiedType(tt[1])
    elif tt[0] == 'ObjInfo':
        return 'ObjInfo-' + tt[1]
    elif tt[0] == 'ScriptFunc':
        return 'ScriptFunc-' + ', '.join([metaTypeToUnifiedType(a) for a in '.'.join(tt[1:]).split('|') if a])
    elif tt[0] == 'Entity':
        r = tt[0]
    elif tt[0] in gameEntities:
        r = tt[0]
    elif tt[0] in scriptEnums:
        r = tt[0]
    elif tt[0] in userObjects or tt[0] in entityRelatives:
        r = tt[0]
    else:
        def mapType(mt):
            typeMap = {'int8': 'int8', 'uint8': 'uint8', 'int16': 'int16', 'uint16': 'uint16', 'int': 'int', 'uint': 'uint', 'int64': 'int64', 'uint64': 'uint64'}
            return typeMap[mt] if mt in typeMap else mt
        r = mapType(tt[0])
    if tt[-1] == 'ref':
        r += '&'
    return r

def metaTypeToEngineType(t, target, passIn, refAsPtr=False):
    tt = t.split('.')
    if tt[0] == 'dict':
        d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
        r = 'map<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToEngineType(d2, target, False) + '>'
    elif tt[0] == 'arr':
        r = 'vector<' + metaTypeToEngineType(tt[1], target, False) + '>'
    elif tt[0] == 'init':
        assert passIn
        r = 'InitFunc<' + metaTypeToEngineType(tt[1], target, False) + '>'
    elif tt[0] == 'callback':
        assert passIn
        r = 'CallbackFunc<' + metaTypeToEngineType(tt[1], target, False) + '>'
    elif tt[0] == 'predicate':
        assert passIn
        r = 'PredicateFunc<' + metaTypeToEngineType(tt[1], target, False) + '>'
    elif tt[0] == 'ObjInfo':
        return 'ObjInfo<' + tt[1] + '>'
    elif tt[0] == 'ScriptFunc':
        return 'ScriptFunc<' + ', '.join([metaTypeToEngineType(a, target, False, refAsPtr=True) for a in '.'.join(tt[1:]).split('|') if a]) + '>'
    elif tt[0] == 'Entity':
        return getEntityFromTarget(target)
    elif tt[0] in gameEntities:
        if target != 'Server':
            r = gameEntitiesInfo[tt[0]]['Client'] + '*'
            if tt[0] == 'Game' and target == 'Mapper':
                r = 'FOMapper*'
        else:
            r = gameEntitiesInfo[tt[0]]['Server'] + '*'
    elif tt[0] in scriptEnums:
        for e in codeGenTags['Enum']:
            if e[0] == tt[0]:
                return 'ScriptEnum_' + e[1]
        assert False, 'Enum not found ' + tt[0]
    elif tt[0] in userObjects or tt[0] in entityRelatives:
        r = tt[0] + '*'
    else:
        def mapType(mt):
            typeMap = {'int8': 'int8', 'uint8': 'uint8', 'int16': 'int16', 'uint16': 'uint16',
                       'int': 'int', 'uint': 'uint', 'int64': 'int64', 'uint64': 'uint64',
                       'any': 'any_t'}
            return typeMap[mt] if mt in typeMap else mt
        r = mapType(tt[0])
    if tt[-1] == 'ref':
        r += '&' if not refAsPtr else '*'
    elif passIn:
        if r == 'string':
            r = 'string_view'
        elif tt[0] in ['arr', 'dict']:
            r = 'const ' + r + '&'
    return r

def genGenericCode():
    globalLines = []
    
    # Engine hooks
    def isHookEnabled(hookName):
        for hookTag in codeGenTags['EngineHook']:
            name, flags, _ = hookTag
            if name == hookName:
                return True
        return False
    
    globalLines.append('// Engine hooks')
    if not isHookEnabled('ConfigSectionParseHook'):
        globalLines.append('void ConfigSectionParseHook(const string&, string&, map<string, string>&) { /* Stub */ }')
    if not isHookEnabled('ConfigEntryParseHook'):
        globalLines.append('void ConfigEntryParseHook(const string&, const string&, string&, string&) { /* Stub */ }')
    globalLines.append('')
    
    # Engine properties
    globalLines.append('// Engine property indices')
    globalLines.append('#include "EntityProperties.h"')
    globalLines.append('EntityProperties::EntityProperties(Properties& props) : _propsRef(props) { }')
    for entity in gameEntities:
        index = 0
        for propTag in codeGenTags['ExportProperty']:
            ent, _, _, name, _, _ = propTag
            if ent == entity:
                globalLines.append('uint16 ' + entity + 'Properties::' + name + '_RegIndex = ' + str(index) + ';')
                index += 1
    globalLines.append('')
    
    # Settings list
    def writeSettings(target):
        globalLines.append('[[maybe_unused]] auto Get' + target + 'Settings() -> unordered_set<string>')
        globalLines.append('{')
        globalLines.append('    unordered_set<string> settings = {')
        for settTag in codeGenTags['ExportSettings']:
            grName, targ, settings, flags, _ = settTag
            if targ in [target, 'Common']:
                for sett in settings:
                    fixOrVar, keyType, keyName, initValues, _ = sett
                    globalLines.append('        "' + keyName + '",')
        for settTag in codeGenTags['Setting']:
            targ, type, name, initValue, flags, _ = settTag
            if targ in [target, 'Common']:
                globalLines.append('        "' + name + '",')
        globalLines.append('    };')
        globalLines.append('    return settings;')
        globalLines.append('}')
        globalLines.append('')
    writeSettings('Server')
    writeSettings('Client')
    
    createFile('GenericCode-Common.cpp', args.genoutput)
    writeCodeGenTemplate('GenericCode')
    
    insertCodeGenLines(globalLines, 'Body')

try:
    genGenericCode()
except Exception as ex:
    showError('Code generation for generic code failed', ex)
checkErrors()

def genDataRegistration(target, isASCompiler):
    globalLines = []
    registerLines = []
    restoreLines = []
    
    def entityAllowed(entity, entityTarget):
        if entityTarget == 'Server':
            return gameEntitiesInfo[entity]['Server'] is not None
        if entityTarget in ['Client', 'Mapper']:
            return gameEntitiesInfo[entity]['Client'] is not None
        if entityTarget in ['Baker', 'Single']:
            return True
        assert False, entityTarget
    
    # Enums
    registerLines.append('// Enums')
    for e in codeGenTags['ExportEnum']:
        gname, utype, keyValues, _, _ = e
        registerLines.append('engine->AddEnumGroup("' + gname + '", typeid(' + metaTypeToEngineType(utype, target, False) + '),')
        registerLines.append('{')
        for kv in keyValues:
            registerLines.append('    {"' + kv[0] + '", ' + kv[1] + '},')
        registerLines.append('});')
        registerLines.append('')
    if target != 'Client' or isASCompiler:
        for e in codeGenTags['Enum']:
            gname, utype, keyValues, _, _ = e
            registerLines.append('engine->AddEnumGroup("' + gname + '", typeid(' + metaTypeToEngineType(utype, target, False) + '),')
            registerLines.append('{')
            for kv in keyValues:
                registerLines.append('    {"' + kv[0] + '", ' + kv[1] + '},')
            registerLines.append('});')
            registerLines.append('')
    
    # Property registrators
    registerLines.append('// Properties')
    registerLines.append('unordered_map<string, PropertyRegistrator*> registrators;')
    registerLines.append('PropertyRegistrator* registrator;')
    registerLines.append('')
    for entity in gameEntities:
        if not entityAllowed(entity, target):
            continue
        registerLines.append('registrators["' + entity + '"] = engine->GetOrCreatePropertyRegistrator("' + entity + '");')
    registerLines.append('')
    
    # Properties
    def getRegisterFlags(t, name, access, baseFlags):
        def getUnderlyingType(t):
            if t in engineEnums:
                for e in codeGenTags['ExportEnum']:
                    if e[0] == t:
                        return e[1]
                assert False, 'Invalid underlying type ' + t
            if t in scriptEnums:
                for e in codeGenTags['Enum']:
                    if e[0] == t:
                        return e[1]
                assert False, 'Invalid underlying type ' + t
            if t in customTypes:
                for e in codeGenTags['ExportType']:
                    if e[0] == t:
                        return e[1]
                assert False, 'Invalid underlying type ' + t
            if t == 'hstring':
                return 'uint'
            return t if t in ['int8', 'uint8', 'int16', 'uint16', 'int', 'uint', 'bool', 'float', 'double'] else None
        def getTypeSize(t):
            if t in ['int8', 'uint8', 'bool']:
                return '1'
            elif t in ['int16', 'uint16']:
                return '2'
            elif t in ['int', 'uint', 'float']:
                return '4'
            elif t in ['int64', 'uint64', 'double']:
                return '8'
            elif t is None:
                return '0'
            else:
                assert False, 'Unknown type size ' + t
        tt = t.split('.')
        bt = tt[-1]
        if tt[0] == 'dict':
            dt = 'Dict'
        elif tt[0] == 'arr':
            dt = 'Array'
        elif bt in ['string', 'any']:
            dt = 'String'
        else:
            dt = 'PlainData'
        ut = getUnderlyingType(bt)
        r = [name, access, dt, bt]
        r.append(getTypeSize(ut)) # type size
        r.append('1' if bt == 'hstring' else '0') # is hash
        r.append('1' if bt in scriptEnums | engineEnums else '0') # is enum
        r.append('1' if ut in ['int8', 'uint8', 'int16', 'uint16', 'int', 'uint', 'int64', 'uint64'] else '0') # is int
        r.append('1' if ut in ['int8', 'int16', 'int', 'int64'] else '0') # is signed int
        r.append('1' if ut in ['float', 'double'] else '0') # is float
        r.append('1' if ut in ['bool'] else '0') # is bool
        if dt == 'Array':
            r.append('1' if bt in ['string', 'any'] else '0') # is array of string
        elif dt == 'Dict':
            btKey = tt[1]
            isDictArr = tt[2] == 'arr'
            r.append('1' if isDictArr else '0') # is dict of array
            r.append('1' if not isDictArr and bt in ['string', 'any'] else '0') # is dict of string
            r.append('1' if isDictArr and bt in ['string', 'any'] else '0') # is dict of array of string
            utKey = getUnderlyingType(btKey)
            r.append(btKey) # key type name
            r.append(getTypeSize(utKey)) # key size
            r.append('1' if btKey == 'hstring' else '0') # is key hash
            r.append('1' if btKey in scriptEnums | engineEnums else '0') # is key enum
        return r + baseFlags
    for entity in gameEntities:
        if not entityAllowed(entity, target):
            continue
        registerLines.append('registrator = registrators["' + entity + '"];')
        if target != 'Client' or isASCompiler:
            for propCompTag in codeGenTags['PropertyComponent']:
                ent, name, flags, _ = propCompTag
                if entity == ent:
                    registerLines.append('registrator->RegisterComponent("' + name + '");')
        for propTag in codeGenTags['ExportProperty']:
            ent, access, type, name, flags, _ = propTag
            if ent == entity:
                registerLines.append('registrator->RegisterProperty({' + ', '.join(['"' + f + '"' for f in getRegisterFlags(type, name, access, flags)]) + '});')
        if target != 'Client' or isASCompiler:
            for propTag in codeGenTags['Property']:
                ent, access, type, name, flags, _ = propTag
                if ent == entity:
                    registerLines.append('registrator->RegisterProperty({' + ', '.join(['"' + f + '"' for f in getRegisterFlags(type, name, access, flags)]) + '});')
        registerLines.append('')
    
    # Restore enums info
    if target == 'Baker' and not isASCompiler:
        restoreLines.append('restore_info["Enums"] =')
        restoreLines.append('{')
        for e in codeGenTags['Enum']:
            gname, utype, keyValues, _, _ = e
            if keyValues:
                restoreLines.append('    "' + gname + ' ' + utype + '"')
                for kv in keyValues[:-1]:
                    restoreLines.append('    " ' + kv[0] + '=' + kv[1] + '"')
                restoreLines.append('    " ' + keyValues[-1][0] + '=' + keyValues[-1][1] + '",')
            else:
                restoreLines.append('    "' + gname + ' ' + utype + '",')
        restoreLines.append('};')
        restoreLines.append('')
    
    # Restore properties info
    if target == 'Baker' and not isASCompiler:
        restoreLines.append('restore_info["PropertyComponents"] =')
        restoreLines.append('{')
        for propCompTag in codeGenTags['PropertyComponent']:
            entity, name, flags, _ = propCompTag
            if not entityAllowed(entity, 'Client'):
                continue
            restoreLines.append('    "' + entity + ' ' + name + '",')
        restoreLines.append('};')
        restoreLines.append('')
        
        def replaceFakedEnum(t):
            tt = t.split('.')
            if tt[0] == 'dict':
                return 'dict.' + replaceFakedEnum(tt[1]) + '.' + replaceFakedEnum('.'.join(tt[2:]))
            if tt[0] == 'arr':
                return 'arr.' + replaceFakedEnum(tt[1])
            if tt[0] in scriptEnums or tt[0] in engineEnums:
                return metaTypeToEngineType(tt[0], target, False)
            return tt[0]
        dummyIndex = 0
        restoreLines.append('restore_info["Properties"] =')
        restoreLines.append('{')
        for e in codeGenTags['Property']:
            entity, access, type, name, flags, _ = e
            if not entityAllowed(entity, 'Client'):
                continue
            if access not in ['PrivateServer', 'VirtualPrivateServer']:
                restoreLines.append('    "' + entity + ' ' + ' '.join(getRegisterFlags(type, name, access, flags)) + '",')
            else:
                restoreLines.append('    "' + entity + ' ' + ' '.join(getRegisterFlags(type, '__dummy' + str(dummyIndex), access, flags)) + '",')
                dummyIndex += 1
        restoreLines.append('};')
        restoreLines.append('')
    
    # Todo: make script events restorable
    # Restore events info
    #if target == 'Baker' and not isASCompiler:
    #    restoreLines.append('restore_info["Events"] =')
    #    restoreLines.append('{')
    #    for entity in gameEntities:
    #        for evTag in codeGenTags['Event']:
    #            targ, ent, evName, evArgs, evFlags, _ = evTag
    #            if targ in ['Client', 'Common'] and ent == entity:
    #                restoreLines.append('    "' + entity + ' ' + evName + ' ' + ' '.join([a[0] + ' ' + (a[1] if a[1] else '_') for a in evArgs]) +
    #                        (' | ' if evFlags else '') + ' '.join(evFlags) + '",')
    #    restoreLines.append('};')
    #    restoreLines.append('')
    
    # Todo: make setting values restorable
    # Restore settings
    #if target == 'Baker' and not isASCompiler:
    #    restoreLines.append('restore_info["Settings"] =')
    #    restoreLines.append('{')
    #    for settTag in codeGenTags['ExportSettings']:
    #        grName, targ, settings, flags, _ = settTag
    #        if targ in ['Common', 'Client']:
    #            for sett in settings:
    #                fixOrVar, keyType, keyName, initValues, _ = sett
    #                restoreLines.append('    "' + grName + ' ' + fixOrVar + ' ' + keyType + ' ' + keyName + (' ' if flags else '') + ' '.join(flags) + (' |' + ' '.join(initValues) if initValues else '') + '",')
    #    for settTag in codeGenTags['Setting']:
    #        targ, type, name, initValue, flags, _ = settTag
    #        restoreLines.append('    "Script fix ' + type + ' ' + name + (' ' if flags else '') + ' '.join(flags) + (' |' + initValue if initValue is not None else '') + '",')
    #    restoreLines.append('};')
    #    restoreLines.append('')
    
    createFile('DataRegistration-' + target + ('Compiler' if isASCompiler else '') + '.cpp', args.genoutput)
    writeCodeGenTemplate('DataRegistration')
    
    if not isASCompiler:
        if target == 'Server':
            insertCodeGenLines(registerLines, 'ServerRegister')
            insertCodeGenLines(globalLines, 'Global')
        elif target == 'Client':
            insertCodeGenLines(registerLines, 'ClientRegister')
            insertCodeGenLines(globalLines, 'Global')
        elif target == 'Single':
            insertCodeGenLines(registerLines, 'SingleRegister')
            insertCodeGenLines(globalLines, 'Global')
        elif target == 'Mapper':
            insertCodeGenLines(registerLines, 'MapperRegister')
            insertCodeGenLines(globalLines, 'Global')
        elif target == 'Baker':
            insertCodeGenLines(restoreLines, 'WriteRestoreInfo')
            insertCodeGenLines(registerLines, 'BakerRegister')
            insertCodeGenLines(globalLines, 'Global')
    else:
        insertCodeGenLines(registerLines, 'CompilerRegister')
        insertCodeGenLines(globalLines, 'Global')
    
    if target == 'Server':
        insertCodeGenLines(['#define SERVER_REGISTRATION 1', '#define CLIENT_REGISTRATION 0', '#define SINGLE_REGISTRATION 0',
                '#define MAPPER_REGISTRATION 0', '#define BAKER_REGISTRATION 0', '#define COMPILER_MODE ' + ('1' if isASCompiler else '0')], 'Defines')
    elif target == 'Client':
        insertCodeGenLines(['#define SERVER_REGISTRATION 0', '#define CLIENT_REGISTRATION 1', '#define SINGLE_REGISTRATION 0',
                '#define MAPPER_REGISTRATION 0', '#define BAKER_REGISTRATION 0', '#define COMPILER_MODE ' + ('1' if isASCompiler else '0')], 'Defines')
    elif target == 'Single':
        insertCodeGenLines(['#define SERVER_REGISTRATION 0', '#define CLIENT_REGISTRATION 0', '#define SINGLE_REGISTRATION 1',
                '#define MAPPER_REGISTRATION 0', '#define BAKER_REGISTRATION 0', '#define COMPILER_MODE ' + ('1' if isASCompiler else '0')], 'Defines')
    elif target == 'Mapper':
        insertCodeGenLines(['#define SERVER_REGISTRATION 0', '#define CLIENT_REGISTRATION 0', '#define SINGLE_REGISTRATION 0',
                '#define MAPPER_REGISTRATION 1', '#define BAKER_REGISTRATION 0', '#define COMPILER_MODE ' + ('1' if isASCompiler else '0')], 'Defines')
    elif target == 'Baker':
        assert not isASCompiler
        insertCodeGenLines(['#define SERVER_REGISTRATION 0', '#define CLIENT_REGISTRATION 0', '#define SINGLE_REGISTRATION 0',
                '#define MAPPER_REGISTRATION 0', '#define BAKER_REGISTRATION 1', '#define COMPILER_MODE 0'], 'Defines')

try:
    genDataRegistration('Baker', False)
    
    genDataRegistration('Mapper', False)
    if args.angelscript:
        genDataRegistration('Mapper', True)
    
    if args.multiplayer:
        genDataRegistration('Server', False)
        genDataRegistration('Client', False)
        if args.angelscript:
            genDataRegistration('Server', True)
            genDataRegistration('Client', True)
    
    if args.singleplayer:
        genDataRegistration('Single', False)
        if args.angelscript:
            genDataRegistration('Single', True)
    
except Exception as ex:
    showError('Code generation for data registration failed', ex)
    
checkErrors()

def genCode(lang, target, isASCompiler=False, isASCompilerValidation=False):
    createFile(lang + 'Scripting' + '-' + target + ('Compiler' if isASCompiler else '') + ('Validation' if isASCompiler and isASCompilerValidation else '') + '.cpp', args.genoutput)
    
    # Make stub for disabled script system
    if (lang == 'AngelScript' and not args.angelscript) or (lang == 'Mono' and not args.csharp) or (lang == 'Native' and not args.native):
        if isASCompiler:
            writeFile('struct ' + target + 'ScriptSystem { void InitAngelScriptScripting(string_view); };')
            writeFile('void ' + target + 'ScriptSystem::InitAngelScriptScripting(string_view) { }')
        else:
            writeFile('#include "' + target + 'Scripting.h"')
            writeFile('void ' + target + 'ScriptSystem::Init' + lang + 'Scripting() { }')
        
        return
    
    # Generate from template
    writeCodeGenTemplate(lang)

    if lang == 'AngelScript':
        def metaTypeToASEngineType(t, ret = False):
            tt = t.split('.')
            if tt[0] == 'arr':
                return 'CScriptArray*'
            elif tt[0] == 'dict':
                return 'CScriptDict*'
            elif tt[0] in ['init', 'callback', 'predicate']:
                return 'asIScriptFunction*'
            elif tt[0] == 'Entity':
                return getEntityFromTarget(target)
            elif tt[0] in gameEntities:
                if target != 'Server':
                    return gameEntitiesInfo[tt[0]]['Client'] + '*'
                else:
                    return gameEntitiesInfo[tt[0]]['Server'] + '*'
            elif tt[0] in userObjects or tt[0] in entityRelatives:
                return tt[0] + '*'
            elif tt[0] in scriptEnums or tt[0] in engineEnums:
                r = 'int'
            elif tt[0] == 'ObjInfo':
                return '[[maybe_unused]] void* obj' + tt[1] + 'Ptr, int'
            elif tt[0] == 'ScriptFunc':
                return 'asIScriptFunction*'
            else:
                def mapType(t):
                    typeMap = {'int8': 'int8', 'uint8': 'uint8', 'int16': 'int16', 'uint16': 'uint16',
                               'int': 'int', 'uint': 'uint', 'int64': 'int64', 'uint64': 'uint64',
                               'any': 'any_t'}
                    return typeMap[t] if t in typeMap else t
                r = mapType(tt[0])
            if tt[-1] == 'ref':
                if r[-1] == '*':
                    r = r[:-1]
                r += '&'
            return r
        
        def metaTypeToASType(t, noHandle = False, isRet = False, forceNoConst = False):
            def getHandle():
                if noHandle:
                    return ''
                if not isRet:
                    return '@+'
                return '@' if t.split('.')[0] in ['arr', 'dict'] else '@+'
            tt = t.split('.')
            noHandle = noHandle or tt[-1] == 'ref'
            if tt[0] == 'dict':
                d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
                r = 'dict<' + metaTypeToASType(tt[1], True) + ', ' + metaTypeToASType(d2, True) + '>' + getHandle()
                r = 'const ' + r if not isRet and not noHandle and not forceNoConst else r
            elif tt[0] == 'arr':
                r = metaTypeToASType(tt[1], True) + '[]' + getHandle()
                r = 'const ' + r if not isRet and not noHandle and not forceNoConst else r
            elif tt[0] == 'init':
                r = metaTypeToASType(tt[1], True) + 'InitFunc' + getHandle()
            elif tt[0] == 'callback':
                r = metaTypeToASType(tt[1], True) + 'Callback' + getHandle()
            elif tt[0] == 'predicate':
                r = metaTypeToASType(tt[1], True) + 'Predicate' + getHandle()
            elif tt[0] == 'Entity':
                r = 'Entity' + getHandle()
            elif tt[0] in gameEntities:
                r = tt[0] + getHandle()
            elif tt[0] in engineEnums or tt[0] in scriptEnums:
                r = tt[0]
            elif tt[0] in userObjects or tt[0] in entityRelatives:
                r = tt[0] + getHandle()
            elif tt[0] == 'ObjInfo':
                return '?&in'
            elif tt[0] == 'ScriptFunc':
                assert not isRet
                assert len(tt) > 1, 'Invalid generic function'
                return 'Generic_' + '.'.join(tt[1:]).replace('|', '_').replace('.', '_') + 'Func@+'
            else:
                r = tt[0]
            return r + '&' if tt[-1] == 'ref' else r
        
        def marshalIn(t, v):
            tt = t.split('.')
            if tt[0] == 'dict':
                d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
                return 'MarshalDict<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToEngineType(d2, target, False) + \
                        ', ' + metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(d2) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v + ')'
            elif tt[0] == 'arr':
                return 'MarshalArray<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToASEngineType(tt[1]) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v + ')'
            elif tt[0] in ['init', 'predicate', 'callback']:
                return 'GetASFuncName(' + v + ', *self->GetEngine())'
            elif tt[0] == 'ScriptFunc':
                return 'GetASScriptFunc<' + ', '.join([metaTypeToEngineType(a, target, False, refAsPtr=True) for a in '.'.join(tt[1:]).split('|') if a]) + '>(' + v + ', GET_SCRIPT_SYS_FROM_SELF())'
            elif tt[0] == 'ObjInfo':
                return 'GetASObjectInfo(' + v + 'Ptr, ' + v + ')'
            elif tt[0] in engineEnums:
                return 'static_cast<' + tt[0] + '>(' + v + ')'
            elif tt[0] in scriptEnums:
                for e in codeGenTags['Enum']:
                    if e[0] == tt[0]:
                        return 'static_cast<ScriptEnum_' + e[1] + '>(' + v + ')'
                else:
                    assert False, 'Enum not found ' + tt[0]
            return v
            
        def marshalBack(t, v):
            tt = t.split('.')
            if tt[0] == 'dict':
                d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
                return 'MarshalBackDict<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToEngineType(d2, target, False) + \
                        ', ' + metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(d2) + \
                        '>(GET_AS_ENGINE_FROM_SELF(), "dict<' + metaTypeToASType(tt[1], True) + ', ' + metaTypeToASType(d2, True) + '>", ' + v + ')'
            elif tt[0] == 'arr':
                return 'MarshalBackArray<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToASEngineType(tt[1]) + \
                        '>(GET_AS_ENGINE_FROM_SELF(), "' + metaTypeToASType(tt[1], True) + '[]", ' + v + ')'
            elif tt[0] in engineEnums or tt[0] in scriptEnums:
                return 'static_cast<int>(' + v + ')'
            return v
        
        def marshalBackRef(t, v, v2):
            tt = t.split('.')
            if tt[-1] != 'ref':
                return None
            if tt[0] == 'dict':
                d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
                return 'AssignDict<' + metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(tt[1]) + ', ' + \
                        metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(d2) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v + ', ' + v2 + ')'
            elif tt[0] == 'arr':
                return 'AssignArray<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToASEngineType(tt[1]) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v2 + ', ' + v + ')'
            elif tt[0] in engineEnums or tt[0] in scriptEnums:
                return v + ' = static_cast<int>(' + v2 + ')'
            return None
        
        def marshalBackRef2(t, v, v2):
            tt = t.split('.')
            if tt[-1] != 'ref':
                return None
            if tt[0] == 'dict':
                d2 = tt[2] if tt[2] != 'arr' else tt[2] + '.' + tt[3]
                return v2 + ' = MarshalDict<' + metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(tt[1]) + ', ' + \
                        metaTypeToASEngineType(tt[1]) + ', ' + metaTypeToASEngineType(d2) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v + ')'
            elif tt[0] == 'arr':
                return v2 + ' = MarshalArray<' + metaTypeToEngineType(tt[1], target, False) + ', ' + metaTypeToASEngineType(tt[1]) + '>(GET_AS_ENGINE_FROM_SELF(), ' + v + ')'
            elif tt[0] in engineEnums or tt[0] in scriptEnums:
                return v2 + ' = static_cast<' + metaTypeToEngineType(tt[0], target, False) + '>(' + v + ')'
            return None
        
        def marshalBackRelease(t, v):
            tt = t.split('.')
            if tt[0] in ['dict', 'arr']:
                return v + '->Release()'
            return None
        
        def nameMangling(params):
            if len(params):
                return ''.join([''.join([p2[0] + p2[-1] for p2 in p[0].split('.')]) for p in params]).replace('|', '')
            return '0'
        
        allowedTargets = ['Common', target] + (['Client' if target == 'Mapper' else ''])
        
        defineLines = []
        globalLines = []
        registerLines = []
        postRegisterLines = []
        
        defineLines.append('#define SERVER_SCRIPTING ' + ('1' if target == 'Server' else '0'))
        defineLines.append('#define CLIENT_SCRIPTING ' + ('1' if target == 'Client' else '0'))
        defineLines.append('#define SINGLE_SCRIPTING ' + ('1' if target == 'Single' else '0'))
        defineLines.append('#define MAPPER_SCRIPTING ' + ('1' if target == 'Mapper' else '0'))
        defineLines.append('#define COMPILER_MODE ' + ('1' if isASCompiler else '0'))
        defineLines.append('#define COMPILER_VALIDATION_MODE ' + ('1' if isASCompilerValidation else '0'))
        
        # User entities
        globalLines.append('// User entities info')
        for entTag in codeGenTags['Entity']:
            targ, entity, flags, _ = entTag
            engineEntityType = gameEntitiesInfo[entity]['Client' if target != 'Server' else 'Server']
            if engineEntityType is None:
                continue
            globalLines.append('struct ' + entity + 'Info')
            globalLines.append('{')
            globalLines.append('    static constexpr string_view ENTITY_CLASS_NAME = "' + entity + '";')
            globalLines.append('};')
        globalLines.append('')
        
        # Scriptable objects and entity stubs
        if isASCompiler:
            globalLines.append('// Compiler entity stubs')
            for entity in gameEntities:
                engineEntityType = gameEntitiesInfo[entity]['Client' if target != 'Server' else 'Server']
                if engineEntityType is None:
                    continue
                if not gameEntitiesInfo[entity]['Exported']:
                    continue
                engineEntityType = engineEntityType
                globalLines.append('struct ' + engineEntityType + ' : BaseEntity { };')
                if gameEntitiesInfo[entity]['HasStatics']:
                    globalLines.append('struct Static' + entity + ' : BaseEntity { };')
            globalLines.append('')
            
            globalLines.append('// Scriptable objects')
            for eo in codeGenTags['ExportObject']:
                targ, objName, fields, methods, _, _ = eo
                if targ in allowedTargets:
                    globalLines.append('struct ' + objName)
                    globalLines.append('{')
                    globalLines.append('    void AddRef() { }')
                    globalLines.append('    void Release() { }')
                    globalLines.append('    int RefCounter;')
                    for f in fields:
                        globalLines.append('    ' + metaTypeToASEngineType(f[0]) + ' ' + f[1] + ';')
                    for m in methods:
                        globalLines.append('    ' + metaTypeToASEngineType(m[1]) + ' ' + m[0] + '() { }')
                    globalLines.append('};')
                    globalLines.append('')
            
        # Marshalling functions
        def writeMarshalingMethod(entity, targ, name, ret, params):
            engineEntityType = gameEntitiesInfo[entity]['Client' if target != 'Server' else 'Server']
            engineEntityTypeExtern = engineEntityType
            
            if entity == 'Game':
                if target == 'Mapper':
                    engineEntityType = 'FOMapper'
                if targ == 'Common':
                    engineEntityTypeExtern = 'FOEngineBase'
                elif targ == 'Mapper':
                    engineEntityTypeExtern = 'FOMapper'
            
            globalLines.append('static ' + metaTypeToASEngineType(ret, True) +
                    ' AS_' + targ + '_' + entity + '_' + name + '_' + nameMangling(params) + '(' +
                    (engineEntityType + '* self' + (', ' if params else '')) +
                    ', '.join([metaTypeToASEngineType(p[0]) + ' ' + p[1] for p in params]) +')')
            globalLines.append('{')
            globalLines.append('    STACK_TRACE_ENTRY();')
            
            if not isASCompiler:
                globalLines.append('    ENTITY_VERIFY_NULL(self);')
                globalLines.append('    ENTITY_VERIFY(self);')
                for p in params:
                    if p[0] in gameEntities:
                        globalLines.append('    ENTITY_VERIFY(' + p[1] + ');')
                for p in params:
                    globalLines.append('    auto&& in_' + p[1] + ' = ' + marshalIn(p[0], p[1]) + ';')
                globalLines.append('    extern ' + metaTypeToEngineType(ret, target, False) + ' ' + targ + '_' + entity + '_' + name +
                        '(' + engineEntityTypeExtern + '*' + (', ' if params else '') + ', '.join([metaTypeToEngineType(p[0], target, True) for p in params]) + ');')
                globalLines.append('    ' + ('auto out_result = ' if ret != 'void' else '') + targ + '_' + entity + '_' + name +
                        '(self' + (', ' if params else '') + ', '.join(['in_' + p[1] for p in params]) + ');')
                for p in params:
                    mbr = marshalBackRef(p[0], p[1], 'in_' + p[1])
                    if mbr:
                        globalLines.append('    ' + mbr + ';')
                if ret != 'void':
                    globalLines.append('    return ' + marshalBack(ret, 'out_result') + ';')
            else:
                # Stub for compiler
                globalLines.append('    UNUSED_VARIABLE(self);')
                for p in params:
                    globalLines.append('    UNUSED_VARIABLE(' + p[1] + ');')
                globalLines.append('    throw ScriptCompilerException("Stub");')
            
            globalLines.append('}')
            globalLines.append('')
            
        globalLines.append('// Marshalling entity methods')
        for entity in gameEntities:
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comment = methodTag
                if targ in allowedTargets and ent == entity:
                    writeMarshalingMethod(entity, targ, name, ret, params)
        
        # Marshal events
        def ctxSetArgs(args, setIndex=0):
            for p in args:
                tt = p[0].split('.')
                if tt[-1] == 'ref':
                    globalLines.append('    ctx->SetArgAddress(' + str(setIndex) + ', &as_' + p[1] + ');')
                elif tt[0] == 'dict' or tt[0] == 'arr' or p[0] == 'Entity' or p[0] in gameEntities or p[0] in userObjects:
                    globalLines.append('    ctx->SetArgObject(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in entityRelatives:
                    globalLines.append('    ctx->SetArgObject(' + str(setIndex) + ', (void*)as_' + p[1] + ');')
                elif p[0] in ['string']:
                    globalLines.append('    ctx->SetArgObject(' + str(setIndex) + ', &as_' + p[1] + ');')
                elif p[0] in ['int8', 'uint8', 'bool']:
                    globalLines.append('    ctx->SetArgByte(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['int16', 'uint16']:
                    globalLines.append('    ctx->SetArgWord(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['int', 'uint'] or p[0] in engineEnums or p[0] in scriptEnums:
                    globalLines.append('    ctx->SetArgDWord(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['int64', 'uint64']:
                    globalLines.append('    ctx->SetArgQWord(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['float']:
                    globalLines.append('    ctx->SetArgFloat(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['double']:
                    globalLines.append('    ctx->SetArgDouble(' + str(setIndex) + ', as_' + p[1] + ');')
                elif p[0] in ['hstring']:
                    globalLines.append('    ctx->SetArgObject(' + str(setIndex) + ', &as_' + p[1] + ');')
                elif p[0] in customTypes:
                    globalLines.append('    ctx->SetArgObject(' + str(setIndex) + ', &as_' + p[1] + ');')
                else:
                    globalLines.append('    static_assert(false, "Invalid configuration");')
                setIndex += 1
        
        globalLines.append('// Marshalling events')
        for entity in gameEntities:
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, _ = evTag
                if targ in allowedTargets and ent == entity:
                    isGlobal = gameEntitiesInfo[entity]['IsGlobal']
                    isExported = evTag in codeGenTags['ExportEvent']
                    funcEntry = 'ASEvent_' + entity + '_' + evName
                    entityArg = metaTypeToEngineType(entity, target, True) + ' self'
                    if not isExported:
                        globalLines.append('static string ' + funcEntry + '_Name = "' + evName + '";')
                    if not isASCompiler:
                        globalLines.append('static bool ' + funcEntry + '_Callback(' + entityArg + ', asIScriptFunction* func, const initializer_list<void*>& args)')
                        globalLines.append('{')
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY_RETURN(self, true);')
                        globalLines.append('    UNUSED_VARIABLE(args);')
                        argIndex = 0
                        for p in evArgs:
                            argType = metaTypeToEngineType(p[0], target, False)
                            if argType[-1] == '&':
                                argType = argType[:-1]
                            globalLines.append('    auto&& arg_' + p[1] + ' = *reinterpret_cast<' + argType + '*>(const_cast<void*>(*(args.begin() + ' + str(argIndex) + ')));')
                            if p[0] in gameEntities:
                                globalLines.append('    ENTITY_VERIFY_RETURN(arg_' + p[1] + ', true);')
                            argIndex += 1
                        for p in evArgs:
                            globalLines.append('    auto&& as_' + p[1] + ' = ' + marshalBack(p[0], 'arg_' + p[1]) + ';')
                        globalLines.append('    auto* script_sys = GET_SCRIPT_SYS_FROM_SELF();')
                        globalLines.append('    auto* ctx = script_sys->PrepareContext(func);')
                        if not isGlobal:
                            globalLines.append('    ctx->SetArgObject(0, self);')
                        ctxSetArgs(evArgs, 0 if isGlobal else 1)
                        globalLines.append('    auto event_result = true;')
                        globalLines.append('    if (script_sys->RunContext(ctx, func->GetReturnTypeId() == asTYPEID_VOID)) {')
                        globalLines.append('        event_result = (func->GetReturnTypeId() == asTYPEID_VOID || (func->GetReturnTypeId() == asTYPEID_BOOL && ctx->GetReturnByte() != 0));')
                        for p in evArgs:
                            mbr = marshalBackRef2(p[0], 'as_' + p[1], 'arg_' + p[1])
                            if mbr:
                                globalLines.append('        ' + mbr + ';')
                        globalLines.append('        script_sys->ReturnContext(ctx);')
                        globalLines.append('    }')
                        for p in evArgs:
                            mbr = marshalBackRelease(p[0], 'as_' + p[1])
                            if mbr:
                                globalLines.append('    ' + mbr + ';')
                        globalLines.append('    return event_result;')
                        globalLines.append('}')
                    globalLines.append('static void ' + funcEntry + '_Subscribe(' + entityArg + ', asIScriptFunction* func)')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY(self);')
                        globalLines.append('    auto event_data = Entity::EventCallbackData();')
                        globalLines.append('    event_data.SubscribtionPtr = (func->GetFuncType() == asFUNC_DELEGATE ? func->GetDelegateFunction() : func);')
                        globalLines.append('    event_data.Callback = [self, func = RefCountHolder(func)](const initializer_list<void*>& args) {')
                        globalLines.append('        return ' + funcEntry + '_Callback(self, func.get(), args);')
                        globalLines.append('    };')
                        if isExported:
                            globalLines.append('    self->' + evName + '.Subscribe(std::move(event_data));')
                        else:
                            globalLines.append('    self->SubscribeEvent(' + funcEntry + '_Name, std::move(event_data));')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        globalLines.append('    UNUSED_VARIABLE(func);')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                    globalLines.append('static void ' + funcEntry + '_Unsubscribe(' + entityArg + ', asIScriptFunction* func)')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY(self);')
                        if isExported:
                            globalLines.append('    self->' + evName + '.Unsubscribe(func->GetFuncType() == asFUNC_DELEGATE ? func->GetDelegateFunction() : func);')
                        else:
                            globalLines.append('    self->UnsubscribeEvent(' + funcEntry + '_Name, func->GetFuncType() == asFUNC_DELEGATE ? func->GetDelegateFunction() : func);')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        globalLines.append('    UNUSED_VARIABLE(func);')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                    globalLines.append('static void ' + funcEntry + '_UnsubscribeAll(' + entityArg + ')')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY(self);')
                        if isExported:
                            globalLines.append('    self->' + evName + '.UnsubscribeAll();')
                        else:
                            globalLines.append('    self->UnsubscribeAllEvent(' + funcEntry + '_Name);')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                    if not isExported:
                        globalLines.append('static bool ' + funcEntry + '_Fire(' + entityArg + (', ' if evArgs else '') + ', '.join([metaTypeToASEngineType(p[0]) + ' ' + p[1] for p in evArgs]) + ')')
                        globalLines.append('{')
                        if not isASCompiler:
                            globalLines.append('    STACK_TRACE_ENTRY();')
                            globalLines.append('    ENTITY_VERIFY_NULL(self);')
                            globalLines.append('    ENTITY_VERIFY_RETURN(self, true);')
                            for p in evArgs:
                                if p[0] in gameEntities:
                                    globalLines.append('    ENTITY_VERIFY_RETURN(' + p[1] + ', true);')
                            for p in evArgs:
                                globalLines.append('    auto&& in_' + p[1] + ' = ' + marshalIn(p[0], p[1]) + ';')
                            if isExported:
                                globalLines.append('    return self->' + evName + '.Fire(' + ', '.join(['in_' + p[1] for p in evArgs]) + ');')
                            else:
                                globalLines.append('    return self->FireEvent(' + funcEntry + '_Name, {' + ', '.join(['&in_' + p[1] for p in evArgs]) + '});')
                        else:
                            globalLines.append('    UNUSED_VARIABLE(self);')
                            for p in evArgs:
                                globalLines.append('    UNUSED_VARIABLE(' + p[1] + ');')
                            globalLines.append('    throw ScriptCompilerException("Stub");')
                        globalLines.append('}')
                    globalLines.append('')
        
        # Marshal settings
        globalLines.append('// Marshalling settings')
        settEntity = metaTypeToEngineType('Game', target, False) + ' self'
        for settTag in codeGenTags['ExportSettings']:
            grName, targ, settings, flags, _ = settTag
            if targ not in allowedTargets:
                continue
            for sett in settings:
                fixOrVar, keyType, keyName, initValues, _ = sett
                globalLines.append('static ' + metaTypeToASEngineType(keyType, True) + ' ASSetting_Get_' + keyName + '(' + settEntity + ')')
                globalLines.append('{')
                if not isASCompiler:
                    globalLines.append('    STACK_TRACE_ENTRY();')
                    globalLines.append('    return ' + marshalBack(keyType, 'self->Settings.' + keyName) + ';')
                else:
                    globalLines.append('    UNUSED_VARIABLE(self);')
                    globalLines.append('    throw ScriptCompilerException("Stub");')
                globalLines.append('}')
                if fixOrVar == 'var':
                    globalLines.append('static void ASSetting_Set_' + keyName + '(' + settEntity + ', ' + metaTypeToASEngineType(keyType, False) + ' value)')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    self->Settings.' + keyName + ' = ' + marshalIn(keyType, 'value') + ';')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        globalLines.append('    UNUSED_VARIABLE(value);')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                globalLines.append('')
        for settTag in codeGenTags['Setting']:
            targ, type, name, initValue, flags, _ = settTag
            if targ not in allowedTargets:
                continue
            globalLines.append('static ' + metaTypeToASEngineType(type, True) + ' ASSetting_Get_' + name + '(' + settEntity + ')')
            globalLines.append('{')
            if not isASCompiler:
                globalLines.append('    STACK_TRACE_ENTRY();')
                globalLines.append('    auto* script_sys = GET_SCRIPT_SYS_FROM_SELF();')
                globalLines.append('    auto&& value = script_sys->GameEngine->Settings.Custom["' + name + '"];')
                if type == 'string':
                    globalLines.append('    return value;')
                elif type == 'any':
                    globalLines.append('    return any_t {' + 'value};')
                elif type == 'bool':
                    globalLines.append('    return _str(value).toBool();')
                elif type in ['float', 'double']:
                    globalLines.append('    return static_cast<' + metaTypeToASEngineType(type) + '>(_str(value).toDouble());')
                else:
                    globalLines.append('    return static_cast<' + metaTypeToASEngineType(type) + '>(_str(value).toInt64());')
            else:
                globalLines.append('    UNUSED_VARIABLE(self);')
                globalLines.append('    throw ScriptCompilerException("Stub");')
            globalLines.append('}')
            globalLines.append('static void ASSetting_Set_' + name + '(' + settEntity + ', ' + metaTypeToASEngineType(type, False) + ' value)')
            globalLines.append('{')
            if not isASCompiler:
                globalLines.append('    STACK_TRACE_ENTRY();')
                globalLines.append('    auto* script_sys = GET_SCRIPT_SYS_FROM_SELF();')
                globalLines.append('    script_sys->GameEngine->Settings.Custom["' + name + '"] = _str("{' + '}", ' + marshalIn(type, 'value') + ');')
            else:
                globalLines.append('    UNUSED_VARIABLE(self);')
                globalLines.append('    UNUSED_VARIABLE(value);')
                globalLines.append('    throw ScriptCompilerException("Stub");')
            globalLines.append('}')
            globalLines.append('')
        
        # Remote calls dispatchers
        if target in ['Server', 'Client']:
            globalLines.append('// Remote calls dispatchers')
            for rcTag in codeGenTags['RemoteCall']:
                targ, subsystem, ns, rcName, rcArgs, rcFlags, _ = rcTag
                if targ == ('Client' if target == 'Server' else 'Server') and subsystem == 'AngelScript':
                    selfArg = 'Player* self' if target == 'Server' else 'PlayerView* self'
                    globalLines.append('static void ASRemoteCall_Send_' + rcName + '(' + selfArg + (', ' if rcArgs else '') + ', '.join([metaTypeToASEngineType(p[0]) + ' ' + p[1] for p in rcArgs]) + ')')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY(self);')
                        globalLines.append('    constexpr uint rpc_num = "' + rcName + '"_hash;')
                        for p in rcArgs:
                            globalLines.append('    auto&& in_' + p[1] + ' = ' + marshalIn(p[0], p[1]) + ';')
                        if target == 'Server':
                            globalLines.append('    auto* conn = self->Connection;')
                            globalLines.append('    CONNECTION_OUTPUT_BEGIN(conn);')
                            globalLines.append('    WriteRpcHeader(conn->OutBuf, rpc_num);')
                            for p in rcArgs:
                                globalLines.append('    WriteNetBuf(conn->OutBuf, in_' + p[1] + ');')
                            globalLines.append('    WriteRpcFooter(conn->OutBuf);')
                            globalLines.append('    CONNECTION_OUTPUT_END(conn);')
                        else:
                            globalLines.append('    auto& conn = self->GetEngine()->GetConnection();')
                            globalLines.append('    WriteRpcHeader(conn.OutBuf, rpc_num);')
                            for p in rcArgs:
                                globalLines.append('    WriteNetBuf(conn.OutBuf, in_' + p[1] + ');')
                            globalLines.append('    WriteRpcFooter(conn.OutBuf);')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        for p in rcArgs:
                            globalLines.append('    UNUSED_VARIABLE(' + p[1] + ');')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                    globalLines.append('')
            for rcTag in codeGenTags['RemoteCall']:
                targ, subsystem, ns, rcName, rcArgs, rcFlags, _ = rcTag
                if targ == target and subsystem == 'AngelScript':
                    selfArg = 'Player* self' if target == 'Server' else 'PlayerView* self'
                    if not isASCompiler:
                        globalLines.append('static void ASRemoteCall_Receive_' + rcName + '(' + selfArg + ', asIScriptFunction* func)')
                    else:
                        globalLines.append('[[maybe_unused]] static void ASRemoteCall_Receive_' + rcName + '(' + selfArg + ', asIScriptFunction* func)')
                    globalLines.append('{')
                    if not isASCompiler:
                        globalLines.append('    STACK_TRACE_ENTRY();')
                        globalLines.append('    ENTITY_VERIFY_NULL(self);')
                        globalLines.append('    ENTITY_VERIFY(self);')
                        if target == 'Server':
                            globalLines.append('    auto* conn = self->Connection;')
                            for p in rcArgs:
                                globalLines.append('    ' + metaTypeToEngineType(p[0], target, False) + ' arg_' + p[1] + ';')
                                globalLines.append('    ReadNetBuf(conn->InBuf, arg_' + p[1] + ', *self->GetEngine());')
                            globalLines.append('    CHECK_CLIENT_IN_BUF_ERROR(conn);')
                        else:
                            globalLines.append('    auto& conn = self->GetEngine()->GetConnection();')
                            for p in rcArgs:
                                globalLines.append('    ' + metaTypeToEngineType(p[0], target, False) + ' arg_' + p[1] + ';')
                                globalLines.append('    ReadNetBuf(conn.InBuf, arg_' + p[1] + ', *self->GetEngine());')
                            globalLines.append('    CHECK_SERVER_IN_BUF_ERROR(conn);')
                        for p in rcArgs:
                            globalLines.append('    auto&& as_' + p[1] + ' = ' + marshalBack(p[0], 'arg_' + p[1]) + ';')
                        globalLines.append('    auto* script_sys = GET_SCRIPT_SYS_FROM_SELF();')
                        globalLines.append('    auto* ctx = script_sys->PrepareContext(func);')
                        if target == 'Server':
                            globalLines.append('    ctx->SetArgObject(0, self);')
                            ctxSetArgs(rcArgs, 1)
                        else:
                            ctxSetArgs(rcArgs, 0)
                        for p in rcArgs:
                            mbr = marshalBackRelease(p[0], 'as_' + p[1])
                            if mbr:
                                globalLines.append('    ' + mbr + ';')
                        globalLines.append('    if (script_sys->RunContext(ctx, true)) {')
                        globalLines.append('        script_sys->ReturnContext(ctx);')
                        globalLines.append('    }')
                    else:
                        globalLines.append('    UNUSED_VARIABLE(self);')
                        globalLines.append('    UNUSED_VARIABLE(func);')
                        globalLines.append('    throw ScriptCompilerException("Stub");')
                    globalLines.append('}')
                    globalLines.append('')
            globalLines.append('')
            
        # Register custom types
        registerLines.append('// Exported types')
        for et in codeGenTags['ExportType']:
            name, utype, rtype, flags, _ = et
            if rtype == 'RelaxedStrong':
                registerLines.append('REGISTER_RELAXED_STRONG_TYPE(' + name + ', ' + utype + ');')
            elif rtype == 'HardStrong':
                registerLines.append('REGISTER_HARD_STRONG_TYPE(' + name + ', ' + utype + ');')
        registerLines.append('')
        
        # Register exported objects
        registerLines.append('// Exported objects')
        for eo in codeGenTags['ExportObject']:
            targ, objName, fields, methods, _, _ = eo
            if targ in allowedTargets:
                registerLines.append('AS_VERIFY(engine->RegisterObjectType("' + objName + '", sizeof(' + objName + '), asOBJ_REF));')
                registerLines.append('AS_VERIFY(engine->RegisterObjectBehaviour("' + objName + '", asBEHAVE_ADDREF, "void f()", SCRIPT_METHOD(' + objName + ', AddRef), SCRIPT_METHOD_CONV));')
                registerLines.append('AS_VERIFY(engine->RegisterObjectBehaviour("' + objName + '", asBEHAVE_RELEASE, "void f()", SCRIPT_METHOD(' + objName + ', Release), SCRIPT_METHOD_CONV));')
                registerLines.append('AS_VERIFY(engine->RegisterObjectBehaviour("' + objName + '", asBEHAVE_FACTORY, "' + objName + '@ f()", SCRIPT_FUNC((ScriptableObject_Factory<' + objName + '>)), SCRIPT_FUNC_CONV));')
                registerLines.append('AS_VERIFY(engine->RegisterObjectProperty("' + objName + '", "const int RefCounter", offsetof(' + objName + ', RefCounter)));')
                for f in fields:
                    registerLines.append('AS_VERIFY(engine->RegisterObjectProperty("' + objName + '", "' + metaTypeToASType(f[0], True) + ' ' + f[1] + '", offsetof(' + objName + ', ' + f[1] + ')));')
                for m in methods:
                    registerLines.append('AS_VERIFY(engine->RegisterObjectMethod("' + objName + '", "' + metaTypeToASType(m[1], isRet=True) + ' ' + m[0] + '()", SCRIPT_METHOD(' + objName + ', ' + m[0] + '), SCRIPT_METHOD_CONV));')
                registerLines.append('')
        
        # Register entities
        registerLines.append('// Register entities')
        for entity in gameEntities:
            engineEntityType = gameEntitiesInfo[entity]['Client' if target != 'Server' else 'Server']
            if engineEntityType is None:
                continue
            if not gameEntitiesInfo[entity]['Exported']:
                assert not gameEntitiesInfo[entity]['IsGlobal']
                registerLines.append('REGISTER_CUSTOM_ENTITY("' + entity + '", ' + engineEntityType + ', ' + entity + 'Info);')
            elif gameEntitiesInfo[entity]['IsGlobal']:
                registerLines.append('REGISTER_GLOBAL_ENTITY("' + entity + '", ' + engineEntityType + ');')
            else:
                registerLines.append('REGISTER_ENTITY("' + entity + '", ' + engineEntityType + ');')
            if gameEntitiesInfo[entity]['HasAbstract']:
                assert not gameEntitiesInfo[entity]['IsGlobal']
                registerLines.append('REGISTER_ENTITY_ABSTRACT("' + entity + '", ' + engineEntityType + ');')
            if gameEntitiesInfo[entity]['HasProto']:
                assert not gameEntitiesInfo[entity]['IsGlobal']
                registerLines.append('REGISTER_ENTITY_PROTO("' + entity + '", ' + engineEntityType + ', Proto' + entity + ');')
            if gameEntitiesInfo[entity]['HasStatics']:
                assert not gameEntitiesInfo[entity]['IsGlobal']
                registerLines.append('REGISTER_ENTITY_STATICS("' + entity + '", ' + engineEntityType + ');')
        registerLines.append('')
        
        # Generic funcdefs
        registerLines.append('// Generic funcdefs')
        for fd in sorted(genericFuncdefs):
            fdParams = fd.split('|')
            registerLines.append('AS_VERIFY(engine->RegisterFuncdef("' + metaTypeToASType(fdParams[0], forceNoConst=True) + ' Generic_' + '.'.join(fdParams).replace('.', '_') +
                    '_Func(' + ', '.join([metaTypeToASType(p, forceNoConst=True) for p in fdParams[1:]]) + ')"));')
        registerLines.append('')
        
        # Register entity methods and global functions
        registerLines.append('// Register methods')
        for entity in gameEntities:
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comment = methodTag
                if targ in allowedTargets and ent == entity:
                    def passOwnership(asRet):
                        if 'PassOwnership' in exportFlags:
                            assert asRet[-1] == '+'
                            return asRet[:-1]
                        else:
                            return asRet
                    registerLines.append('REGISTER_ENTITY_METHOD("' + (entity + 'Singleton' if gameEntitiesInfo[entity]['IsGlobal'] else entity) +
                            '", "' + passOwnership(metaTypeToASType(ret, isRet=True)) + ' ' + name + '(' +
                            ', '.join([metaTypeToASType(p[0]) + ' ' + p[1] for p in params]) + ')", AS_' + targ + '_' +
                            entity + '_' + name + '_' + nameMangling(params) + ');')
        registerLines.append('')
        
        # Register events
        registerLines.append('// Register events')
        for entity in gameEntities:
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, _ = evTag
                if targ in allowedTargets and ent == entity:
                    isExported = evTag in codeGenTags['ExportEvent']
                    funcEntry = 'ASEvent_' + entity + '_' + evName
                    asArgs = ', '.join([metaTypeToASType(p[0], forceNoConst=True) + ' ' + p[1] for p in evArgs])
                    asArgsEnt = metaTypeToASType(entity, forceNoConst=True) + (', ' if evArgs else '') if not gameEntitiesInfo[entity]['IsGlobal'] else ''
                    className = entity + 'Singleton' if gameEntitiesInfo[entity]['IsGlobal'] else entity
                    realClass = gameEntitiesInfo[entity]['Client' if target != 'Server' else 'Server']
                    if isExported:
                        registerLines.append('REGISTER_ENTITY_EXPORTED_EVENT("' + entity + '", "' + className + '", ' + realClass + ', "' + evName + '", "' + asArgsEnt + '", "' + asArgs + '", ' + funcEntry + ');')
                    else:
                        registerLines.append('REGISTER_ENTITY_SCRIPT_EVENT("' + entity + '", "' + className + '", ' + realClass + ', "' + evName + '", "' + asArgsEnt + '", "' + asArgs + '", ' + funcEntry + ');')
        registerLines.append('')
        
        # Register settings
        registerLines.append('// Register settings')
        settEntity = gameEntitiesInfo['Game']['Client' if target != 'Server' else 'Server'] + '* self'
        for settTag in codeGenTags['ExportSettings']:
            grName, targ, settings, flags, _ = settTag
            if targ not in allowedTargets:
                continue
            for sett in settings:
                fixOrVar, keyType, keyName, initValues, _ = sett
                registerLines.append('REGISTER_GET_SETTING(' + keyName + ', "' + metaTypeToASType(keyType, isRet=True) + ' get_' + keyName + '() const");')
                if fixOrVar == 'var':
                    registerLines.append('REGISTER_SET_SETTING(' + keyName + ', "void set_' + keyName + '(' + metaTypeToASType(keyType) + ')");')
        for settTag in codeGenTags['Setting']:
            targ, type, name, initValue, flags, _ = settTag
            if targ not in allowedTargets:
                continue
            registerLines.append('REGISTER_GET_SETTING(' + name + ', "' + metaTypeToASType(type, isRet=True) + ' get_' + name + '() const");')
            registerLines.append('REGISTER_SET_SETTING(' + name + ', "void set_' + name + '(' + metaTypeToASType(type) + ')");')
        registerLines.append('')
        
        # Register remote calls
        if target in ['Server', 'Client']:
            registerLines.append('// Register remote call senders')
            postRegisterLines.append('// Bind remote call receivers')
            for rcTag in codeGenTags['RemoteCall']:
                targ, subsystem, ns, rcName, rcArgs, rcFlags, _ = rcTag
                if targ == ('Client' if target == 'Server' else 'Server') and subsystem == 'AngelScript':
                    registerLines.append('AS_VERIFY(engine->RegisterObjectMethod("RemoteCaller", "void ' + rcName +
                            '(' + ', '.join([metaTypeToASType(p[0]) + ' ' + p[1] for p in rcArgs]) + ')", SCRIPT_FUNC_THIS(ASRemoteCall_Send_' + rcName + '), SCRIPT_FUNC_THIS_CONV));')
            for rcTag in codeGenTags['RemoteCall']:
                targ, subsystem, ns, rcName, rcArgs, rcFlags, _ = rcTag
                if targ == target and subsystem == 'AngelScript':
                    asFuncFirstArg = ('Player@+ player' + (', ' if rcArgs else '')) if target == 'Server' else ''
                    asFuncDecl = 'void ' + ns + '::' + rcName + '(' + asFuncFirstArg + ', '.join([metaTypeToASType(p[0], forceNoConst=True) + ' ' + p[1] for p in rcArgs]) + ')'
                    postRegisterLines.append('BIND_REMOTE_CALL_RECEIVER("' + rcName + '", ASRemoteCall_Receive_' + rcName + ', "' + asFuncDecl + '");')
            registerLines.append('')
            postRegisterLines.append('')
        
        # Modify file content (from bottom to top)
        insertCodeGenLines(postRegisterLines, 'PostRegister')
        insertCodeGenLines(registerLines, 'Register')
        insertCodeGenLines(globalLines, 'Global')
        insertCodeGenLines(defineLines, 'Defines')

    elif lang == 'Mono':
        assert False, 'Mono generation not implemented'
    
    elif lang == 'Native':
        assert False, 'Native generation not implemented'

try:
    if args.multiplayer:
        genCode('AngelScript', 'Server')
        genCode('AngelScript', 'Client')
        genCode('AngelScript', 'Server', True)
        genCode('AngelScript', 'Server', True, True)
        genCode('AngelScript', 'Client', True)
    if args.singleplayer:
        genCode('AngelScript', 'Single')
        genCode('AngelScript', 'Single', True)
        genCode('AngelScript', 'Single', True, True)
    genCode('AngelScript', 'Mapper')
    genCode('AngelScript', 'Mapper', True)
    
    if args.multiplayer:
        genCode('Mono', 'Server')
        genCode('Mono', 'Client')
    if args.singleplayer:
        genCode('Mono', 'Single')
    genCode('Mono', 'Mapper')
    
    if args.multiplayer:
        genCode('Native', 'Server')
        genCode('Native', 'Client')
    if args.singleplayer:
        genCode('Native', 'Single')
    genCode('Native', 'Mapper')
    
except Exception as ex:
    showError('Code generation failed', ex)

checkErrors()

# AngelScript content file
if args.angelscript and args.ascontentoutput:
    try:
        createFile('Content.fos', args.ascontentoutput)
        def writeEnums(name, lst):
            writeFile('namespace ' + name)
            writeFile('{')
            for i in lst:
                writeFile('    hstring ' + i + ' = hstring("' + i + '");')
            writeFile('}')
            writeFile('')
        writeFile('// FOS Common')
        writeFile('')
        writeEnums('Dialog', content['fodlg'])
        writeEnums('Item', content['foitem'])
        writeEnums('Critter', content['focr'])
        writeEnums('Map', content['fomap'])
        writeEnums('Location', content['foloc'])
    
    except Exception as ex:
        showError('Can\'t generate scripts', ex)

# Markdown
def genApiMarkdown(target):
    createFile('SCRIPT_API.md', args.mdpath)
    writeFile('# ' + args.devname + ' Script API')
    writeFile('')
    writeFile('## Table of Content')
    writeFile('')
    writeFile('GNEREATE AUTOMATICALLY')
    writeFile('')
    
    # Generate source
    def writeComm(comm, ident):
        if not comm:
            comm = ['...']
        writeFile('')
        index = 0
        for c in comm:
            if c.startswith('param'):
                pass
            elif c.startswith('return'):
                pass
            else:
                pass
            writeFile(''.center(ident * 2 + 2) + '' + c + '' + ('  ' if index < len(comm) - 1 else ''))
            index += 1
        writeFile('')
    
    writeFile('## Settings')
    writeFile('')
    writeFile('### General')
    writeFile('')
    for settTag in codeGenTags['Setting']:
        targ, type, name, initValue, flags, comm = settTag
        writeFile('* `' + metaTypeToUnifiedType(type) + ' ' + name + (' = ' + initValue if initValue is not None else '') + (' ' + ', '.join(flags) if flags else '') + (' (' + targ.lower() + ' only)' if targ != 'Common' else '') + '`')
        writeComm(comm, 0)
    writeFile('')
    for settTag in codeGenTags['ExportSettings']:
        grName, targ, settings, flags, comm = settTag
        writeFile('### ' + grName + (' ' + ', '.join(flags) if flags else ''))
        writeComm(comm, 0)
        for sett in settings:
            fixOrVar, keyType, keyName, initValues, comm2 = sett
            writeFile('* `' + ('const ' if fixOrVar == 'fix' else '')  + metaTypeToUnifiedType(keyType) + ' ' + keyName + ' = ' + ', '.join(initValues) + '`')
            writeComm(comm2, 0)
        writeFile('')
    
    for entity in gameEntities:
        entityInfo = gameEntitiesInfo[entity]
        writeFile('## ' + entity + ' entity')
        writeComm(entityInfo['Comment'], 0)
        writeFile('* `Target: ' + ('Server/Client' if entityInfo['Server'] and entityInfo['Client'] else ('Server' if entityInfo['Server'] else ('Client' if entityInfo['Client'] else '?'))) + '`')
        writeFile('* `Built-in: ' + ('Yes' if entityInfo['Exported'] else 'No') + '`')
        writeFile('* `Singleton: ' + ('Yes' if entityInfo['IsGlobal'] else 'No') + '`')
        writeFile('* `Has proto: ' + ('Yes' if entityInfo['HasProto'] else 'No') + '`')
        writeFile('* `Has statics: ' + ('Yes' if entityInfo['HasStatics'] else 'No') + '`')
        writeFile('* `Has abstract: ' + ('Yes' if entityInfo['HasAbstract'] else 'No') + '`')
        writeFile('')
        writeFile('### ' + entity + ' properties')
        writeFile('')
        for propTag in codeGenTags['ExportProperty'] + codeGenTags['Property']:
            ent, access, type, name, flags, comm = propTag
            if ent == entity:
                if target == 'Multiplayer':
                    writeFile('* `' + access + ' ' + metaTypeToUnifiedType(type) + ' ' + name + (' ' + ' '.join(flags) if flags else '') + '`')
                else:
                    writeFile('* `' + metaTypeToUnifiedType(type) + ' ' + name + (' ' + ' '.join(flags) if flags else '') + '`')
                writeComm(comm, 0)
        if target == 'Multiplayer':
            writeFile('### ' + entity + ' server events')
            writeFile('')
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, comm = evTag
                if ent == entity and targ == 'Server':
                    writeFile('* `' + evName + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in evArgs]) + ')' + (' ' + ' '.join(evFlags) if evFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' client events')
            writeFile('')
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, comm = evTag
                if ent == entity and targ == 'Client':
                    writeFile('* `' + evName + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in evArgs]) + ')' + (' ' + ' '.join(evFlags) if evFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' common methods')
            writeFile('')
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comm = methodTag
                if ent == entity and targ == 'Common':
                    writeFile('* `' + metaTypeToUnifiedType(ret) + ' ' + name + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in params]) + ')' + (' ' + ' '.join(exportFlags) if exportFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' server methods')
            writeFile('')
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comm = methodTag
                if ent == entity and targ == 'Server':
                    writeFile('* `' + metaTypeToUnifiedType(ret) + ' ' + name + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in params]) + ')' + (' ' + ' '.join(exportFlags) if exportFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' client methods')
            writeFile('')
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comm = methodTag
                if ent == entity and targ == 'Client':
                    writeFile('* `' + metaTypeToUnifiedType(ret) + ' ' + name + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in params]) + ')' + (' ' + ' '.join(exportFlags) if exportFlags else '') + '`')
                    writeComm(comm, 0)
        elif target == 'Singleplayer':
            writeFile('### ' + entity + ' events')
            writeFile('')
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, comm = evTag
                if ent == entity:
                    writeFile('* `' + evName + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in evArgs]) + ')' + (' ' + ' '.join(evFlags) if evFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' methods')
            writeFile('')
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comm = methodTag
                if ent == entity and targ != 'Mapper':
                    writeFile('* `' + metaTypeToUnifiedType(ret) + ' ' + name + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in params]) + ')' + (' ' + ' '.join(exportFlags) if exportFlags else '') + '`')
                    writeComm(comm, 0)
        if entity == 'Game':
            writeFile('### ' + entity + ' mapper events')
            writeFile('')
            for evTag in codeGenTags['ExportEvent'] + codeGenTags['Event']:
                targ, ent, evName, evArgs, evFlags, comm = evTag
                if ent == entity and targ == 'Mapper':
                    writeFile('* `' + evName + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in evArgs]) + ')' + (' ' + ' '.join(evFlags) if evFlags else '') + '`')
                    writeComm(comm, 0)
            writeFile('### ' + entity + ' mapper methods')
            writeFile('')
            for methodTag in codeGenTags['ExportMethod']:
                targ, ent, name, ret, params, exportFlags, comm = methodTag
                if ent == entity and targ == 'Mapper':
                    writeFile('* `' + metaTypeToUnifiedType(ret) + ' ' + name + '(' + ', '.join([metaTypeToUnifiedType(a[0]) + ' ' + a[1] for a in params]) + ')' + (' ' + ' '.join(exportFlags) if exportFlags else '') + '`')
                    writeComm(comm, 0)
    
    writeFile('## Types')
    writeFile('')
    for eoTag in codeGenTags['ExportObject']:
        targ, objName, fields, methods, flags, comm = eoTag
        writeFile('### ' + objName + ' reference object')
        writeComm(comm, 0)
        for f in fields:
            writeFile('* `' + metaTypeToUnifiedType(f[0]) + ' ' + f[1] + '`')
            writeComm(f[2], 0)
        for m in methods:
            writeFile('* `' + metaTypeToUnifiedType(m[1]) + ' ' + m[0] + '()' + '`')
            writeComm(m[2], 0)
    for etTag in codeGenTags['ExportType']:
        name, utype, rtype, flags, comm = etTag
        writeFile('### ' + name + ' value object')
        writeComm(comm, 0)
        writeFile('* `Alias to: ' + metaTypeToUnifiedType(utype) + '`')
        writeFile('* `Type: ' + rtype + '`')
        if flags:
            writeFile('* `Flags: ' + ', '.join(flags) + '`')
        writeFile('')
    
    writeFile('## Enums')
    writeFile('')
    for eTag in codeGenTags['ExportEnum'] + codeGenTags['Enum']:
        gname, utype, keyValues, flags, comm = eTag
        writeFile('* `' + gname + (' ' + ' '.join(flags) if flags else '') + '`')
        writeComm(comm, 0)
        for kv in keyValues:
            writeFile('  - `' + kv[0] + ' = ' + kv[1] + '`')
            if kv[2]:
                writeComm(kv[2], 1)
            else:
                writeFile('')
    
    # Cleanup empty sections and generate Table of content
    global lastFile
    filteredLines = []
    tableOfContent = []
    i = 0
    while i < len(lastFile):
        if i < len(lastFile) - 2 and lastFile[i].startswith('### ') and lastFile[i + 2].startswith('#'):
            i += 2
            continue
        if lastFile[i].startswith('## '):
            tableOfContent.append('* [' + lastFile[i][3:] + '](#' + lastFile[i][3:].lower().replace(' ', '-') + ')')
        elif lastFile[i].startswith('### '):
            tableOfContent.append('  - [' + lastFile[i][4:] + '](#' + lastFile[i][4:].lower().replace(' ', '-') + ')')
        filteredLines.append(lastFile[i])
        i += 1
    lastFile.clear()
    lastFile.extend(filteredLines[:4] + tableOfContent + filteredLines[5:])

if args.markdown:
    try:
        if args.multiplayer:
            genApiMarkdown('Multiplayer')
        if args.singleplayer:
            genApiMarkdown('Singleplayer')
    
    except Exception as ex:
        showError('Can\'t generate markdown representation', ex)
    
    checkErrors()

"""
def genApi(target):
    # C++ projects
    if args.native:
        createFile('FOnline.' + target + '.h')

        # Generate source
        def parseType(t):
            def mapType(t):
                typeMap = {'int8': 'int8', 'uint8': 'uint8', 'int16': 'int16', 'uint16': 'uint16', 'int64': 'int64', 'uint64': 'uint64',
                        'ItemView': 'ScriptItem*', 'ItemHexView': 'ScriptItem*', 'PlayerView': 'ScriptPlayer*', 'Player': 'ScriptPlayer*',
                        'CritterView': 'ScriptCritter*', 'CritterHexView': 'ScriptCritter*', 'MapView': 'ScriptMap*', 'LocationView': 'ScriptLocation*',
                        'Item': 'ScriptItem*', 'Critter': 'ScriptCritter*', 'Map': 'ScriptMap*', 'Location': 'ScriptLocation*',
                        'string': 'std::string', 'Entity': 'ScriptEntity*'}
                return typeMap[t] if t in typeMap else t
            tt = t.split('.')
            if tt[0] == 'dict':
                r = 'std::map<' + mapType(tt[1]) + ', ' + mapType(tt[2]) + '>'
            elif tt[0] in userObjects:
                return tt[0] + '*'
            else:
                r = mapType(tt[0])
            if 'arr' in tt:
                r = 'std::vector<' + r + '>'
            if 'ref' in tt:
                r += '&'
            return r
        def parseArgs(args):
            return ', '.join([parseType(a[0]) + ' ' + a[1] for a in args])
        def writeDoc(ident, doc):
            if doc:
                writeFile(''.center(ident) + '/**')
                for d in doc:
                    writeFile(''.center(ident) + ' * ' + d)
                writeFile(''.center(ident) + ' */')
            else:
                writeFile(''.center(ident) + '/**')
                writeFile(''.center(ident) + ' * ...')
                writeFile(''.center(ident) + ' */')
        def writeMethod(tok, entity):
            writeDoc(4, tok[3])
            writeFile('    ' + parseType(tok[1]) + ' ' + tok[0] + '(' + parseArgs(tok[2]) + ');')
            writeFile('')
        def writeProp(tok, entity):
            rw, name, access, ret, mods, comms = tok
            if not (target == 'Mapper' and 'Virtual' in access) and \
                    not (target == 'Server' and 'PrivateClient' in access) and \
                    not (target == 'Client' and 'PrivateServer' in access):
                isGet, isSet = True, rw == 'rw'
                if isGet:
                    writeDoc(4, comms)
                    writeFile('    ' + parseType(ret) + ' Get' + name + '();')
                    writeFile('')
                if isSet:
                    writeDoc(4, comms)
                    writeFile('    void Set' + name + '(' + parseType(ret) + ' value);')
                    writeFile('')

        # Header
        writeFile('// FOnline scripting native API')
        writeFile('')
        writeFile('#include <cstdint>')
        writeFile('#include <vector>')
        writeFile('#include <map>')
        writeFile('#include <functional>')
        writeFile('')
        
        # Namespace begin
        writeFile('namespace FOnline')
        writeFile('{')
        writeFile('')
        
        # Usings
        writeFile('')
        
        # Forward declarations
        writeFile('class ScriptEntity;')
        for entity in ['Player', 'Item', 'Critter', 'Map', 'Location']:
            writeFile('class Script' + entity + ';')
        writeFile('class MapSprite;')
        writeFile('')
        
        # Enums
        for i in nativeMeta.enums:
            group, entries, doc = i
            writeDoc(0, doc)
            writeFile('enum class ' + group)
            writeFile('{')
            for e in entries:
                name, val, edoc = e
                writeDoc(4, edoc)
                writeFile('    ' + name + ' = ' + val + ',')
                if e != entries[len(entries) - 1]:
                    writeFile('')
            writeFile('};')
            writeFile('')

        # Global
        writeFile('class ScriptGame')
        writeFile('{')
        writeFile('public:')
        for i in nativeMeta.properties['global']:
            writeProp(i, None)
        if target == 'Server':
            for i in nativeMeta.methods['globalcommon']:
                writeMethod(i, None)
            for i in nativeMeta.methods['globalserver']:
                writeMethod(i, None)
        elif target == 'Client':
            for i in nativeMeta.methods['globalcommon']:
                writeMethod(i, None)
            for i in nativeMeta.methods['globalclient']:
                writeMethod(i, None)
        elif target == 'Single':
            for i in nativeMeta.methods['globalcommon']:
                writeMethod(i, None)
            for i in nativeMeta.methods['globalserver']:
                writeMethod(i, None)
            for i in nativeMeta.methods['globalclient']:
                writeMethod(i, None)
        elif target == 'Mapper':
            for i in nativeMeta.methods['globalmapper']:
                writeMethod(i, None)
        writeFile('')
        writeFile('private:')
        writeFile('    void* _mainObjPtr;')
        writeFile('};')
        writeFile('')

        # Entities
        writeFile('class ScriptEntity')
        writeFile('{')
        writeFile('protected:')
        writeFile('    void* _mainObjPtr;')
        writeFile('    void* _thisPtr;')
        writeFile('};')
        writeFile('')

        for entity in ['Player', 'Item', 'Critter', 'Map', 'Location']:
            writeFile('class Script' + entity + ' : public ScriptEntity')
            writeFile('{')
            writeFile('public:')
            for i in nativeMeta.properties[entity.lower()]:
                writeProp(i, entity)
            writeFile('')
            if target == 'Server' or target == 'Single':
                for i in nativeMeta.methods[entity.lower()]:
                    writeMethod(i, entity)
            if target == 'Client' or target == 'Single':
                for i in nativeMeta.methods[entity.lower() + 'view']:
                    writeMethod(i, entity)
            writeFile('};')
            writeFile('')

        # Events
        " ""
        writeFile('## Events')
        writeFile('')
        for ename in ['server', 'client', 'mapper']:
            writeFile('### ' + ename[0].upper() + ename[1:] + ' events')
            writeFile('')
            for e in nativeMeta.events[ename]:
                name, eargs, doc = e
                writeFile('* ' + name + '(' + parseArgs(eargs) + ')')
                writeDoc(doc)
            writeFile('')
        " ""

        # Settings
        " ""
        writeFile('## Settings')
        writeFile('')
        for i in nativeMeta.settings:
            ret, name, init, doc = i
            writeFile('* ' + parseType(ret) + ' ' + name + ' = ' + init)
            writeDoc(doc)
            writeFile('')
        " ""

        # Content pids
        " ""
        writeFile('## Content')
        writeFile('')
        def writeEnums(name, lst):
            writeFile('### ' + name + ' pids')
            writeFile('')
            for i in lst:
                writeFile('* ' +  i)
            writeFile('')
        writeEnums('Item', content['foitem'])
        writeEnums('Critter', content['focr'])
        writeEnums('Map', content['fomap'])
        writeEnums('Location', content['foloc'])
        " ""
        
        # Namespace end
        writeFile('} // namespace FOnline')

    # C# projects
    if args.csharp:
        # Generate source
        def writeHeader(rootClass, usings=None):
            writeFile('using System;')
            writeFile('using System.Collections.Generic;')
            writeFile('using System.Runtime.CompilerServices;')
            writeFile('using hash = System.UInt32;')
            if usings:
                for u in usings:
                    writeFile(u)
            writeFile('')
            writeFile('namespace FOnline')
            writeFile('{')
            writeFile('    ' + rootClass)
            writeFile('    {')
        def writeEndHeader():
            writeFile('    }')
            writeFile('}')
        def parseType(t):
            def mapType(t):
                typeMap = {'int8': 'sbyte', 'uint8': 'byte', 'int16': 'short', 'uint16': 'ushort', 'int': 'int', 'uint': 'uint', 'int64': 'long', 'uint64': 'ulong',
                        'PlayerView': 'Player', 'ItemView': 'Item', 'CritterView': 'Critter', 'MapView': 'Map', 'LocationView': 'Location'}
                return typeMap[t] if t in typeMap else t
            tt = t.split('.')
            if tt[0] == 'dict':
                r = 'Dictionary<' + mapType(tt[1]) + ', ' + mapType(tt[2]) + '>'
            elif tt[0] == 'callback':
                r = 'Action<' + mapType(tt[1]) + '>'
            elif tt[0] == 'predicate':
                r = 'Func<' + mapType(tt[1]) + ', bool>'
            else:
                r = mapType(tt[0])
            if 'arr' in tt:
                r += '[]'
            if 'ref' in tt:
                r = 'ref ' + r
            return r
        def parseArgs(args):
            return ', '.join([parseType(a[0]) + ' ' + a[1] for a in args])
        def parseExtArgs(args, entity):
            r = ['AppDomain domain']
            if entity:
                r.append('IntPtr entityPtr')
            return ', '.join(r + ['out Exception ex'] + [parseType(a[0]) + ' ' + a[1] for a in args])
        def parsePassArgs(args, entity, addDomEx=True):
            r = []
            if addDomEx:
                r.append('AppDomain.CurrentDomain')
            if entity:
                r.append('_entityPtr')
            if addDomEx:
                r.append('out _ex')
            return ', '.join(r + [('ref ' if 'ref' in a[0].split('.') else '') + a[1] for a in args])
        def writeDoc(ident, doc):
            if doc:
                for comm in doc[1:-1]:
                    writeFile(''.center(ident) + '/// ' + comm[3:])
        def writeMethod(tok, entity, extCalls):
            writeDoc(8, tok[3])
            writeFile('        public ' + ('static ' if entity is None else '') + parseType(tok[1]) + ' ' + tok[0] + '(' + parseArgs(tok[2]) + ')')
            writeFile('        {')
            writeFile('            Exception _ex;')
            writeFile('            ' + ('var _result = ' if tok[1] != 'void' else '') +
                    '_' + tok[0] + '(' + parsePassArgs(tok[2], entity) + ');')
            writeFile('            if (_ex != null)')
            writeFile('                throw _ex;')
            if tok[1] != 'void':
                writeFile('            return _result;')
            writeFile('        }')
            writeFile('')
            extCalls.append('        [MethodImpl(MethodImplOptions.InternalCall)]')
            extCalls.append('        extern static ' + parseType(tok[1]) + ' _' + tok[0] + '(' + parseExtArgs(tok[2], entity) + ');')
        def writeProp(tok, entity, extCalls):
            rw, name, access, ret, mods, comms = tok
            if not (target == 'Mapper' and 'Virtual' in access) and \
                    not (target == 'Server' and 'PrivateClient' in access) and \
                    not (target == 'Client' and 'PrivateServer' in access):
                isGet, isSet = True, rw == 'rw'
                writeDoc(8, comms)
                writeFile('        public ' + ('static ' if entity is None else '') + parseType(ret) + ' ' + name)
                writeFile('        {')
                if isGet:
                    writeFile('            get')
                    writeFile('            {')
                    writeFile('                Exception _ex;')
                    if entity:
                        writeFile('                var _result = _Get_' + name + '(AppDomain.CurrentDomain, _entityPtr, out _ex);')
                    else:
                        writeFile('                var _result = _Get_' + name + '(AppDomain.CurrentDomain, out _ex);')
                    writeFile('                if (_ex != null)')
                    writeFile('                    throw _ex;')
                    writeFile('                return _result;')
                    writeFile('            }')
                    extCalls.append('        [MethodImpl(MethodImplOptions.InternalCall)]')
                    if entity:
                        extCalls.append('        extern static ' + parseType(ret) + ' _Get_' + name + '(AppDomain domain, IntPtr entityPtr, out Exception ex);')
                    else:
                        extCalls.append('        extern static ' + parseType(ret) + ' _Get_' + name + '(AppDomain domain, out Exception ex);')
                if isSet:
                    writeFile('            set')
                    writeFile('            {')
                    writeFile('                Exception _ex;')
                    if entity:
                        writeFile('                _Set_' + name + '(AppDomain.CurrentDomain, _entityPtr, out _ex, value);')
                    else:
                        writeFile('                _Set_' + name + '(AppDomain.CurrentDomain, out _ex, value);')
                    writeFile('                if (_ex != null)')
                    writeFile('                    throw _ex;')
                    writeFile('            }')
                    extCalls.append('        [MethodImpl(MethodImplOptions.InternalCall)]')
                    if entity:
                        extCalls.append('        extern static void _Set_' + name + '(AppDomain domain, IntPtr entityPtr, out Exception ex, ' + parseType(ret) + ' value);')
                    else:
                        extCalls.append('        extern static void _Set_' + name + '(AppDomain domain, out Exception ex, ' + parseType(ret) + ' value);')
                writeFile('        }')
                writeFile('')

        # Global methods
        createFile(target + 'Game.cs')
        writeHeader('public static partial class Game')
        extCalls = []
        if target == 'Server':
            for i in monoMeta.methods['globalcommon']:
                writeMethod(i, None, extCalls)
            for i in monoMeta.methods['globalserver']:
                writeMethod(i, None, extCalls)
        elif target == 'Client':
            for i in monoMeta.methods['globalcommon']:
                writeMethod(i, None, extCalls)
            for i in monoMeta.methods['globalclient']:
                writeMethod(i, None, extCalls)
        elif target == 'Single':
            for i in monoMeta.methods['globalcommon']:
                writeMethod(i, None, extCalls)
            for i in monoMeta.methods['globalserver']:
                writeMethod(i, None, extCalls)
            for i in monoMeta.methods['globalclient']:
                writeMethod(i, None, extCalls)
        elif target == 'Mapper':
            for i in monoMeta.methods['globalcommon']:
                writeMethod(i, None, extCalls)
            for i in monoMeta.methods['globalmapper']:
                writeMethod(i, None, extCalls)
        writeFile('')
        for i in extCalls:
            writeFile(i)
        writeEndHeader()

        # Global properties
        createFile(target + 'Globals.cs')
        writeHeader('public static partial class Game')
        extCalls = []
        for i in monoMeta.properties['global']:
            writeProp(i, None, extCalls)
        for i in extCalls:
            writeFile(i)
        writeEndHeader()

        # Entities
        for entity in ['Player', 'Item', 'Critter', 'Map', 'Location']:
            createFile(target + entity + '.cs')
            writeHeader('public partial class ' + entity + ' : Entity')
            extCalls = []
            if target == 'Server':
                for i in monoMeta.properties[entity.lower()]:
                    writeProp(i, entity, extCalls)
                for i in monoMeta.methods[entity.lower()]:
                    writeMethod(i, entity, extCalls)
            elif target == 'Client':
                for i in monoMeta.properties[entity.lower()]:
                    writeProp(i, entity, extCalls)
                for i in monoMeta.methods[entity.lower() + 'view']:
                    writeMethod(i, entity, extCalls)
            elif target == 'Single':
                for i in monoMeta.properties[entity.lower()]:
                    writeProp(i, entity, extCalls)
                for i in monoMeta.methods[entity.lower()]:
                    writeMethod(i, entity, extCalls)
                for i in monoMeta.methods[entity.lower() + 'view']:
                    writeMethod(i, entity, extCalls)
            elif target == 'Mapper':
                for i in monoMeta.properties[entity.lower()]:
                    writeProp(i, entity, extCalls)
            for i in extCalls:
                writeFile(i)
            writeEndHeader()

        # Events
        def writeEvent(tok):
            name, eargs, doc = tok
            writeDoc(8, doc)
            writeFile('        public static event ' + name + 'Delegate ' + name + ';')
            writeFile('        public delegate void ' + name + 'Delegate(' + parseArgs(eargs) + ');')
            writeFile('        public static event ' + name + 'RetDelegate ' + name + 'Ret;')
            writeFile('        public delegate bool ' + name + 'RetDelegate(' + parseArgs(eargs) + ');')
            writeFile('')
        def writeEventExt(tok):
            name, eargs, doc = tok
            pargs = parseArgs(eargs)
            writeFile('        static bool _' + name + '(' + (pargs + ', ' if pargs else '') + 'out Exception[] exs)')
            writeFile('        {')
            writeFile('            exs = null;')
            writeFile('            foreach (var eventDelegate in ' + name + '.GetInvocationList().Cast<' + name + 'Delegate>())')
            writeFile('            {')
            writeFile('                try')
            writeFile('                {')
            writeFile('                    eventDelegate(' + parsePassArgs(eargs, None, False) + ');')
            writeFile('                }')
            writeFile('                catch (Exception ex)')
            writeFile('                {')
            writeFile('                    exs = exs == null ? new Exception[] { ex } : exs.Concat(new Exception[] { ex }).ToArray();')
            writeFile('                }')
            writeFile('            }')
            writeFile('            foreach (var eventDelegate in ' + name + 'Ret.GetInvocationList().Cast<' + name + 'RetDelegate>())')
            writeFile('            {')
            writeFile('                try')
            writeFile('                {')
            writeFile('                    if (eventDelegate(' + parsePassArgs(eargs, None, False) + '))')
            writeFile('                        return true;')
            writeFile('                }')
            writeFile('                catch (Exception ex)')
            writeFile('                {')
            writeFile('                    exs = exs == null ? new Exception[] { ex } : exs.Concat(new Exception[] { ex }).ToArray();')
            writeFile('                }')
            writeFile('            }')
            writeFile('            return false;')
            writeFile('        }')
            writeFile('')
        createFile(target + 'Events.cs')
        writeHeader('public static partial class Game', ['using System.Linq;'])
        if target == 'Server':
            for e in monoMeta.events['server']:
                writeEvent(e)
            for e in monoMeta.events['server']:
                writeEventExt(e)
        elif target == 'Client':
            for e in monoMeta.events['client']:
                writeEvent(e)
            for e in monoMeta.events['client']:
                writeEventExt(e)
        elif target == 'Single':
            for ename in ['server', 'client']:
                for e in monoMeta.events[ename]:
                    writeEvent(e)
            for ename in ['server', 'client']:
                for e in monoMeta.events[ename]:
                    writeEventExt(e)
        elif target == 'Mapper':
            for e in monoMeta.events['mapper']:
                writeEvent(e)
            for e in monoMeta.events['mapper']:
                writeEventExt(e)
        writeEndHeader()

        # Settings
        createFile(target + 'Settings.cs')
        writeHeader('public static partial class Game')
        writeFile('        public static class Settings')
        writeFile('        {')
        for i in monoMeta.settings:
            ret, name, init, doc = i
            writeDoc(12, doc)
            writeFile('            public static ' + parseType(ret) + ' ' + name)
            writeFile('            {')
            writeFile('                get')
            writeFile('                {')
            writeFile('                    Exception _ex;')
            writeFile('                    var _result = _Setting_' + name + '(AppDomain.CurrentDomain, out _ex);')
            writeFile('                    if (_ex != null)')
            writeFile('                        throw _ex;')
            writeFile('                    return _result;')
            writeFile('                }')
            writeFile('            }')
            writeFile('')
            extCalls.append('        [MethodImpl(MethodImplOptions.InternalCall)]')
            extCalls.append('        extern static ' + parseType(ret) + ' _Setting_' + name + '(AppDomain domain, out Exception ex);')
        writeFile('        }')
        writeEndHeader()

        # Enums
        createFile(target + 'Enums.cs')
        writeFile('namespace FOnline')
        writeFile('{')
        for i in monoMeta.enums:
            group, entries, doc = i
            writeDoc(4, doc)
            writeFile('    public enum ' + group)
            writeFile('    {')
            for e in entries:
                name, val, edoc = e
                writeDoc(8, edoc)
                writeFile('        ' + name + ' = ' + val + ',')
            writeFile('    }')
            writeFile('')
        writeFile('}')

        # Content pids
        createFile(target + 'Content.cs')
        writeFile('namespace FOnline')
        writeFile('{')
        writeFile('    public static class Content')
        writeFile('    {')
        def writeEnums(name, lst):
            writeFile('        public enum ' + name)
            writeFile('        {')
            for i in lst:
                #writeFile('            ' + i + ' = ' + getHash(i) + ',')
                pass
            writeFile('        }')
            writeFile('')
        writeEnums('Item', content['foitem'])
        writeEnums('Critter', content['focr'])
        writeEnums('Map', content['fomap'])
        writeEnums('Location', content['foloc'])
        writeFile('    }')
        writeFile('}')

        # Generate .csproj files
        for assembly in args.monoassembly:
            csprojName = assembly + '.' + target + '.csproj'
            projGuid = getGuid(csprojName)
            csprojects.append((csprojName, projGuid))

            createFile(csprojName)
            writeFile('<?xml version="1.0" encoding="utf-8"?>')
            writeFile('<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">')

            writeFile('  <PropertyGroup>')
            writeFile('    <Configuration Condition=" \'$(Configuration)\' == \'\' ">Debug</Configuration>')
            writeFile('    <Platform Condition=" \'$(Platform)\' == \'\' ">AnyCPU</Platform>')
            writeFile('    <ProjectGuid>' + projGuid + '</ProjectGuid>')
            writeFile('    <OutputType>Library</OutputType>')
            writeFile('    <RootNamespace>' + assembly + '</RootNamespace>')
            writeFile('    <AssemblyName>' + assembly + '.' + target + '</AssemblyName>')
            writeFile('    <TargetFrameworkVersion>v4.5</TargetFrameworkVersion>')
            writeFile('    <FileAlignment>512</FileAlignment>')
            writeFile('    <Deterministic>true</Deterministic>')
            writeFile('  </PropertyGroup>')

            writeFile('  <PropertyGroup Condition=" \'$(Configuration)|$(Platform)\' == \'Debug|AnyCPU\' ">')
            writeFile('    <DebugSymbols>true</DebugSymbols>')
            writeFile('    <DebugType>embedded</DebugType>')
            writeFile('    <Optimize>false</Optimize>')
            writeFile('    <OutputPath>bin\\Debug\\</OutputPath>')
            writeFile('    <DefineConstants>DEBUG;TRACE;' + target.upper() + '</DefineConstants>')
            writeFile('    <ErrorReport>prompt</ErrorReport>')
            writeFile('    <WarningLevel>4</WarningLevel>')
            writeFile('  </PropertyGroup>')

            writeFile('  <PropertyGroup Condition=" \'$(Configuration)|$(Platform)\' == \'Release|AnyCPU\' ">')
            writeFile('    <DebugType>embedded</DebugType>')
            writeFile('    <Optimize>true</Optimize>')
            writeFile('    <OutputPath>bin\\Release\\</OutputPath>')
            writeFile('    <DefineConstants>TRACE;' + target.upper() + '</DefineConstants>')
            writeFile('    <ErrorReport>prompt</ErrorReport>')
            writeFile('    <WarningLevel>4</WarningLevel>')
            writeFile('  </PropertyGroup>')

            writeFile('  <ItemGroup>')
            if target == 'Server':
                for src in args.monoserversource:
                    if src.split(',')[0] == assembly:
                        writeFile('    <Compile Include="' + src.split(',')[1].replace('/', '\\') + '" />')
            elif target == 'Client':
                for src in args.monoclientsource:
                    if src.split(',')[0] == assembly:
                        writeFile('    <Compile Include="' + src.split(',')[1].replace('/', '\\') + '" />')
            elif target == 'Single':
                for src in args.monosinglesource:
                    if src.split(',')[0] == assembly:
                        writeFile('    <Compile Include="' + src.split(',')[1].replace('/', '\\') + '" />')
            elif target == 'Mapper':
                for src in args.monomappersource:
                    if src.split(',')[0] == assembly:
                        writeFile('    <Compile Include="' + src.split(',')[1].replace('/', '\\') + '" />')
            writeFile('    <Compile Include="' + target + 'Game.cs" />')
            writeFile('    <Compile Include="' + target + 'Globals.cs" />')
            writeFile('    <Compile Include="' + target + 'Player.cs" />')
            writeFile('    <Compile Include="' + target + 'Item.cs" />')
            writeFile('    <Compile Include="' + target + 'Critter.cs" />')
            writeFile('    <Compile Include="' + target + 'Map.cs" />')
            writeFile('    <Compile Include="' + target + 'Location.cs" />')
            writeFile('    <Compile Include="' + target + 'Events.cs" />')
            writeFile('    <Compile Include="' + target + 'Settings.cs" />')
            writeFile('    <Compile Include="' + target + 'Enums.cs" />')
            writeFile('    <Compile Include="' + target + 'Content.cs" />')
            writeFile('  </ItemGroup>')

            writeFile('  <ItemGroup>')
            def addRef(ref):
                if ref in args.monoassembly:
                    writeFile('    <ProjectReference Include="' + ref + '.' + target + '.csproj">')
                    writeFile('      <Project>' + getGuid(ref + '.' + target + '.csproj') + '</Project>')
                    writeFile('      <Name>' + ref + '.' + target + '</Name>')
                    writeFile('    </ProjectReference>')
                else:
                    writeFile('    <Reference Include="' + ref + '">')
                    writeFile('      <Private>True</Private>')
                    writeFile('    </Reference>')
            if target == 'Server':
                for ref in args.monoserverref:
                    if ref.split(',')[0] == assembly:
                        addRef(ref.split(',')[1])
            elif target == 'Client':
                for ref in args.monoclientref:
                    if ref.split(',')[0] == assembly:
                        addRef(ref.split(',')[1])
            elif target == 'Single':
                for ref in args.monoclientref:
                    if ref.split(',')[0] == assembly:
                        addRef(ref.split(',')[1])
            elif target == 'Mapper':
                for ref in args.monomapperref:
                    if ref.split(',')[0] == assembly:
                        addRef(ref.split(',')[1])
            writeFile('  </ItemGroup>')

            writeFile('  <Import Project="$(MSBuildToolsPath)\\Microsoft.CSharp.targets" />')
            writeFile('</Project>')
"""

csprojects = []
"""
try:
    if args.multiplayer:
        genApi('Server')
        genApi('Client')
    if args.singleplayer:
        genApi('Single')
    if args.mapper:
        genApi('Mapper')
        
except Exception as ex:
    showError('Can\'t generate scripts', ex)
"""

# Write solution file
if csprojects:
    try:
        # Write solution file that contains all project files
        slnName = args.monoassembly[0] + '.sln'
        createFile(slnName)
        writeFile('')
        writeFile('Microsoft Visual Studio Solution File, Format Version 12.00')
        writeFile('# Visual Studio Version 16')
        writeFile('VisualStudioVersion = 16.0.29905.134')
        writeFile('MinimumVisualStudioVersion = 10.0.40219.1')

        for name, guid in csprojects:
            writeFile('Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "' +
                    name[:-7] + '", "' + name + '", "' + guid + '"')
            writeFile('EndProject')

        writeFile('Global')
        writeFile('    GlobalSection(SolutionConfigurationPlatforms) = preSolution')
        writeFile('        Debug|Any CPU = Debug|Any CPU')
        writeFile('        Release|Any CPU = Release|Any CPU')
        writeFile('    EndGlobalSection')
        writeFile('    GlobalSection(ProjectConfigurationPlatforms) = postSolution')

        for name, guid in csprojects:
            writeFile('    ' + guid + '.Debug|Any CPU.ActiveCfg = Debug|Any CPU')
            writeFile('    ' + guid + '.Debug|Any CPU.Build.0 = Debug|Any CPU')
            writeFile('    ' + guid + '.Release|Any CPU.ActiveCfg = Release|Any CPU')
            writeFile('    ' + guid + '.Release|Any CPU.Build.0 = Release|Any CPU')

        writeFile('    EndGlobalSection')
        writeFile('    GlobalSection(SolutionProperties) = preSolution')
        writeFile('        HideSolutionNode = FALSE')
        writeFile('    EndGlobalSection')
        writeFile('    GlobalSection(ExtensibilityGlobals) = postSolution')
        writeFile('        SolutionGuid = ' + getGuid(slnName))
        writeFile('    EndGlobalSection')
        writeFile('EndGlobal')
        writeFile('')
    
    except Exception as ex:
        showError('Can\'t write solution files', ex)

checkErrors()

# Embedded resources
try:
    #zipData = io.BytesIO()
    #with zipfile.ZipFile(zipData, 'w', compression=zipfile.ZIP_DEFLATED) as zip:
    #    for res in resources['Embedded']:
    #        zip.write('Backed_' + res[1], res[0])
    #createFile('EmbeddedResources-Include.h', args.genoutput)
    #writeFile('const uint8 EMBEDDED_RESOURCES[] = {0x' + ', 0x'.join(zipData.getvalue().hex(' ').split(' ')) + '};')
    preserveBufSize = 1200000 # Todo: move preserveBufSize to build setup
    assert preserveBufSize > 100
    createFile('EmbeddedResources-Include.h', args.genoutput)
    writeFile('volatile const uint8 EMBEDDED_RESOURCES[' + str(preserveBufSize) + '] = {' + ','.join([str((i + 42) % 200) for i in range(preserveBufSize)]) + '};')
    
except Exception as ex:
    showError('Can\'t write embedded resources', ex)

checkErrors()

# Default settings
createFile('DebugSettings-Include.h', args.genoutput)
writeFile('R"CONFIG(###DebugConfig###')
for cfg in args.config:
    k, v = cfg.split(',', 1)
    if len(v) > 0 and v[0] == '+':
        writeFile(k + ' += ' + v[1:])
    else:
        writeFile(k + ' = ' + v)
writeFile('###DebugConfigEnd###)CONFIG"')

# Version info
createFile('Version-Include.h', args.genoutput)
writeFile('static constexpr auto FO_BUILD_HASH = "' + args.buildhash + '";')
writeFile('static constexpr auto FO_DEV_NAME = "' + args.devname + '";')
writeFile('static constexpr auto FO_GAME_NAME = "' + args.gamename + '";')
writeFile('static constexpr auto FO_GAME_VERSION = "' + args.gameversion + '";')
writeFile('static constexpr auto FO_COMPATIBILITY_VERSION = ' + getHash(args.buildhash) + ';')

# Actual writing of generated files
try:
    flushFiles()
    
except Exception as ex:
    showError('Can\'t flush generated files', ex)

checkErrors()

elapsedTime = time.time() - startTime
print('[CodeGen]', 'Code generation complete in ' + '{:.2f}'.format(elapsedTime) + ' seconds')
