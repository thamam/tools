import AppKit
import SwiftUI

@MainActor
final class RewritePanelController {
    private let settingsStore: SettingsStore
    private let historyStore: HistoryStore
    private let selectionCaptureService: SelectionCaptureService
    private var panel: NSPanel?

    init(settingsStore: SettingsStore, historyStore: HistoryStore, selectionCaptureService: SelectionCaptureService) {
        self.settingsStore = settingsStore
        self.historyStore = historyStore
        self.selectionCaptureService = selectionCaptureService
    }

    func show(selection: CapturedSelection, initialError: String?, selectedAction: RewriteActionSelection, autoRun: Bool) {
        let viewModel = RewriteViewModel(
            originalText: selection.text,
            initialError: initialError,
            selectedAction: selectedAction,
            sourceApplication: selection.sourceApplication,
            closePanel: { [weak self] in self?.closePanel() },
            settingsStore: settingsStore,
            historyStore: historyStore,
            selectionCaptureService: selectionCaptureService
        )
        let view = RewritePanelView(viewModel: viewModel)
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 760, height: 760),
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

        if autoRun && initialError == nil {
            Task { await viewModel.rewrite() }
        }
    }

    private func closePanel() {
        panel?.close()
        panel = nil
    }
}
