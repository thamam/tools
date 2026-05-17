import AppKit
import TextPilotCore

@MainActor
final class SelectionCaptureService {
    func captureSelectedText() async throws -> String {
        let pasteboard = NSPasteboard.general
        let previousContents = pasteboard.string(forType: .string)

        sendCopyCommand()
        try await Task.sleep(nanoseconds: 180_000_000)

        let copiedText = pasteboard.string(forType: .string) ?? ""
        restoreClipboard(previousContents)
        return try SelectedTextValidator.validated(copiedText)
    }

    private func sendCopyCommand() {
        let source = CGEventSource(stateID: .hidSystemState)
        let keyDown = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: true)
        let keyUp = CGEvent(keyboardEventSource: source, virtualKey: 0x08, keyDown: false)

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
