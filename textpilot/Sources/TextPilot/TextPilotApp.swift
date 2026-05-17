import SwiftUI
import AppKit
import TextPilotCore

@main
struct TextPilotApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        MenuBarExtra("TextPilot", systemImage: "text.bubble") {
            Button("Rewrite Selection") {
                appDelegate.rewriteSelection()
            }
            .keyboardShortcut("r")

            Button("Settings") {
                appDelegate.showSettings()
            }
            .keyboardShortcut(",")

            Divider()

            Button("Quit") {
                NSApp.terminate(nil)
            }
            .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }
}

@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate {
    private let settingsStore = SettingsStore()
    private let selectionCaptureService = SelectionCaptureService()
    private var rewritePanelController: RewritePanelController?
    private var settingsWindowController: NSWindowController?
    private var hotKeyManager: HotKeyManager?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        hotKeyManager = HotKeyManager { [weak self] in
            Task { @MainActor in
                self?.rewriteSelection()
            }
        }
        hotKeyManager?.register()
    }

    func rewriteSelection() {
        Task { @MainActor in
            do {
                let selectedText = try await selectionCaptureService.captureSelectedText()
                showRewritePanel(selectedText: selectedText)
            } catch {
                showRewritePanel(selectedText: "", initialError: error.localizedDescription)
            }
        }
    }

    func showSettings() {
        if let settingsWindowController {
            settingsWindowController.showWindow(nil)
            settingsWindowController.window?.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }

        let view = SettingsView(settingsStore: settingsStore)
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 460, height: 260),
            styleMask: [.titled, .closable, .miniaturizable],
            backing: .buffered,
            defer: false
        )
        window.title = "TextPilot Settings"
        window.center()
        window.contentView = NSHostingView(rootView: view)

        let controller = NSWindowController(window: window)
        settingsWindowController = controller
        controller.showWindow(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func showRewritePanel(selectedText: String, initialError: String? = nil) {
        let panelController = RewritePanelController(settingsStore: settingsStore)
        rewritePanelController = panelController
        panelController.show(selectedText: selectedText, initialError: initialError)
    }
}
