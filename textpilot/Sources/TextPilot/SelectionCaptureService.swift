import AppKit
import TextPilotCore

struct CapturedSelection {
    let text: String
    let sourceApplication: NSRunningApplication?
}

struct SelectionReplacementReport {
    enum Method: String {
        case accessibilityDirect
        case pasteFallback
        case failed
    }

    let method: Method
    let targetApplicationName: String
    let targetProcessIdentifier: pid_t?
    let focusedElementRole: String?
    let message: String

    var succeeded: Bool {
        method != .failed
    }

    var logLine: String {
        [
            "method=\(method.rawValue)",
            "target=\(targetApplicationName)",
            "pid=\(targetProcessIdentifier.map(String.init) ?? "nil")",
            "role=\(focusedElementRole ?? "nil")",
            "message=\(message)"
        ].joined(separator: " ")
    }
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

    func replaceSelection(with text: String, expectedSelectedText: String?, in sourceApplication: NSRunningApplication?) async -> SelectionReplacementReport {
        NSApp.hide(nil)
        sourceApplication?.activate(options: [.activateAllWindows])
        try? await Task.sleep(nanoseconds: 800_000_000)

        let directAttempt = attemptAccessibilityReplacement(
            with: text,
            expectedSelectedText: expectedSelectedText,
            in: sourceApplication
        )
        if directAttempt.method == .accessibilityDirect {
            logReplacement(directAttempt)
            return directAttempt
        }

        if ProcessInfo.processInfo.environment["TEXTPILOT_REQUIRE_DIRECT_REPLACE"] == "1" {
            logReplacement(directAttempt)
            return directAttempt
        }

        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(text, forType: .string)
        sendCommand(key: 0x09)

        let fallback = SelectionReplacementReport(
            method: .pasteFallback,
            targetApplicationName: applicationName(sourceApplication),
            targetProcessIdentifier: sourceApplication?.processIdentifier,
            focusedElementRole: directAttempt.focusedElementRole,
            message: "Accessibility replacement unavailable: \(directAttempt.message). Used Cmd+V fallback."
        )
        logReplacement(fallback)
        return fallback
    }

    func replaceSelection(with text: String, in sourceApplication: NSRunningApplication?) async {
        _ = await replaceSelection(with: text, expectedSelectedText: nil, in: sourceApplication)
    }

