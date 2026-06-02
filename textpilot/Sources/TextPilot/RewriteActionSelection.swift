import Foundation
import TextPilotCore

enum RewriteActionSelection: String, CaseIterable, Identifiable {
    case fixGrammar
    case rewriteClearly
    case shorten
    case professional
    case casual
    case custom

    var id: String { rawValue }

    var displayName: String {
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
        case .custom:
            "Custom"
        }
    }

    var mode: RewriteMode? {
        switch self {
        case .fixGrammar:
            .fixGrammar
        case .rewriteClearly:
            .rewriteClearly
        case .shorten:
            .shorten
        case .professional:
            .professional
        case .casual:
            .casual
        case .custom:
            nil
        }
    }

    func operation(customInstruction: String) throws -> RewriteOperation {
        if let mode {
            return .mode(mode)
        }

        let trimmed = customInstruction.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            throw CustomActionError.emptyInstruction
        }
        return .custom(trimmed)
    }
}

enum CustomActionError: LocalizedError {
    case emptyInstruction

    var errorDescription: String? {
        "Add a custom instruction before running."
    }
}
