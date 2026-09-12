import AppKit
import Foundation
import Security

let health = URL(string:"http://127.0.0.1:8782/healthz")!, learner = URL(string:"http://127.0.0.1:8782/trainer/")!
let support = FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Application Support/Eksamio/StudentStaging")
let ownerFile = support.appendingPathComponent("runtime-owner.json")
struct Owner: Codable { let pid:Int32; let python:String; let runtime:String; let marker:String }
func key() throws -> String {
  let service="ru.eksamio.student-staging", account="runtime-key", query:[String:Any]=[kSecClass as String:kSecClassGenericPassword,kSecAttrService as String:service,kSecAttrAccount as String:account,kSecReturnData as String:true]
  var item:CFTypeRef?; if SecItemCopyMatching(query as CFDictionary,&item)==errSecSuccess, let d=item as? Data { return String(decoding:d,as:UTF8.self) }
  var bytes=[UInt8](repeating:0,count:32); guard SecRandomCopyBytes(kSecRandomDefault,bytes.count,&bytes)==errSecSuccess else { throw NSError(domain:"key",code:1) }
  let value=bytes.map{String(format:"%02x",$0)}.joined(), data=Data(value.utf8)
  var add=query; add.removeValue(forKey:kSecReturnData as String); add[kSecValueData as String]=data; guard SecItemAdd(add as CFDictionary,nil)==errSecSuccess else { throw NSError(domain:"key",code:2) }; return value
}
func processArguments(_ pid:Int32)->[String] { let p=Process(); p.executableURL=URL(fileURLWithPath:"/bin/ps"); p.arguments=["-p",String(pid),"-o","command="]; let q=Pipe();p.standardOutput=q;try? p.run();p.waitUntilExit();return String(decoding:q.fileHandleForReading.readDataToEndOfFile(),as:UTF8.self).split(separator:" ").map(String.init) }
func verifiedOwner()->Owner? { guard let d=try? Data(contentsOf:ownerFile),let o=try? JSONDecoder().decode(Owner.self,from:d) else{return nil};let a=processArguments(o.pid);return a.contains(o.python)&&a.contains(o.runtime)&&a.contains("--owner-marker="+o.marker) ? o:nil }
func healthy()->Bool { (try? Data(contentsOf:health)) != nil }

final class Panel:NSObject,NSApplicationDelegate {
  var window:NSWindow!, status=NSTextField(labelWithString:"Остановлен"), starting=false, child:Process?
  func applicationDidFinishLaunching(_ n:Notification){ window=NSWindow(contentRect:NSRect(x:0,y:0,width:430,height:220),styleMask:[.titled,.closable],backing:.buffered,defer:false);let v=NSStackView();v.orientation = .vertical;v.spacing=12;v.edgeInsets=NSEdgeInsets(top:20,left:20,bottom:20,right:20);v.addArrangedSubview(NSTextField(labelWithString:"STAGING — не публичный сайт"));v.addArrangedSubview(status);for (t,a) in [("Запустить Eksamio",#selector(start)),("Открыть как ученик",#selector(openLearner)),("Остановить",#selector(stop))]{let b=NSButton(title:t,target:self,action:a);v.addArrangedSubview(b)};window.contentView=v;window.makeKeyAndOrderFront(nil);refresh() }
  func refresh(){ if healthy(){status.stringValue=verifiedOwner() == nil ? "Ошибка: порт занят неизвестным процессом":"Работает"}else{status.stringValue="Остановлен"} }
  @objc func start(){ if starting || verifiedOwner() != nil{return}; if healthy(){refresh();return};starting=true;status.stringValue="Запускается";do{try FileManager.default.createDirectory(at:support,withIntermediateDirectories:true);let info=Bundle.main.infoDictionary!, python=info["EksamioPython"] as! String,runtime=info["EksamioRuntime"] as! String,marker=UUID().uuidString;let p=Process();p.executableURL=URL(fileURLWithPath:python);p.arguments=[runtime,"--owner-marker="+marker];p.environment=["EKSAMIO_STAGING_SECRET_STDIN":"1","EKSAMIO_STAGING_DB":support.appendingPathComponent("student-staging.sqlite").path,"EKSAMIO_STAGING_HOST":"127.0.0.1","EKSAMIO_STAGING_PORT":"8782"];let input=Pipe();p.standardInput=input;let log=FileHandle(forWritingAtPath:support.appendingPathComponent("runtime.log").path) ?? FileHandle.standardError;p.standardOutput=log;p.standardError=log;try p.run();input.fileHandleForWriting.write(Data((try key()+"\n").utf8));input.fileHandleForWriting.closeFile();let o=Owner(pid:p.processIdentifier,python:python,runtime:runtime,marker:marker);try JSONEncoder().encode(o).write(to:ownerFile,options:.atomic);child=p;DispatchQueue.main.asyncAfter(deadline:.now()+1){self.starting=false;self.refresh()}}catch{starting=false;status.stringValue="Ошибка"}}
  @objc func openLearner(){ guard healthy(),verifiedOwner() != nil else{status.stringValue="Ошибка: порт занят неизвестным процессом";return};NSWorkspace.shared.open(learner) }
  @objc func stop(){guard let o=verifiedOwner() else{refresh();return};kill(o.pid,SIGTERM);let end=Date().addingTimeInterval(8);while kill(o.pid,0)==0 && Date()<end{Thread.sleep(forTimeInterval:0.1)};guard kill(o.pid,0) != 0 else{status.stringValue="Ошибка: процесс не остановлен";return};try? FileManager.default.removeItem(at:ownerFile);child=nil;refresh()}
}
let app=NSApplication.shared,panel=Panel();app.delegate=panel;app.run()
