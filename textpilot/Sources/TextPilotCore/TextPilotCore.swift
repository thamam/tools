import Foundation

public enum TextPilotVersion {
    public static let current = "0.2.3"
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


public struct TextReplacementRange: Equatable, Sendable {
    public let location: Int
    public let length: Int

    public init(location: Int, length: Int) {
        self.location = location
        self.length = length
    }
}

public enum TextSelectionReplacer {
    public static func replacingSelection(in value: String, range: TextReplacementRange, with replacement: String) -> String? {
        guard range.location >= 0, range.length >= 0 else { return nil }
        let nsRange = NSRange(location: range.location, length: range.length)
        guard let swiftRange = Range(nsRange, in: value) else { return nil }

        var updated = value
        updated.replaceSubrange(swiftRange, with: replacement)
        return updated
    }

    public static func selectedText(in value: String, range: TextReplacementRange) -> String? {
        guard range.location >= 0, range.length >= 0 else { return nil }
        let nsRange = NSRange(location: range.location, length: range.length)
        guard let swiftRange = Range(nsRange, in: value) else { return nil }
        return String(value[swiftRange])
    }
}

public enum RewriteMode: String, CaseIterable, Codable, Identifiable, Sendable {
    case fixGrammar
    case rewriteClearly
    case shorten
    case professional
    case casual
    case deAI

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
        case .deAI:
            "deAI"
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
        case .deAI:
            """
            Strip the signature of machine-written prose from the text below. Rewrite it so it reads as if a careful human wrote it in one sitting.

            Work sentence by sentence. For each sentence, decide what it actually tells the reader. If the answer is nothing, delete the sentence. If the answer is something, rebuild the sentence from that content in plain words, as short as it can be said. Do not edit around the original wording; write the sentence again.

            Rules:
            Keep every fact, claim, number, name, and quotation, and keep the order of the argument. Add nothing.
            Write in the language of the original. The English phrases below are examples of categories, not a word list. In any other language, find the phrases that play the same role and cut those: the stock opener about the fast-paced modern world, the "it is worth noting" hedge, the closer that summarizes what was just said, the run of three adjectives of praise, the offer of further help. In Hebrew these sound like "בעולם המהיר של ימינו", "ראוי לציין", "חשוב מאין כמותו", "לסיכום", "פתרון חזק, גמיש ומקיף", "אני מקווה שזה עוזר".
            Cut throat-clearing and filler openers: "it's worth noting", "importantly", "in today's fast-paced world", "let's dive in", "I wanted to reach out", "I'm writing to", "more important than ever".
            Cut any run of three whose third item is there for rhythm, including adjective strings like "strengths, weaknesses, and trade-offs" and "flexible, scalable, and reliable". Keep only the items that carry information.
            Cut vague praise and filler verbs: "robust", "seamless", "powerful", "comprehensive", "cutting-edge", "vibrant", "delve", "leverage", "navigate", "landscape", "tapestry", "testament to", "has emerged as". Say the concrete thing instead, or say nothing.
            Cut promotional closers and generic sign-offs: "will serve you well for years to come", "is a solid choice", "the possibilities are endless", calls to action, and offers of further help.
            Cut "not X, but Y" constructions and em-dashes used for drama.
            Cut bold phrases used as inline pseudo-headers inside a paragraph. Keep the headers, lists, code blocks, and line breaks that are part of the document's own structure.
            Cut the padding, keep the content. Models pad; humans writing in one sitting do not:
            Delete preamble that restates the question or announces the answer before giving it.
            Delete a sentence that says again, in different words, what the sentence before it said.
            Delete background and definitions the reader of this text plainly already has.
            Delete caveats and qualifications nobody asked for that change no decision.
            Collapse softening clauses: "it may be worth considering that X" becomes "X".
            Use a plain sentence instead of a bulleted list when the items are not discrete things.
            Never delete a fact, number, claim, or recommendation to make the text shorter. Compress the prose, not the content. If the text is already tight, it stays the same length.
            Do not hoist the conclusion to the top, and do not add a summary line at either end. Cutting padding is not reordering: the argument stays in the order the author put it, and a point made once is not made again.

            Vary sentence length. Some sentences should be under eight words.
            Keep the author's voice, contractions, register, markdown, and punctuation characters. Do not introduce curly quotes or em-dashes.
            If a passage already reads as human, return it unchanged, word for word.

            Before you answer, read your rewrite once and delete anything in it that still matches a rule above.

            Return the rewritten text only, with no commentary.
            """
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
    private enum CodingKeys: String, CodingKey {
        case id, timestamp, operationName, profileName, originalText, outputText, usedFallbackReplacement
    }

    public let id: String
    public let timestamp: Date
    public let operationName: String
    public let profileName: String
    public let originalText: String
    public let outputText: String
    public var usedFallbackReplacement: Bool

    public init(id: String = UUID().uuidString, timestamp: Date = Date(), operationName: String, profileName: String, originalText: String, outputText: String, usedFallbackReplacement: Bool = false) {
        self.id = id
        self.timestamp = timestamp
        self.operationName = operationName
        self.profileName = profileName
        self.originalText = originalText
        self.outputText = outputText
        self.usedFallbackReplacement = usedFallbackReplacement
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        timestamp = try container.decode(Date.self, forKey: .timestamp)
        operationName = try container.decode(String.self, forKey: .operationName)
        profileName = try container.decode(String.self, forKey: .profileName)
        originalText = try container.decode(String.self, forKey: .originalText)
        outputText = try container.decode(String.self, forKey: .outputText)
        // Absent in history persisted before this field existed.
        usedFallbackReplacement = try container.decodeIfPresent(Bool.self, forKey: .usedFallbackReplacement) ?? false
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
