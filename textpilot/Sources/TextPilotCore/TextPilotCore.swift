import Foundation

public enum TextPilotVersion {
    public static let current = "0.2.1"
}

public struct EditorKeyModifiers: OptionSet, Equatable, Sendable {
    public let rawValue: Int

    public init(rawValue: Int) {
        self.rawValue = rawValue
    }

    public static let shift = EditorKeyModifiers(rawValue: 1 << 0)
    public static let command = EditorKeyModifiers(rawValue: 1 << 1)
    public static let option = EditorKeyModifiers(rawValue: 1 << 2)
}

public enum EditorReturnKeyAction: Equatable, Sendable {
    case run
    case insertNewline
    case copyAndClose
    case replaceAndClose
}

public enum EditorReturnKeyPolicy {
    public static func action(for modifiers: EditorKeyModifiers) -> EditorReturnKeyAction {
        if modifiers.contains(.shift) {
            return .insertNewline
        }
        if modifiers.contains(.command) {
            return .copyAndClose
        }
        if modifiers.contains(.option) {
            return .replaceAndClose
        }
        return .run
    }
}

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

public enum RewriteOperation: Equatable, Sendable {
    case mode(RewriteMode)
    case custom(String)

    public var displayName: String {
        switch self {
        case .mode(let mode):
            mode.displayName
        case .custom:
            "Custom"
        }
    }

    public var instruction: String {
        switch self {
        case .mode(let mode):
            mode.instruction
        case .custom(let instruction):
            instruction
        }
    }
}

public struct RewriteHistoryEntry: Codable, Equatable, Identifiable, Sendable {
    public let id: String
    public let timestamp: Date
    public let operationName: String
    public let profileName: String
    public let originalText: String
    public let outputText: String

    public init(id: String = UUID().uuidString, timestamp: Date = Date(), operationName: String, profileName: String, originalText: String, outputText: String) {
        self.id = id
        self.timestamp = timestamp
        self.operationName = operationName
        self.profileName = profileName
        self.originalText = originalText
        self.outputText = outputText
    }
}

public enum RewriteHistoryBuffer {
    public static func adding(_ entry: RewriteHistoryEntry, to entries: [RewriteHistoryEntry], limit: Int = 20) -> [RewriteHistoryEntry] {
        guard limit > 0 else { return [] }
        return Array(([entry] + entries).prefix(limit))
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
        prompt(for: .mode(mode), text: text, profile: profile)
    }

    public static func prompt(for operation: RewriteOperation, text: String, profile: PromptProfile = .default) -> RewritePrompt {
        let instruction: String
        switch operation {
        case .mode(let mode):
            instruction = profile.prompt(for: mode)
        case .custom(let customInstruction):
            instruction = customInstruction
        }

        return RewritePrompt(
            system: "You rewrite selected user text. Return only the rewritten text, with no commentary.",
            user: """
            \(instruction)

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
