//
//  mac_UIApp.swift
//  mac-UI
//
//  Created by 袁新宇 on 2024/11/26.
//

import SwiftUI
import AppKit

@main
struct mqtt_uiApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
        
    var body: some Scene {
        WindowGroup {
            ContentView()
            .onAppear {
                makeWindowTransparent()
            }
        }
        .windowStyle(HiddenTitleBarWindowStyle()) // 隐藏标题栏
        .defaultSize(width: 1200, height: 800) // 设置默认窗口大小
    }
    
    func makeWindowTransparent() {
        DispatchQueue.main.async {
            if let window = NSApplication.shared.windows.first {
                window.isOpaque = false // 设置窗口支持透明
                window.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.55) // 半透明背景
                window.titlebarAppearsTransparent = true // 让标题栏透明
                window.titleVisibility = .hidden // 隐藏窗口标题
            }
        }
    }
}

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        // 当最后一个窗口关闭时退出程序
        return true
    }
}



