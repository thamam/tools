import AppKit
import SwiftUI

@MainActor
final class RewritePanelController {
    private let settingsStore: SettingsStore
    private var panel: NSPanel?

    init(settingsStore: SettingsStore) {
        self.settingsStore = settingsStore
    }

    func show(selectedText: String, initialError: String?) {
        let viewModel = RewriteViewModel(
            originalText: selectedText,
            initialError: initialError,
            settingsStore: settingsStore
        )
        let view = RewritePanelView(viewModel: viewModel)
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 680, height: 560),
            styleMask: [.titled, .closable, .resizable, .fullSizeContentView],
            backing: .buffered,
            defer: false
        )
        panel.title = "TextPilot"
        panel.isFloatingPanel = true
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.contentView = NSHostingView(rootView: view)
        panel.center()
        panel.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        self.panel = panel
    }
}
