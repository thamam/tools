import Foundation
import TextPilotCore

@MainActor
final class SettingsStore: ObservableObject {
    @Published var apiKey: String {
        didSet { defaults.set(apiKey, forKey: Keys.apiKey) }
    }

    @Published var model: String {
        didSet { defaults.set(model, forKey: Keys.model) }
    }

    @Published var promptProfiles: [PromptProfile] {
        didSet { saveProfiles() }
    }

    @Published var selectedPromptProfileID: String {
        didSet { defaults.set(selectedPromptProfileID, forKey: Keys.selectedPromptProfileID) }
    }

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.apiKey = defaults.string(forKey: Keys.apiKey) ?? ""
        self.model = defaults.string(forKey: Keys.model) ?? "gpt-5.4-mini"
        let loadedProfiles = SettingsStore.loadProfiles(from: defaults)
        self.promptProfiles = loadedProfiles

        let savedProfileID = defaults.string(forKey: Keys.selectedPromptProfileID) ?? PromptProfile.defaultID
        if loadedProfiles.contains(where: { profile in profile.id == savedProfileID }) {
            self.selectedPromptProfileID = savedProfileID
        } else {
            self.selectedPromptProfileID = PromptProfile.defaultID
        }
    }

    var selectedPromptProfile: PromptProfile {
        promptProfiles.first(where: { $0.id == selectedPromptProfileID }) ?? .default
    }

    var selectedPromptProfileIndex: Int? {
        promptProfiles.firstIndex(where: { $0.id == selectedPromptProfileID })
    }

    func createProfile() {
        let existingCustomCount = promptProfiles.filter { !$0.isReadOnly }.count
        let profile = PromptProfile.custom(name: "Custom Profile \(existingCustomCount + 1)")
        promptProfiles.append(profile)
        selectedPromptProfileID = profile.id
    }

    func deleteSelectedProfile() {
        guard let index = selectedPromptProfileIndex, !promptProfiles[index].isReadOnly else { return }
        promptProfiles.remove(at: index)
        selectedPromptProfileID = PromptProfile.defaultID
    }

    func renameSelectedProfile(_ name: String) {
        guard let index = selectedPromptProfileIndex, !promptProfiles[index].isReadOnly else { return }
        let trimmed = name.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        promptProfiles[index].name = trimmed
    }

    func updatePrompt(_ prompt: String, for mode: RewriteMode) {
        guard let index = selectedPromptProfileIndex, !promptProfiles[index].isReadOnly else { return }
        promptProfiles[index].prompts[mode] = prompt
    }

    private func saveProfiles() {
        let customProfiles = promptProfiles.filter { !$0.isReadOnly }
        if let data = try? JSONEncoder().encode(customProfiles) {
            defaults.set(data, forKey: Keys.promptProfiles)
        }
    }

    private static func loadProfiles(from defaults: UserDefaults) -> [PromptProfile] {
        guard let data = defaults.data(forKey: Keys.promptProfiles),
              let customProfiles = try? JSONDecoder().decode([PromptProfile].self, from: data) else {
            return [.default]
        }

        return [.default] + customProfiles.filter { !$0.isReadOnly }
    }

    private enum Keys {
        static let apiKey = "openaiApiKey"
        static let model = "openaiModel"
        static let promptProfiles = "promptProfiles"
        static let selectedPromptProfileID = "selectedPromptProfileID"
    }
}
