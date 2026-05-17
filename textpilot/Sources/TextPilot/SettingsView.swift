import SwiftUI
import TextPilotCore

struct SettingsView: View {
    @ObservedObject var settingsStore: SettingsStore
    @State private var profileNameDraft = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("TextPilot Settings")
                .font(.title2.weight(.semibold))

            VStack(alignment: .leading, spacing: 8) {
                Text("OpenAI API Key")
                    .font(.headline)
                SecureField("sk-...", text: $settingsStore.apiKey)
                    .textFieldStyle(.roundedBorder)
            }

            VStack(alignment: .leading, spacing: 8) {
                Text("Model")
                    .font(.headline)
                TextField("gpt-5.4-mini", text: $settingsStore.model)
                    .textFieldStyle(.roundedBorder)
            }

            Divider()

            profileEditor

            Text("Shortcut: Control + Option + R")
                .foregroundStyle(.secondary)

            Spacer(minLength: 0)
        }
        .padding(24)
        .frame(width: 620, height: 680)
        .onAppear {
            profileNameDraft = settingsStore.selectedPromptProfile.name
        }
        .onChange(of: settingsStore.selectedPromptProfileID) { _, _ in
            profileNameDraft = settingsStore.selectedPromptProfile.name
        }
    }

    private var profileEditor: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Prompt Profile")
                    .font(.headline)

                Spacer()

                Picker("Profile", selection: $settingsStore.selectedPromptProfileID) {
                    ForEach(settingsStore.promptProfiles) { profile in
                        Text(profile.name).tag(profile.id)
                    }
                }
                .frame(width: 220)
            }

            HStack(spacing: 8) {
                TextField("Profile name", text: $profileNameDraft)
                    .textFieldStyle(.roundedBorder)
                    .disabled(settingsStore.selectedPromptProfile.isReadOnly)
                    .onSubmit {
                        settingsStore.renameSelectedProfile(profileNameDraft)
                    }

                Button("Rename") {
                    settingsStore.renameSelectedProfile(profileNameDraft)
                }
                .disabled(settingsStore.selectedPromptProfile.isReadOnly)

                Button("New Profile") {
                    settingsStore.createProfile()
                    profileNameDraft = settingsStore.selectedPromptProfile.name
                }

                Button("Delete") {
                    settingsStore.deleteSelectedProfile()
                    profileNameDraft = settingsStore.selectedPromptProfile.name
                }
                .disabled(settingsStore.selectedPromptProfile.isReadOnly)
            }

            if settingsStore.selectedPromptProfile.isReadOnly {
                Text("Default is read-only. Create a custom profile to edit prompts.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }

            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    ForEach(RewriteMode.allCases) { mode in
                        VStack(alignment: .leading, spacing: 6) {
                            Text(mode.displayName)
                                .font(.subheadline.weight(.semibold))
                            TextEditor(text: promptBinding(for: mode))
                                .font(.system(.body, design: .default))
                                .frame(minHeight: 74)
                                .disabled(settingsStore.selectedPromptProfile.isReadOnly)
                                .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
                        }
                    }
                }
                .padding(.vertical, 4)
            }
            .frame(minHeight: 330)
        }
    }

    private func promptBinding(for mode: RewriteMode) -> Binding<String> {
        Binding(
            get: { settingsStore.selectedPromptProfile.prompt(for: mode) },
            set: { settingsStore.updatePrompt($0, for: mode) }
        )
    }
}
