import SwiftUI
import TextPilotCore

struct RewritePanelView: View {
    @ObservedObject var viewModel: RewriteViewModel
    @State private var showingDebugLogs = false

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("TextPilot")
                    .font(.title2.weight(.semibold))
                Spacer()
                Picker("Action", selection: $viewModel.selectedMode) {
                    ForEach(RewriteMode.allCases) { mode in
                        Text(mode.displayName).tag(mode)
                    }
                }
                .frame(width: 190)

                Button("Run") {
                    Task { await viewModel.rewrite() }
                }
                .keyboardShortcut("r")
                .disabled(viewModel.isLoading || viewModel.originalText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Selected Text")
                    .font(.headline)
                TextEditor(text: $viewModel.originalText)
                    .font(.body)
                    .frame(minHeight: 120)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            }

            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text("Alternative")
                        .font(.headline)
                    Spacer()
                    if viewModel.isLoading {
                        ProgressView()
                            .controlSize(.small)
                    }
                }

                TextEditor(text: $viewModel.outputText)
                    .font(.body)
                    .frame(minHeight: 180)
                    .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .foregroundStyle(.red)
                    .font(.callout)
            }

            VStack(alignment: .leading, spacing: 8) {
                Toggle("Debug Logs", isOn: $showingDebugLogs)
                    .toggleStyle(.checkbox)

                if showingDebugLogs {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Request Body")
                            .font(.subheadline.weight(.semibold))
                        TextEditor(text: .constant(viewModel.debugRequestBody))
                            .font(.system(.caption, design: .monospaced))
                            .frame(minHeight: 90)
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))

                        Text(viewModel.debugStatus.isEmpty ? "Response" : "Response - \(viewModel.debugStatus)")
                            .font(.subheadline.weight(.semibold))
                        TextEditor(text: .constant(viewModel.debugResponseBody))
                            .font(.system(.caption, design: .monospaced))
                            .frame(minHeight: 90)
                            .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
                    }
                }
            }

            HStack {
                Button("Retry") {
                    Task { await viewModel.rewrite() }
                }
                .disabled(viewModel.isLoading)

                Spacer()

                Button("Copy") {
                    viewModel.copyOutput()
                }
                .keyboardShortcut(.defaultAction)
                .disabled(viewModel.outputText.isEmpty)
            }
        }
        .padding(20)
        .frame(minWidth: 620, minHeight: 500)
    }
}
