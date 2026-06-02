import AppKit
import TextPilotCore

struct CapturedSelection {
    let text: String
    let sourceApplication: NSRunningApplication?
}

@MainActor
final class SelectionCaptureService {
    func captureSelection() async throws -> CapturedSelection {
        let sourceApplication = NSWorkspace.shared.frontmostApplication
        let pasteboard = NSPasteboard.general
        let previousContents = pasteboard.string(forType: .string)

        sendCommand(key: 0x08)
        try await Task.sleep(nanoseconds: 800_000_000)

        let copiedText = pasteboard.string(forType: .string) ?? ""
        restoreClipboard(previousContents)
        return CapturedSelection(
            text: try SelectedTextValidator.validated(copiedText),
            sourceApplication: sourceApplication
        )
    }

    func captureSelectedText() async throws -> String {
        try await captureSelection().text
    }

    func replaceSelection(with text: String, in sourceApplication: NSRunningApplication?) async {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)

        NSApp.hide(nil)
        sourceApplication?.activate(options: [.activateAllWindows])
        try? await Task.sleep(nanoseconds: 800_000_000)
        sendCommand(key: 0x09)
    }

    private func sendCommand(key: CGKeyCode) {
        let source = CGEventSource(stateID: .hidSystemState)
        let keyDown = CGEvent(keyboardEventSource: source, virtualKey: key, keyDown: true)
        let keyUp = CGEvent(keyboardEventSource: source, virtualKey: key, keyDown: false)

        keyDown?.flags = .maskCommand
        keyUp?.flags = .maskCommand
        keyDown?.post(tap: .cghidEventTap)
        keyUp?.post(tap: .cghidEventTap)
    }

    private func restoreClipboard(_ previousContents: String?) {
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        if let previousContents {
            pasteboard.setString(previousContents, forType: .string)
        }
    }
}
