import SwiftUI
import AppKit
import TextPilotCore

@main
struct TextPilotApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        MenuBarExtra("TextPilot", systemImage: "text.bubble") {
            Button("Rewrite Selection") {
                appDelegate.rewriteSelection(action: .fixGrammar, autoRun: false)
            }
            .keyboardShortcut("r")

            Button("Shorten Selection") {
                appDelegate.rewriteSelection(action: .shorten, autoRun: true)
            }

            Button("Custom Action") {
                appDelegate.rewriteSelection(action: .custom, autoRun: false)
            }

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
    private let defaults = TextPilotDefaults.make()
    private lazy var settingsStore = SettingsStore(defaults: defaults)
    private lazy var historyStore = HistoryStore(defaults: defaults)
    private let selectionCaptureService = SelectionCaptureService()
    private var rewritePanelController: RewritePanelController?
    private var settingsWindowController: NSWindowController?
    private var hotKeyManager: HotKeyManager?

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.accessory)
        hotKeyManager = HotKeyManager { [weak self] invocation in
            Task { @MainActor in
                self?.rewriteSelection(action: invocation.action, autoRun: invocation.autoRun)
            }
        }
        hotKeyManager?.register()
    }

    func rewriteSelection(action: RewriteActionSelection, autoRun: Bool) {
        Task { @MainActor in
            do {
                let selection = try await selectionCaptureService.captureSelection()
                showRewritePanel(selection: selection, initialError: nil, selectedAction: action, autoRun: autoRun)
            } catch {
                let selection = CapturedSelection(text: "", sourceApplication: NSWorkspace.shared.frontmostApplication)
                showRewritePanel(selection: selection, initialError: error.localizedDescription, selectedAction: action, autoRun: false)
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
            contentRect: NSRect(x: 0, y: 0, width: 620, height: 680),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
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

    private func showRewritePanel(selection: CapturedSelection, initialError: String?, selectedAction: RewriteActionSelection, autoRun: Bool) {
        let panelController = RewritePanelController(
            settingsStore: settingsStore,
            historyStore: historyStore,
            selectionCaptureService: selectionCaptureService
        )
        rewritePanelController = panelController
        panelController.show(selection: selection, initialError: initialError, selectedAction: selectedAction, autoRun: autoRun)
    }
}
