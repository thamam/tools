import AppKit
import Foundation
import TextPilotCore

@MainActor
final class RewriteViewModel: ObservableObject {
    @Published var originalText: String
    @Published var outputText = ""
    @Published var selectedMode: RewriteMode = .fixGrammar
    @Published var isLoading = false
    @Published var errorMessage: String?
     var debugRequestBody = ""
     var debugStatus = ""
     var debugResponseBody = ""

    private let settingsStore: SettingsStore

    init(originalText: String, initialError: String?, settingsStore: SettingsStore) {
        self.originalText = originalText
        self.errorMessage = initialError
        self.settingsStore = settingsStore
    }

    func rewrite() async {
        errorMessage = nil
        outputText = ""
        debugRequestBody = ""
        debugStatus = ""
        debugResponseBody = ""

        do {
            let text = try SelectedTextValidator.validated(originalText)
            guard !settingsStore.apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                errorMessage = "Add your OpenAI API key in Settings."
                return
            }

            isLoading = true
            defer { isLoading = false }

            let client = OpenAIRewriteClient(
                apiKey: settingsStore.apiKey,
                model: settingsStore.model,
                transport: URLSessionHTTPTransport()
            )
            let profile = settingsStore.selectedPromptProfile
            let response = try await client.rewriteWithTrace(text, mode: selectedMode, profile: profile)
            outputText = response.text
            debugRequestBody = response.trace.requestBody
            debugStatus = "HTTP \(response.trace.statusCode)"
            debugResponseBody = response.trace.responseBody
        } catch let rewriteError as RewriteClientError {
            let trace = rewriteError.debugTrace
            debugRequestBody = trace.requestBody
            debugStatus = "HTTP \(trace.statusCode)"
            debugResponseBody = trace.responseBody
            errorMessage = rewriteError.localizedDescription
            isLoading = false
        } catch {
            errorMessage = error.localizedDescription
            isLoading = false
        }
    }

    func copyOutput() {
        guard !outputText.isEmpty else { return }
        let pasteboard = NSPasteboard.general
        pasteboard.clearContents()
        pasteboard.setString(outputText, forType: .string)
    }
}