    private func attemptAccessibilityReplacement(with text: String, expectedSelectedText: String?, in sourceApplication: NSRunningApplication?) -> SelectionReplacementReport {
        let targetName = applicationName(sourceApplication)
        guard ProcessInfo.processInfo.environment["TEXTPILOT_DISABLE_DIRECT_REPLACE"] != "1" else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: nil, message: "direct replacement disabled")
        }
        guard let sourceApplication else {
            return failedReport(targetName: targetName, sourceApplication: nil, role: nil, message: "missing source application")
        }
        guard AXIsProcessTrusted() else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: nil, message: "Accessibility permission is not trusted")
        }
        let expected = expectedSelectedText?.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let expected, !expected.isEmpty else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: nil, message: "missing expected selected text")
        }

        let applicationElement = AXUIElementCreateApplication(sourceApplication.processIdentifier)
        let focusedResult = copyAttribute(kAXFocusedUIElementAttribute, from: applicationElement)
        guard focusedResult.error == .success, let focusedElement = focusedResult.value as! AXUIElement? else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: nil, message: "focused element unavailable: \(focusedResult.error)")
        }

        let role = copyStringAttribute(kAXRoleAttribute, from: focusedElement)
        let selectedText = copyStringAttribute(kAXSelectedTextAttribute, from: focusedElement)
        let selectedRange = copySelectedRange(from: focusedElement)
        let value = copyStringAttribute(kAXValueAttribute, from: focusedElement)

        if let selectedText, !matchesSelection(selectedText, expected: expected) {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "focused selection does not match captured text")
        }

        if let selectedText, matchesSelection(selectedText, expected: expected) {
            let setSelectedError = AXUIElementSetAttributeValue(focusedElement, kAXSelectedTextAttribute as CFString, text as CFString)
            if setSelectedError == .success {
                return SelectionReplacementReport(
                    method: .accessibilityDirect,
                    targetApplicationName: targetName,
                    targetProcessIdentifier: sourceApplication.processIdentifier,
                    focusedElementRole: role,
                    message: "replaced AXSelectedText"
                )
            }
        }

        guard let selectedRange else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "selected text range unavailable")
        }
        guard selectedRange.length > 0 else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "selected text range is empty")
        }
        guard let value else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "focused value unavailable")
        }
        guard let currentSelectedText = TextSelectionReplacer.selectedText(in: value, range: selectedRange),
              matchesSelection(currentSelectedText, expected: expected) else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "selected range text does not match captured text")
        }
        guard let updatedValue = TextSelectionReplacer.replacingSelection(in: value, range: selectedRange, with: text) else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "selected range cannot be mapped into focused value")
        }

        let setValueError = AXUIElementSetAttributeValue(focusedElement, kAXValueAttribute as CFString, updatedValue as CFString)
        guard setValueError == .success else {
            return failedReport(targetName: targetName, sourceApplication: sourceApplication, role: role, message: "setting focused value failed: \(setValueError)")
        }

        setSelectedRange(TextReplacementRange(location: selectedRange.location + text.utf16.count, length: 0), on: focusedElement)
        return SelectionReplacementReport(
            method: .accessibilityDirect,
            targetApplicationName: targetName,
            targetProcessIdentifier: sourceApplication.processIdentifier,
            focusedElementRole: role,
            message: "replaced AXValue selected range"
        )
    }

    private func failedReport(targetName: String, sourceApplication: NSRunningApplication?, role: String?, message: String) -> SelectionReplacementReport {
        SelectionReplacementReport(
            method: .failed,
            targetApplicationName: targetName,
            targetProcessIdentifier: sourceApplication?.processIdentifier,
            focusedElementRole: role,
            message: message
        )
    }

    private func copyAttribute(_ attribute: String, from element: AXUIElement) -> (error: AXError, value: CFTypeRef?) {
        var value: CFTypeRef?
        let error = AXUIElementCopyAttributeValue(element, attribute as CFString, &value)
        return (error, value)
    }

    private func copyStringAttribute(_ attribute: String, from element: AXUIElement) -> String? {
        let result = copyAttribute(attribute, from: element)
        guard result.error == .success else { return nil }
        return result.value as? String
    }

    private func copySelectedRange(from element: AXUIElement) -> TextReplacementRange? {
        let result = copyAttribute(kAXSelectedTextRangeAttribute, from: element)
        guard result.error == .success, let value = result.value, CFGetTypeID(value) == AXValueGetTypeID() else { return nil }
        let axValue = value as! AXValue
        guard AXValueGetType(axValue) == .cfRange else { return nil }
        var range = CFRange(location: 0, length: 0)
        guard AXValueGetValue(axValue, .cfRange, &range) else { return nil }
        return TextReplacementRange(location: range.location, length: range.length)
    }

    private func setSelectedRange(_ range: TextReplacementRange, on element: AXUIElement) {
        var cfRange = CFRange(location: range.location, length: range.length)
        guard let axValue = AXValueCreate(.cfRange, &cfRange) else { return }
        AXUIElementSetAttributeValue(element, kAXSelectedTextRangeAttribute as CFString, axValue)
    }

    private func matchesSelection(_ selectedText: String, expected: String) -> Bool {
        selectedText == expected || selectedText.trimmingCharacters(in: .whitespacesAndNewlines) == expected
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

    private func applicationName(_ application: NSRunningApplication?) -> String {
        application?.localizedName ?? "unknown"
    }

    private func logReplacement(_ report: SelectionReplacementReport) {
        guard let path = ProcessInfo.processInfo.environment["TEXTPILOT_REPLACEMENT_LOG"], !path.isEmpty else { return }
        let line = report.logLine + "\n"
        guard let data = line.data(using: .utf8) else { return }
        if FileManager.default.fileExists(atPath: path), let handle = try? FileHandle(forWritingTo: URL(fileURLWithPath: path)) {
            defer { try? handle.close() }
            _ = try? handle.seekToEnd()
            try? handle.write(contentsOf: data)
        } else {
            try? data.write(to: URL(fileURLWithPath: path), options: .atomic)
        }
    }
}
