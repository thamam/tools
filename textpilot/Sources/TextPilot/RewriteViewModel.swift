import AppKit
import Foundation
import TextPilotCore

@MainActor
final class RewriteViewModel: ObservableObject {
    @Published var originalText: String
    @Published var outputText = ""
    @Published var selectedAction: RewriteActionSelection
    @Published var customInstruction = ""
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var debugRequestBody = ""
    @Published var debugStatus = ""
    @Published var debugResponseBody = ""

    private let capturedSelectedText: String
    private let settingsStore: SettingsStore
    private let historyStore: HistoryStore
    private let selectionCaptureService: SelectionCaptureService
    private let sourceApplication: NSRunningApplication?
    private let closePanel: @MainActor () -> Void

    init(
        originalText: String,
        initialError: String?,
        selectedAction: RewriteActionSelection = .fixGrammar,
        customInstruction: String = "",
        sourceApplication: NSRunningApplication?,
        closePanel: @escaping @MainActor () -> Void = {},
        settingsStore: SettingsStore,
        historyStore: HistoryStore,
        selectionCaptureService: SelectionCaptureService
    ) {
        self.originalText = originalText
        self.capturedSelectedText = originalText
        self.errorMessage = initialError
        self.selectedAction = selectedAction
        self.customInstruction = customInstruction
        self.sourceApplication = sourceApplication
        self.closePanel = closePanel
        self.settingsStore = settingsStore
        self.historyStore = historyStore
        self.selectionCaptureService = selectionCaptureService
    }

    var historyEntries: [RewriteHistoryEntry] {
        historyStore.entries
    }

    func rewrite() async {
        errorMessage = nil
        outputText = ""
        debugRequestBody = ""
        debugStatus = ""
        debugResponseBody = ""

        do {
            let text = try SelectedTextValidator.validated(originalText)
            let operation = try selectedAction.operation(customInstruction: customInstruction)
            let profile = settingsStore.selectedPromptProfile

            isLoading = true
            defer { isLoading = false }

            let response: RewriteResponse
            if let mockOutput = ProcessInfo.processInfo.environment["TEXTPILOT_MOCK_OUTPUT"] {
                response = mockResponse(output: mockOutput, text: text, operation: operation, profile: profile)
            } else {
                guard !settingsStore.apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else {
                    errorMessage = "Add your OpenAI API key in Settings."
                    return
                }
                let client = OpenAIRewriteClient(
                    apiKey: settingsStore.apiKey,
                    model: settingsStore.model,
                    transport: URLSessionHTTPTransport()
                )
                response = try await client.rewriteWithTrace(text, operation: operation, profile: profile)
            }

            outputText = response.text
            debugRequestBody = response.trace.requestBody
            debugStatus = "HTTP \(response.trace.statusCode)"
            debugResponseBody = response.trace.responseBody
            copyOutput()
            historyStore.add(
                RewriteHistoryEntry(
                    operationName: operation.displayName,
                    profileName: profile.name,
                    originalText: text,
                    outputText: response.text
                )
            )
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

    func copyHistoryEntry(_ entry: RewriteHistoryEntry) {
        historyStore.copy(entry)
    }

    func copyAndClose() {
        guard !outputText.isEmpty else { return }
        copyOutput()
        closePanel()
    }

    @discardableResult
    func replaceSelection() async -> Bool {
        guard !outputText.isEmpty else { return false }
        let report = await selectionCaptureService.replaceSelection(
            with: outputText,
            expectedSelectedText: capturedSelectedText,
            in: sourceApplication
        )
        debugStatus = "Replacement - \(report.method.rawValue)"
        debugResponseBody = [debugResponseBody, report.logLine]
            .filter { !$0.isEmpty }
            .joined(separator: "\n")
        if !report.succeeded {
            errorMessage = report.message
        }
        return report.succeeded
    }

    func replaceAndClose() async {
        guard !outputText.isEmpty else { return }
        if await replaceSelection() {
            closePanel()
        }
    }

    private func mockResponse(output: String, text: String, operation: RewriteOperation, profile: PromptProfile) -> RewriteResponse {
        let prompt = RewritePromptFactory.prompt(for: operation, text: text, profile: profile)
        let escapedSystem = prompt.system.replacingOccurrences(of: "\"", with: "\\\"")
        let escapedUser = prompt.user.replacingOccurrences(of: "\"", with: "\\\"")
        let requestBody = """
        {"mock":true,"operation":"\(operation.displayName)","system":"\(escapedSystem)","user":"\(escapedUser)"}
        """
        let responseBody = """
        {"mock":true,"output":"\(output.replacingOccurrences(of: "\"", with: "\\\""))"}
        """
        return RewriteResponse(
            text: output,
            trace: RewriteDebugTrace(requestBody: requestBody, responseBody: responseBody, statusCode: 200)
        )
    }
}
