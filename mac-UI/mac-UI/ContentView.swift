//
//  ContentView.swift
//  mac-UI
//
//  Created by 袁新宇 on 2024/11/26.
//

import SwiftUI
import Pow
import AppKit
import Foundation
import Network

extension NSTextField{
    open override var focusRingType:NSFocusRingType{
        get {
            return .none
        }
        set{}
    }
}


/// 根据 [log]、[debug] 和 [unknown] 分割消息
func splitMessages(from message: String) -> [String] {
    let pattern = #"\[(log|debug|unknown)\].*?(?=\[log\]|\[debug\]|\[unknown\]|$)"#
    var results: [String] = []
    
    do {
        let regex = try NSRegularExpression(pattern: pattern, options: [])
        let matches = regex.matches(in: message, options: [], range: NSRange(location: 0, length: message.utf16.count))
        
        for match in matches {
            if let range = Range(match.range, in: message) {
                results.append(String(message[range]))
            }
        }
    } catch {
        print("正则表达式错误: \(error)")
    }
    
    return results
}


class SocketCommunicator: ObservableObject {
    private var connection: NWConnection?
    private let queue = DispatchQueue(label: "SocketCommunicatorQueue")
    
    @Published var receivedMessages: [String] = [] // 所有收到的消息（备用）
    @Published var userLogMessages: [String] = ["用户日志初始化..."] // 用户日志信息
    @Published var debugLogMessages: [String] = ["调试日志初始化..."] // 调试日志信息
    
    init() {}
    
    deinit {
        send(message: "disconnect")
        disconnect() // 在对象销毁时断开连接
        print("SocketCommunicator 已销毁，连接已断开")
    }
    
    /// 连接到服务器
    func connect() {
        let host: String = "127.0.0.1"
        let port: UInt16 = 12345
        
        connection = NWConnection(host: NWEndpoint.Host(host), port: NWEndpoint.Port(rawValue: port)!, using: .tcp)
        connection?.stateUpdateHandler = { state in
            switch state {
            case .ready:
                print("✅ 已成功连接到 \(host):\(port)")
                self.receive() // 开始监听消息
            case .failed(let error):
                print("❌ 连接失败: \(error)")
            case .cancelled:
                print("❌ 连接被取消")
            default:
                break
            }
        }
        connection?.start(queue: queue)
    }
    
    /// 发送消息到服务器
    func send(message: String) {
        guard let connection = connection else {
            print("⚠️ 连接未建立")
            return
        }
        let data = message.data(using: .utf8) ?? Data()
        connection.send(content: data, completion: .contentProcessed { error in
            if let error = error {
                print("❌ 消息发送失败: \(error)")
            } else {
                print("✅ 消息已发送: \(message)")
            }
        })
    }
    
    /// 接收服务器返回的消息
    private func receive() {
        connection?.receive(minimumIncompleteLength: 1, maximumLength: 1024) { [weak self] content, _, isComplete, error in
            if let error = error {
                print("❌ 接收消息失败: \(error)")
            }
            if let data = content, let message = String(data: data, encoding: .utf8) {
                DispatchQueue.main.async {
                    self?.processMessage(message) // 处理消息类型并更新日志
                }
            }
            if isComplete {
                print("✅ 接收完成")
            } else {
                self?.receive() // 继续接收
            }
        }
    }
    
    private func processMessage(_ message: String) {
        // 分割消息
        let splitMessages = splitMessages(from: message)
        
        for singleMessage in splitMessages {
            receivedMessages.append(singleMessage)
            
            if singleMessage.hasPrefix("[log]") {
                userLogMessages.append(singleMessage)
                print("📩 用户日志: \(singleMessage)")
            } else if singleMessage.hasPrefix("[debug]") {
                debugLogMessages.append(singleMessage)
                print("🐛 调试日志: \(singleMessage)")
            } else if singleMessage.hasPrefix("[unknown]") {
                debugLogMessages.append(singleMessage)
                print("❓ 未知日志: \(singleMessage)")
            } else {
                debugLogMessages.append("未知消息类型: \(singleMessage)")
                print("❓ 未知消息类型: \(singleMessage)")
            }
        }
    }
    
    /// 断开连接
    func disconnect() {
        connection?.cancel()
        print("🔌 已断开连接")
    }
}



