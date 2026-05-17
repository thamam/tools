import Foundation

public enum RewriteMode: String, CaseIterable, Codable, Identifiable, Sendable {
    case fixGrammar
    case rewriteClearly
    case shorten
    case professional
    case casual

    public var id: String { rawValue }

    public var displayName: String {
        switch self {
        case .fixGrammar:
            "Fix Grammar"
        case .rewriteClearly:
            "Rewrite Clearly"
        case .shorten:
            "Shorten"
        case .professional:
            "Professional"
        case .casual:
            "Casual"
        }
    }

    public var instruction: String {
        switch self {
        case .fixGrammar:
            "Fix grammar and spelling while preserving the original meaning."
        case .rewriteClearly:
            "Rewrite this to be clearer while preserving the original meaning."
        case .shorten:
            "Shorten this while preserving the important details."
        case .professional:
            "Rewrite this in a professional tone while preserving the original meaning."
        case .casual:
            "Rewrite this in a casual, natural tone while preserving the original meaning."
        }
    }
}

public struct PromptProfile: Codable, Equatable, Identifiable, Sendable {
    public static let defaultID = "default"

    public let id: String
    public var name: String
    public var prompts: [RewriteMode: String]
    public let isReadOnly: Bool

    public static var `default`: PromptProfile {
        PromptProfile(
            id: defaultID,
            name: "Default",
            prompts: Dictionary(uniqueKeysWithValues: RewriteMode.allCases.map { ($0, $0.instruction) }),
            isReadOnly: true
        )
    }

    public static func custom(id: String = UUID().uuidString, name: String, prompts: [RewriteMode: String] = [:]) -> PromptProfile {
        var mergedPrompts = PromptProfile.default.prompts
        for (mode, prompt) in prompts {
            mergedPrompts[mode] = prompt
        }
        return PromptProfile(id: id, name: name, prompts: mergedPrompts, isReadOnly: false)
    }

    public init(id: String, name: String, prompts: [RewriteMode: String], isReadOnly: Bool) {
        self.id = id
        self.name = name
        self.prompts = prompts
        self.isReadOnly = isReadOnly
    }

    public func prompt(for mode: RewriteMode) -> String {
        prompts[mode] ?? mode.instruction
    }
}

public struct RewritePrompt: Equatable, Sendable {
    public let system: String
    public let user: String
}

public enum RewritePromptFactory {
    public static func prompt(for mode: RewriteMode, text: String, profile: PromptProfile = .default) -> RewritePrompt {
        return RewritePrompt(
            system: "You rewrite selected user text. Return only the rewritten text, with no commentary.",
            user: """
            \(profile.prompt(for: mode))

            Selected text:
            \(text)
            """
        )
    }
}

public enum SelectedTextValidationError: Error, Equatable {
    case emptySelection
}

public enum SelectedTextValidator {
    public static func validated(_ text: String) throws -> String {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            throw SelectedTextValidationError.emptySelection
        }
        return trimmed
    }
}
