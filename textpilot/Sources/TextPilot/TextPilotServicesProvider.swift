import AppKit
import Foundation
import TextPilotCore

/// Backs the macOS Services menu entries declared in Info.plist's
/// `NSServices` array (right-click selected text -> Services -> TextPilot ->
/// <mode>). Unlike the hotkey flow, Services capture and replace the
/// selection natively via the pasteboard/responder chain, so this bypasses
/// SelectionCaptureService's Accessibility-based capture/replace entirely.
@objc final class TextPilotServicesProvider: NSObject {
    private let settingsStore: SettingsStore
    private let timeout: TimeInterval

    init(settingsStore: SettingsStore, timeout: TimeInterval = 20) {
        self.settingsStore = settingsStore
        self.timeout = timeout
    }

    @objc(fixGrammarService:userData:error:)
    func fixGrammarService(_ pasteboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        perform(mode: .fixGrammar, pasteboard: pasteboard, error: error)
    }

    @objc(rewriteClearlyService:userData:error:)
    func rewriteClearlyService(_ pasteboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        perform(mode: .rewriteClearly, pasteboard: pasteboard, error: error)
    }

    @objc(shortenService:userData:error:)
    func shortenService(_ pasteboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        perform(mode: .shorten, pasteboard: pasteboard, error: error)
    }

    @objc(professionalService:userData:error:)
    func professionalService(_ pasteboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        perform(mode: .professional, pasteboard: pasteboard, error: error)
    }

    @objc(casualService:userData:error:)
    func casualService(_ pasteboard: NSPasteboard, userData: String, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        perform(mode: .casual, pasteboard: pasteboard, error: error)
    }

    /// Reference type so the write from the detached Task is visible to the
    /// caller after `semaphore.wait()` returns; the semaphore is the
    /// happens-before edge, `@unchecked Sendable` documents that trade-off.
    private final class ResultBox: @unchecked Sendable {
        var result: Result<String, Error>?
    }

    private func perform(mode: RewriteMode, pasteboard: NSPasteboard, error: AutoreleasingUnsafeMutablePointer<NSString>) {
        guard let text = pasteboard.string(forType: .string),
              let validated = try? SelectedTextValidator.validated(text) else {
            error.pointee = "TextPilot: no text selected." as NSString
            return
        }

        // AppKit dispatches Services calls on the main thread. `assumeIsolated`
        // reads the @MainActor SettingsStore synchronously; an `await
        // MainActor.run` here would deadlock, since the main thread's run loop
        // won't be pumped once semaphore.wait() blocks it below. Bind the store
        // to a local first so the closure doesn't need to capture `self`.
        let store = settingsStore
        let snapshot = MainActor.assumeIsolated {
            (apiKey: store.apiKey, model: store.model, profile: store.selectedPromptProfile)
        }

        guard !snapshot.apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
            error.pointee = "TextPilot: add an OpenAI API key in Settings." as NSString
            return
        }

        let box = ResultBox()
        let semaphore = DispatchSemaphore(value: 0)

        Task.detached(priority: .userInitiated) {
            do {
                let client = OpenAIRewriteClient(apiKey: snapshot.apiKey, model: snapshot.model, transport: URLSessionHTTPTransport())
                let response = try await client.rewriteWithTrace(validated, mode: mode, profile: snapshot.profile)
                box.result = .success(response.text)
            } catch {
                box.result = .failure(error)
            }
            semaphore.signal()
        }

        guard semaphore.wait(timeout: .now() + timeout) == .success else {
            error.pointee = "TextPilot: request timed out after \(Int(timeout))s." as NSString
            return
        }

        switch box.result {
        case .success(let rewritten):
            pasteboard.clearContents()
            pasteboard.declareTypes([.string], owner: nil)
            pasteboard.setString(rewritten, forType: .string)
        case .failure(let underlying):
            error.pointee = "TextPilot: \(underlying.localizedDescription)" as NSString
        case .none:
            error.pointee = "TextPilot: unknown error." as NSString
        }
    }
}