/* ----------------------------- APP 主界面 ------------------------------------ */
//struct ContentView: View {
//    @State private var path: String = "1" // 用户输入的路径
//    @State private var pathAttempts: Int = 100 // 输入尝试次数
//    @State private var isProcessing: Bool = false // 是否正在验证路径
//    @State private var isValidPath: Bool = true // 路径是否有效
//    @StateObject private var socketCommunicator = SocketCommunicator() // 通信器对象
//    
//    @State private var userLog: [String] = ["用户日志初始化..."] // 用户日志数组
//    @State private var debugLog: [String] = ["调试日志初始化..."] // 调试日志数组
//    
//    @State private var isCarRun: Bool = false   // 小车是否正在运行
//
//    var body: some View {
//        VStack(spacing: 10) {
//            // 标题
//            Text("MQTT 用户界面")
//                .font(.largeTitle)
//                .bold()
//                .padding(.top, 20)
//
//            // 日志显示模块
//            HStack(alignment: .top, spacing: 20) {
//                LogView(title: "用户日志", logs: userLog, fontColor: Color.green.opacity(0.85))
//                LogView(title: "调试日志", logs: debugLog, fontColor: Color.blue.opacity(0.85))
//            }
//            .frame(maxWidth: .infinity, maxHeight: 250) // 让日志模块自适应布局
//            .padding()
//            
//            // 第一排：按钮
//            HStack(spacing: 220) {
//                // 按钮：初始化智能车
//                Button("初始化智能车") {
//                    socketCommunicator.send(message: "init") // 发送“init”字符串
//                    debugLog.append("发送指令: init")
//                    isCarRun = true // 开始小车动画
//                }
//                .buttonStyle(PushDownButtonStyle())
//                
//                // 按钮：发送停止指令
//                Button("发送停止指令") {
//                    socketCommunicator.send(message: "stop") // 发送“stop”字符串
//                    debugLog.append("发送指令: stop")
//                    isCarRun = false // 开始小车动画
//                }
//                .buttonStyle(PushDownButtonStyle())
//            }
//            .padding(.bottom, 20)
//            
//            // 第二排：按钮和小车动画
//            HStack(spacing: 160) {
//                VStack(spacing: 4) {
//                    // 按钮：发送任务指令
//                    Button("发送任务指令") {
//                        let taskMessage = "task:\(path)"
//                        socketCommunicator.send(message: taskMessage) // 发送“task:<path>”字符串
//                        debugLog.append("发送指令: \(taskMessage)")
//                        isCarRun = true // 开始小车动画
//                    }
//                    .buttonStyle(PushDownButtonStyle())
//                }
//                
//                // 小车动画
//                CarAnimationView(isRunning: $isCarRun) // 自定义小车动画视图
//                    .frame(width: 200, height: 100) // 设置动画视图大小
//                
//            }
//            .padding(.bottom, 5) // 保留底部间距
//            
//            // 路径选择输入框
//            VStack(spacing: 2) {
//                TextField("请输入选择的路径：1 or 2", text: $path)
//                    .changeEffect(.shake(rate: .fast), value: pathAttempts, isEnabled: !isValidPath)
//                    .disabled(isProcessing)
//                    .textFieldStyle(.roundedBorder)
//                    .frame(width: 180) // 调整输入框宽度
//                    .padding(.horizontal, 32)
//                
//                // 输入框错误提示
//                if !isValidPath {
//                    Text("输入路径无效")
//                        .foregroundColor(.red)
//                        .font(.caption)
//                }
//            }
//            .padding(.bottom, 20) // 与按钮区域保持间距
//        }
//        .frame(maxWidth: .infinity, maxHeight: .infinity) // 让整个内容填满窗口
//        .padding()
//        .onAppear {
//            debugLog.append("尝试连接到服务器...")
//            socketCommunicator.connect() // 界面加载时自动连接到服务器
//           
//        }
//    }
//}

struct ContentView: View {
    @State private var path: String = "" // 用户输入的路径
    @State private var pathAttempts: Int = 100 // 输入尝试次数
    @State private var isProcessing: Bool = false // 是否正在验证路径
    @State private var isValidPath: Bool = true // 路径是否有效
    @StateObject private var socketCommunicator = SocketCommunicator() // 通信器对象
    
    @State private var isCarRun: Bool = false   // 小车是否正在运行

