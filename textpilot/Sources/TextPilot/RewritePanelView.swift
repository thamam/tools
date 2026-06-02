import SwiftUI
import TextPilotCore

struct RewritePanelView: View {
    @ObservedObject var viewModel: RewriteViewModel
    @State private var showingDebugLogs = false
    @State private var showingHistory = true

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("TextPilot")
                    .font(.title2.weight(.semibold))
                Spacer()
                Picker("Action", selection: $viewModel.selectedAction) {
                    ForEach(RewriteActionSelection.allCases) { action in
                        Text(action.displayName).tag(action)
                    }
                }
                .frame(width: 210)

                Button("Run") {
                    runRewrite()
                }
                .keyboardShortcut(.return, modifiers: [])
                .disabled(viewModel.isLoading || viewModel.originalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }

            if viewModel.selectedAction == .custom {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Custom Instruction")
                        .font(.headline)
                    KeyboardSubmittingTextEditor(text: $viewModel.customInstruction, onReturnAction: handleReturnAction)
                        .font(.body)
                        .frame(minHeight: 70)
                        .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Selected Text")
                    .font(.headline)
                KeyboardSubmittingTextEditor(text: $viewModel.originalText, onReturnAction: handleReturnAction)
                    .font(.body)
                    .frame(minHeight: 105)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Alternative")
                        .font(.headline)
                    if !viewModel.outputText.isEmpty {
                        Text("Copied automatically")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if viewModel.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    }
                }

                KeyboardSubmittingTextEditor(text: $viewModel.outputText, onReturnAction: handleReturnAction)
                    .font(.body)
                    .frame(minHeight: 155)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundStyle(.red)
                    .font(.callout)
            }

            HStack {
                Button("Retry") {
                    runRewrite()
                }
                .disabled(viewModel.isLoading)

                Button("Replace") {
                    Task { await viewModel.replaceSelection() }
                }
                .disabled(viewModel.outputText.isEmpty)

                Button("Replace & Close") {
                    Task { await viewModel.replaceAndClose() }
                }
                .keyboardShortcut(.return, modifiers: .option)
                .disabled(viewModel.outputText.isEmpty)

                Spacer()

                Button("Copy") {
                    viewModel.copyOutput()
                }
                .disabled(viewModel.outputText.isEmpty)

                Button("Copy & Close") {
                    viewModel.copyAndClose()
                }
                .keyboardShortcut(.return, modifiers: .command)
                .disabled(viewModel.outputText.isEmpty)
            }

            VStack(alignment: .leading, spacing: 8) {
                Toggle("History", isOn: $showingHistory)
                    .toggleStyle(.checkbox)

                if showingHistory {
                    if viewModel.historyEntries.isEmpty {
                        Text("No generated responses yet.")
                            .font(.callout)
                            .foregroundStyle(.secondary)
                    } else {
                        ScrollView {
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(viewModel.historyEntries) { entry in
                                    VStack(alignment: .leading, spacing: 6) {
                                        HStack {
                                            Text(entry.operationName)
                                                .font(.subheadline.weight(.semibold))
                                            Text(entry.profileName)
                                                .font(.caption)
                                                .foregroundStyle(.secondary)
                                            Spacer()
                                            Button("Copy") {
                                                viewModel.copyHistoryEntry(entry)
                                            }
                                        }
                                        Text(entry.outputText)
                                            .font(.callout)
                                            .lineLimit(3)
                                            .textSelection(.enabled)
                                    }
                                    .padding(8)
                                    .background(Color.secondary.opacity(0.08))
                                    .clipShape(RoundedRectangle(cornerRadius: 6))
                                }
                            }
                        }
                        .frame(maxHeight: 150)
                    }
                }
            }

            VStack(alignment: .leading, spacing: 8) {
                Toggle("Debug Logs", isOn: $showingDebugLogs)
                    .toggleStyle(.checkbox)

                if showingDebugLogs {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Request Body")
                            .font(.subheadline.weight(.semibold))
                        KeyboardSubmittingTextEditor(text: .constant(viewModel.debugRequestBody), onReturnAction: handleReturnAction)
                            .font(.system(.caption, design: .monospaced))
                            .frame(minHeight: 80)
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))

                        Text(viewModel.debugStatus.isEmpty ? "Response" : "Response - \(viewModel.debugStatus)")
                            .font(.subheadline.weight(.semibold))
                        KeyboardSubmittingTextEditor(text: .constant(viewModel.debugResponseBody), onReturnAction: handleReturnAction)
                            .font(.system(.caption, design: .monospaced))
                            .frame(minHeight: 80)
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
                    }
                }
            }
        }
        .padding(20)
        .frame(minWidth: 700, minHeight: 680)
    }

    private func handleReturnAction(_ action: EditorReturnKeyAction) {
        switch action {
        case .run:
            runRewrite()
        case .insertNewline:
            break
        case .copyAndClose:
            viewModel.copyAndClose()
        case .replaceAndClose:
            Task { await viewModel.replaceAndClose() }
        }
    }

    private func runRewrite() {
        Task { await viewModel.rewrite() }
    }
}