    var body: some View {
        VStack(spacing: 10) {
            // 标题
            Text("MQTT 用户界面")
                .font(.largeTitle)
                .bold()
                .padding(.top, 20)

            // 日志显示模块
            HStack(alignment: .top, spacing: 20) {
                LogView(title: "用户日志", logs: socketCommunicator.userLogMessages, fontColor: Color.green.opacity(0.85))
                LogView(title: "调试日志", logs: socketCommunicator.debugLogMessages, fontColor: Color.blue.opacity(0.85))
            }
            .frame(maxWidth: .infinity, maxHeight: 250) // 让日志模块自适应布局
            .padding()
            
            // 第一排：按钮
            HStack(spacing: 220) {
                // 按钮：初始化智能车
                Button("初始化智能车") {
                    socketCommunicator.send(message: "init") // 发送“init”字符串
                    socketCommunicator.debugLogMessages.append("发送指令: init")
                    isCarRun = true // 开始小车动画
                }
                .buttonStyle(PushDownButtonStyle())
                
                // 按钮：发送停止指令
                Button("发送停止指令") {
                    socketCommunicator.send(message: "stop") // 发送“stop”字符串
                    socketCommunicator.debugLogMessages.append("发送指令: stop")
                    isCarRun = false // 停止小车动画
                }
                .buttonStyle(PushDownButtonStyle())
            }
            .padding(.bottom, 20)
            
            // 第二排：按钮和小车动画
            HStack(spacing: 160) {
                VStack(spacing: 4) {
                    // 按钮：发送任务指令
                    Button("发送任务指令") {
                        let taskMessage = "task:\(path)"
                        socketCommunicator.send(message: taskMessage) // 发送“task:<path>”字符串
                        socketCommunicator.debugLogMessages.append("发送指令: \(taskMessage)")
                        isCarRun = true // 开始小车动画
                    }
                    .buttonStyle(PushDownButtonStyle())
                }
                
                // 小车动画
                CarAnimationView(isRunning: $isCarRun) // 自定义小车动画视图
                    .frame(width: 200, height: 100) // 设置动画视图大小
                
            }
            .padding(.bottom, 5) // 保留底部间距
            
            // 路径选择输入框
            VStack(spacing: 2) {
                TextField("请输入选择的路径：1 or 2", text: $path)
                    .changeEffect(.shake(rate: .fast), value: pathAttempts, isEnabled: !isValidPath)
                    .disabled(isProcessing)
                    .textFieldStyle(.roundedBorder)
                    .frame(width: 180) // 调整输入框宽度
                    .padding(.horizontal, 32)
                    .onSubmit {
                        validatePath()
                    }

                
                // 输入框错误提示
                if !isValidPath {
                    Text("输入路径无效")
                        .foregroundColor(.red)
                        .font(.caption)
                }
            }
            .padding(.bottom, 20) // 与按钮区域保持间距
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity) // 让整个内容填满窗口
        .padding()
        .onAppear {
            socketCommunicator.connect() // 界面加载时自动连接到服务器
        }
    }
    // 验证路径的方法
    func validatePath() {
        Task {
            isProcessing = true
            defer { isProcessing = false }
            do {
                try await validatePathAsync()
                isValidPath = true // 路径验证成功
            } catch {
                pathAttempts += 1 // 增加尝试次数
                isValidPath = false // 路径无效
            }
        }
    }
    // 异步验证路径
    func validatePathAsync() async throws {
        // 验证逻辑：路径必须是整数且只能是 1 或 2
        guard let intPath = Int(path), intPath == 1 || intPath == 2 else {
            throw PathError.invalidPath
        }
    }
    enum PathError: Error {
        case invalidPath
    }
}


/* ----------------------------- APP 组件库 ------------------------------------ */
// 抽象日志显示组件
struct LogView: View {
    var title: String // 日志标题
    var logs: [String] // 日志内容
    var fontColor: Color // 日志字体颜色

    @State private var scrollProxy: ScrollViewProxy? = nil

    var body: some View {
        VStack(alignment: .leading) {
            Text(title)
                .font(.headline)
                .padding(.bottom, 5)

            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 5) {
                        ForEach(logs, id: \.self) { log in
                            Text(log)
                                .font(.body)
                                .foregroundColor(fontColor)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding()
                }
                .background(Color.gray.opacity(0.45))
                .cornerRadius(8)
                .onAppear {
                    scrollProxy = proxy
                }
                .onChange(of: logs) { oldValue, newValue in
                   if let lastLog = newValue.last {
                       proxy.scrollTo(lastLog, anchor: .bottom)
                   }
               }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity) // 自适应大小
        .padding()
    }
}

// 按钮样式
struct PushDownButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .bold()
            .foregroundStyle(.white)
            .padding(.vertical, 12)
            .padding(.horizontal, 32)
            .background(.tint, in: Capsule())
            .opacity(configuration.isPressed ? 0.75 : 1)
            .conditionalEffect(
                .pushDown,
                condition: configuration.isPressed
            )
    }
}


// 小车动画组件
struct CarAnimationView: View {
    @Binding var isRunning: Bool // 小车运行状态

    @State private var carPosition: CGFloat = -100 // 小车初始位置
    @State private var animationDuration: Double = 4.0 // 动画持续时间

    var body: some View {
        GeometryReader { geometry in // 获取视图宽度
            ZStack {
                // 轨道
                Rectangle()
                    .fill(Color.gray.opacity(0.3))
                    .frame(height: 4)
                    .offset(y: 50)

                // 小车
                Image(systemName: "car") // 侧面小车图标
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 50, height: 30)
                    .foregroundColor(.blue)
                    .offset(x: carPosition, y: 20)
                    .onChange(of: isRunning) { newValue in
                        if newValue {
                            startCarAnimation(viewWidth: geometry.size.width)
                        } else {
                            stopCarAnimation()
                        }
                    }
            }
        }
        .frame(height: 100) // 限制动画视图高度
    }

    // 小车开始动画
    func startCarAnimation(viewWidth: CGFloat) {
        withAnimation(.linear(duration: animationDuration).repeatForever(autoreverses: false)) {
            carPosition = viewWidth - 85 // 让小车移动到视图右侧
        }
    }

    // 小车停止动画
    func stopCarAnimation() {
        withAnimation(.easeOut(duration: 0.5)) {
            carPosition = -100 // 重置到初始位置
        }
    }
}


/* ------------------------------ TODO list ------------------------------------ */

//
//struct ContentView_Previews: PreviewProvider {
//    static var previews: some View {
//        ContentView() // 指定需要预览的视图
//    }
//}









